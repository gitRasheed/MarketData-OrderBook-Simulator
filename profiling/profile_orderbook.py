import cProfile
import pstats
import io
import sys
import os
import json
from decimal import Decimal
from line_profiler import LineProfiler
from memory_profiler import profile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orderbook import Orderbook
from src.ticker import Ticker
from src.order import Order
from src.exceptions import InsufficientLiquidityException

def load_test_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(current_dir, "test_data.json")
    with open(data_file, "r") as f:
        data = json.load(f)
    return data['orders'], data['operations']

def setup_orderbook(initial_orders, ticker):
    orderbook = Orderbook(ticker)
    for order in initial_orders:
        o = Order(order['id'], "limit", order['side'], Decimal(order['price']), Decimal(str(order['quantity'])), ticker.symbol)
        orderbook.add_order(o)
    return orderbook

def run_mixed_workload(ob, operations, orders):
    order_index = 0
    for operation in operations:
        if operation == "add":
            order = orders[order_index]
            o = Order(order['id'], "limit", order['side'], Decimal(order['price']), Decimal(str(order['quantity'])), ob.ticker.symbol)
            ob.add_order(o)
            order_index += 1
        elif operation == "cancel":
            if ob.orders:
                order_id = list(ob.orders.keys())[order_index % len(ob.orders)]
                ob.cancel_order(order_id)
        elif operation == "modify":
            if ob.orders:
                order_id = list(ob.orders.keys())[order_index % len(ob.orders)]
                new_order = orders[order_index]
                ob.modify_order(order_id, Decimal(new_order['price']), Decimal(str(new_order['quantity'])))
            order_index += 1
        elif operation == "market":
            order = orders[order_index]
            o = Order(order['id'], "market", order['side'], None, Decimal(str(order['quantity'])), ob.ticker.symbol)
            try:
                ob.add_order(o)
            except InsufficientLiquidityException:
                pass
            order_index += 1
        elif operation == "best_bid_ask":
            _ = ob.best_bid_ask
        elif operation == "snapshot":
            ob.get_order_book_snapshot(10)

def run_cprofile(ob, operations, orders):
    print("Running cProfile...")
    cProfile.runctx("run_mixed_workload(ob, operations, orders)", globals(), locals(), "profiling/profiling_results/orderbook_stats")

    s = io.StringIO()
    ps = pstats.Stats("profiling/profiling_results/orderbook_stats", stream=s).sort_stats("cumulative")
    ps.print_stats()
    with open("profiling/profiling_results/cprofile_results.txt", "w") as f:
        f.write(s.getvalue())

def run_line_profiler(ob, operations, orders):
    print("Running line_profiler...")
    lp = LineProfiler()
    lp.add_function(Orderbook.add_order)
    lp.add_function(Orderbook.cancel_order)
    lp.add_function(Orderbook.modify_order)
    lp.add_function(Orderbook.process_market_order)
    lp.add_function(Orderbook.get_order_book_snapshot)
    lp_wrapper = lp(run_mixed_workload)
    lp_wrapper(ob, operations, orders)
    with open("profiling/profiling_results/line_profiler_results.txt", "w") as f:
        lp.print_stats(stream=f)

@profile
def run_memory_profiler(ob, operations, orders):
    print("Running memory_profiler...")
    run_mixed_workload(ob, operations, orders)

def main():
    os.makedirs("profiling/profiling_results", exist_ok=True)
    
    tick_size = Decimal('0.01')
    ticker = Ticker("TEST", str(tick_size))
    
    all_orders, operations = load_test_data()
    initial_orders = all_orders[:10000]
    orders = all_orders[10000:]
    
    if "--workload" in sys.argv:
        ob = setup_orderbook(initial_orders, ticker)
        run_mixed_workload(ob, operations, orders)
    else:
        ob = setup_orderbook(initial_orders, ticker)
        run_cprofile(ob, operations, orders)
        
        ob = setup_orderbook(initial_orders, ticker)
        run_line_profiler(ob, operations, orders)
        
        ob = setup_orderbook(initial_orders, ticker)
        run_memory_profiler(ob, operations, orders)
        
        print("Profiling complete. Results are in the profiling/profiling_results directory.")
        print("To visualize cProfile results, run: snakeviz profiling/profiling_results/orderbook_stats")

if __name__ == "__main__":
    main()