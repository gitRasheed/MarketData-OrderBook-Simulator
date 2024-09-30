import grpc
from concurrent import futures
import time
import json
from .orderbook_service_pb2 import OrderBookUpdate, PriceLevel, OrderResponse, PriceLevelUpdate, Side, Action
from .orderbook_service_pb2_grpc import OrderBookServiceServicer, add_OrderBookServiceServicer_to_server
from .orderbook_manager import OrderBookManager
from .order import Order
from decimal import Decimal

class OrderBookServer(OrderBookServiceServicer):
    def __init__(self):
        self.order_book_manager = OrderBookManager()
        with open('src/config.json') as config_file:
            config = json.load(config_file)
        for symbol, details in config['instruments'].items():
            self.order_book_manager.create_order_book(symbol, Decimal(details['tick_size']))

    def SubscribeOrderBook(self, request_iterator, context):
        subscribed_symbols = set()
        try:
            for request in request_iterator:
                if request.subscribe:
                    subscribed_symbols.add(request.symbol)
                    yield self._create_snapshot(request.symbol)
                else:
                    subscribed_symbols.remove(request.symbol)
                    yield self._create_empty_update(request.symbol)

                while subscribed_symbols:
                    for symbol in subscribed_symbols:
                        update, version = self.order_book_manager.get_order_book_update(symbol)
                        if update:
                            yield self._create_incremental_update(symbol, update, version)
                    time.sleep(0.1)  # Adjust the sleep time as needed
        except grpc.RpcError:
            for symbol in subscribed_symbols:
                self.order_book_manager.unsubscribe(symbol, context.peer())

    def PlaceOrder(self, request, context):
        order = Order(
            request.order_id,
            request.type,
            request.side,
            Decimal(request.price) if request.type == "limit" else None,
            request.quantity,
            request.symbol
        )
        order_id, _, _ = self.order_book_manager.process_order(order)
        return OrderResponse(order_id=str(order_id), status="PLACED")

    def _create_snapshot(self, symbol):
        snapshot, version = self.order_book_manager.get_order_book_snapshot(symbol)
        return OrderBookUpdate(
            symbol=symbol,
            bids=[PriceLevel(price=str(price), quantity=quantity) for price, quantity in snapshot['bids']],
            asks=[PriceLevel(price=str(price), quantity=quantity) for price, quantity in snapshot['asks']],
            is_snapshot=True,
            version=version
        )

    def _create_incremental_update(self, symbol, updates, version):
        return OrderBookUpdate(
            symbol=symbol,
            is_snapshot=False,
            changes=[
                PriceLevelUpdate(
                    price=str(update['price']),
                    quantity=update['quantity'],
                    side=Side.BID if update['side'] == 'buy' else Side.ASK,
                    action=Action.ADD if update['action'] == 'add' else Action.UPDATE if update['action'] == 'update' else Action.DELETE
                )
                for update in updates
            ],
            version=version
        )

    def _create_empty_update(self, symbol):
        return OrderBookUpdate(symbol=symbol, is_snapshot=True, version=0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_OrderBookServiceServicer_to_server(OrderBookServer(), server)
    with open('src/config.json') as config_file:
        config = json.load(config_file)
    server.add_insecure_port(f'[::]:{config["server_port"]}')
    server.start()
    print(f"Server started on port {config['server_port']}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()