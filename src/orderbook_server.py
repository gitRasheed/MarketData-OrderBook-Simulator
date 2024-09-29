import grpc
from concurrent import futures
import time
import json
from .orderbook_service_pb2 import OrderBookUpdate, PriceLevel, OrderResponse
from .orderbook_service_pb2_grpc import OrderBookServiceServicer, add_OrderBookServiceServicer_to_server
from .orderbook_manager import OrderBookManager
from .order import Order
from decimal import Decimal

class OrderBookServer(OrderBookServiceServicer):
    def __init__(self):
        self.order_book_manager = OrderBookManager()
        with open('src\config.json') as config_file:
            config = json.load(config_file)
        for symbol, details in config['instruments'].items():
            self.order_book_manager.create_order_book(symbol, Decimal(details['tick_size']))

    def SubscribeOrderBook(self, request, context):
        symbol = request.symbol
        client_id = context.peer()
        self.order_book_manager.subscribe(symbol, client_id)

        try:
            while True:
                snapshot = self.order_book_manager.get_order_book_snapshot(symbol, 10)
                if snapshot:
                    yield self._create_order_book_update(symbol, snapshot, is_snapshot=True)
                time.sleep(1)  # Simulate periodic updates
        except grpc.RpcError:
            self.order_book_manager.unsubscribe(symbol, client_id)

    def PlaceOrder(self, request, context):
        order = Order(
            request.order_id,
            request.type,
            request.side,
            Decimal(request.price) if request.type == "limit" else None,
            request.quantity,
            request.symbol
        )
        order_id, _ = self.order_book_manager.process_order(order)
        return OrderResponse(order_id=str(order_id), status="PLACED")

    def _create_order_book_update(self, symbol, snapshot, is_snapshot):
        return OrderBookUpdate(
            symbol=symbol,
            bids=[PriceLevel(price=str(price), quantity=quantity) for price, quantity in snapshot['bids']],
            asks=[PriceLevel(price=str(price), quantity=quantity) for price, quantity in snapshot['asks']],
            is_snapshot=is_snapshot
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_OrderBookServiceServicer_to_server(OrderBookServer(), server)
    with open('src\config.json') as config_file:
        config = json.load(config_file)
    server.add_insecure_port(f'[::]:{config["server_port"]}')
    server.start()
    print(f"Server started on port {config['server_port']}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()