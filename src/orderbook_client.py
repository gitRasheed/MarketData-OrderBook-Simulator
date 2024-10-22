import grpc
import json
import argparse
from .orderbook_service_pb2 import SubscriptionRequest, Order, OrderBookUpdate
from .orderbook_service_pb2_grpc import OrderBookServiceStub

class OrderBookClient:
    def __init__(self):
        with open('src/config.json') as config_file:
            config = json.load(config_file)
        channel = grpc.insecure_channel(f'localhost:{config["server_port"]}')
        self.stub = OrderBookServiceStub(channel)

    def subscribe_order_book(self, symbol):
        def request_iterator():
            yield SubscriptionRequest(symbol=symbol, subscribe=True)
            while True:
                user_input = input("Enter 'u' to unsubscribe or press Enter to continue: ")
                if user_input.lower() == 'u':
                    yield SubscriptionRequest(symbol=symbol, subscribe=False)
                    break

        try:
            for update in self.stub.SubscribeOrderBook(request_iterator()):
                self._handle_update(update)
        except grpc.RpcError as e:
            print(f"RPC error: {e}")

    def _handle_update(self, update: OrderBookUpdate):
        print(f"Received update for {update.symbol}:")
        if update.is_snapshot:
            print("Snapshot:")
            print("Bids:")
            for bid in update.bids:
                print(f"  Price: {bid.price}, Quantity: {bid.quantity}")
            print("Asks:")
            for ask in update.asks:
                print(f"  Price: {ask.price}, Quantity: {ask.quantity}")
        else:
            print("Incremental Update:")
            for change in update.changes:
                print(f"  {'Bid' if change.side == 0 else 'Ask'} - "
                      f"Price: {change.price}, Quantity: {change.quantity}, "
                      f"Action: {'Add' if change.action == 0 else 'Update' if change.action == 1 else 'Delete'}")
        print("------------------------")

    def place_order(self, symbol, order_id, side, order_type, price, quantity):
        order = Order(
            symbol=symbol,
            order_id=order_id,
            side=side,
            type=order_type,
            price=str(price) if order_type == "limit" else "",
            quantity=quantity
        )
        try:
            response = self.stub.PlaceOrder(order)
            print(f"Order placed: ID = {response.order_id}, Status = {response.status}")
        except grpc.RpcError as e:
            print(f"RPC error: {e}")

def main():
    parser = argparse.ArgumentParser(description="OrderBook Client")
    parser.add_argument('action', choices=['subscribe', 'place_order'], help="Action to perform")
    parser.add_argument('--symbol', required=True, help="Symbol to subscribe or place order for")
    parser.add_argument('--order_id', help="Order ID for placing an order")
    parser.add_argument('--side', choices=['buy', 'sell'], help="Order side")
    parser.add_argument('--type', choices=['market', 'limit'], help="Order type")
    parser.add_argument('--price', type=float, help="Order price (for limit orders)")
    parser.add_argument('--quantity', type=int, help="Order quantity")

    args = parser.parse_args()
    client = OrderBookClient()

    if args.action == 'subscribe':
        client.subscribe_order_book(args.symbol)
    elif args.action == 'place_order':
        if not all([args.order_id, args.side, args.type, args.quantity]):
            parser.error("place_order requires order_id, side, type, and quantity")
        if args.type == 'limit' and args.price is None:
            parser.error("limit orders require a price")
        client.place_order(args.symbol, args.order_id, args.side, args.type, args.price, args.quantity)

if __name__ == '__main__':
    main()