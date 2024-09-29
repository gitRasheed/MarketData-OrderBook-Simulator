import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import timeit
import time
from decimal import Decimal
from src.orderbook import Orderbook
from src.order import Order
from src.ticker import Ticker
import numpy as np
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from src.exceptions import InsufficientLiquidityException, OrderNotFoundException

SEED = 42
rng = np.random.default_rng(SEED)

def setup_orderbooks(num_orderbooks, num_initial_orders, min_price, max_price, tick_size):
    orderbooks = []
    for i in range(num_orderbooks):
        ticker = Ticker(f"TEST{i}", str(tick_size))
        orderbook = Orderbook(ticker)
        
        mid_price = (min_price + max_price) / 2
        buy_prices = generate_tick_appropriate_prices(num_initial_orders // 2, min_price, mid_price, tick_size)
        sell_prices = generate_tick_appropriate_prices(num_initial_orders // 2, mid_price, max_price, tick_size)
        
        quantities = rng.integers(100, 1001, size=num_initial_orders)
        
        for j in range(num_initial_orders // 2):
            buy_order = Order(j, "limit", "buy", Decimal(str(buy_prices[j])), quantities[j], f"TEST{i}")
            sell_order = Order(j + num_initial_orders // 2, "limit", "sell", Decimal(str(sell_prices[j])), quantities[j + num_initial_orders // 2], f"TEST{i}")
            orderbook.add_order(buy_order)
            orderbook.add_order(sell_order)
        
        orderbooks.append(orderbook)
    
    return orderbooks

def generate_tick_appropriate_prices(num_prices, min_price, max_price, tick_size):
    ticks = np.arange(min_price, max_price + tick_size, tick_size)
    return rng.choice(ticks, size=num_prices)

def generate_limit_order_params(num_orders, min_price, max_price, tick_size, orderbooks):
    order_ids = rng.integers(1, 10000001, size=num_orders)
    sides = rng.choice(["buy", "sell"], size=num_orders)
    orderbook_indices = rng.integers(0, len(orderbooks), size=num_orders)
    
    prices = []
    quantities = []
    
    for side, orderbook_index in zip(sides, orderbook_indices):
        orderbook = orderbooks[orderbook_index]
        if side == "buy":
            price = generate_tick_appropriate_prices(1, min_price, orderbook.best_ask or max_price, tick_size)[0]
        else:
            price = generate_tick_appropriate_prices(1, orderbook.best_bid or min_price, max_price, tick_size)[0]
        prices.append(price)
        
        quantity = rng.integers(1, 101)
        quantities.append(quantity)
    
    return order_ids, sides, prices, quantities, orderbook_indices

def generate_market_order_params(num_orders, orderbooks):
    order_ids = rng.integers(1, 10000001, size=num_orders)
    sides = rng.choice(["buy", "sell"], size=num_orders)
    orderbook_indices = rng.integers(0, len(orderbooks), size=num_orders)
    quantities = []
    
    for side, orderbook_index in zip(sides, orderbook_indices):
        orderbook = orderbooks[orderbook_index]
        snapshot = orderbook.get_order_book_snapshot(10)
        available_liquidity = sum(level[1] for level in snapshot[("asks" if side == "buy" else "bids")])
        quantity = min(rng.integers(1, 101), max(1, available_liquidity // 100))
        quantities.append(quantity)
    
    return order_ids, sides, quantities, orderbook_indices

def benchmark_add_limit_order(orderbooks, params):
    order_id, side, price, quantity, orderbook_index = next(params)
    orderbook = orderbooks[orderbook_index]
    order = Order(order_id, "limit", side, Decimal(str(price)), quantity, orderbook.ticker.symbol)
    orderbook.add_order(order)

def benchmark_cancel_order(orderbooks):
    orderbook = rng.choice(orderbooks)
    if orderbook.orders:
        order_id = rng.choice(list(orderbook.orders.keys()))
        try:
            orderbook.cancel_order(order_id)
        except OrderNotFoundException:
            pass

def benchmark_process_market_order(orderbooks, params):
    order_id, side, quantity, orderbook_index = next(params)
    orderbook = orderbooks[orderbook_index]
    order = Order(order_id, "market", side, None, quantity, orderbook.ticker.symbol)
    try:
        orderbook.add_order(order)
    except InsufficientLiquidityException:
        pass

def benchmark_get_best_bid_ask(orderbooks):
    orderbook = rng.choice(orderbooks)
    _ = orderbook.best_bid_ask

def benchmark_get_order_book_snapshot(orderbooks):
    orderbook = rng.choice(orderbooks)
    orderbook.get_order_book_snapshot(10)

def run_single_operation_benchmark(orderbooks, num_operations, operation, params=None):
    latencies = []
    
    for _ in range(num_operations):
        start_time = timeit.default_timer()
        if operation == "Add limit order":
            benchmark_add_limit_order(orderbooks, params)
        elif operation == "Cancel order":
            benchmark_cancel_order(orderbooks)
        elif operation == "Process market order":
            benchmark_process_market_order(orderbooks, params)
        elif operation == "Get best bid ask":
            benchmark_get_best_bid_ask(orderbooks)
        elif operation == "Get order book snapshot":
            benchmark_get_order_book_snapshot(orderbooks)
        end_time = timeit.default_timer()
        latencies.append(end_time - start_time)
    
    return latencies

def print_latency_stats(operation, latencies):
    times_us = np.array(latencies) * 1e6
    mean = np.mean(times_us)
    median = np.median(times_us)
    percentile_95 = np.percentile(times_us, 95)
    percentile_99 = np.percentile(times_us, 99)
    ops_per_sec = len(latencies) / sum(latencies)
    print(f"{operation:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}")

def plot_latency_distribution(all_latencies, results_dir):
    fig = make_subplots(rows=2, cols=3, subplot_titles=list(all_latencies.keys()))
    row, col = 1, 1
    for op, times in all_latencies.items():
        times_us = np.array(times) * 1e6
        fig.add_trace(go.Histogram(x=times_us, name=op), row=row, col=col)
        fig.update_xaxes(title_text="Latency (μs)", row=row, col=col)
        fig.update_yaxes(title_text="Frequency", row=row, col=col)
        col += 1
        if col > 3:
            row += 1
            col = 1
    fig.update_layout(height=800, width=1200, title_text="Latency Distribution for Different Operations")

    filename = f"{results_dir}/latency_distribution.png"
    fig.write_image(filename)
    print(f"Latency distribution plot saved to: {filename}")

def plot_throughput_vs_orderbook_size(sizes, all_latencies, results_dir):
    fig = go.Figure()
    for op in all_latencies[sizes[0]].keys():
        y = [len(all_latencies[size][op]) / sum(all_latencies[size][op]) for size in sizes]
        fig.add_trace(go.Scatter(x=sizes, y=y, mode='lines+markers', name=op))
    fig.update_layout(title='Throughput vs Order Book Size',
                      xaxis_title='Order Book Size',
                      yaxis_title='Throughput (ops/sec)',
                      xaxis_type="log")
    
    filename = f"{results_dir}/throughput.png"
    fig.write_image(filename)
    print(f"Throughput plot saved to: {filename}")

def generate_summary(all_latencies):
    summary = "Benchmark Summary\n"
    summary += "=" * 80 + "\n\n"
    summary += f"Random Seed: {SEED}\n\n"

    for size, latencies in all_latencies.items():
        summary += f"Order Book Size: {size}\n"
        summary += "-" * 80 + "\n"
        summary += f"{'Operation':<25} {'Mean (μs)':<12} {'Median (μs)':<12} {'95th % (μs)':<12} {'99th % (μs)':<12} {'Ops/sec':<12}\n"
        summary += "-" * 80 + "\n"

        for op, times in latencies.items():
            times_us = np.array(times) * 1e6
            mean = np.mean(times_us)
            median = np.median(times_us)
            percentile_95 = np.percentile(times_us, 95)
            percentile_99 = np.percentile(times_us, 99)
            ops_per_sec = len(times) / sum(times)

            summary += f"{op:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}\n"

        summary += "\n"

    return summary

def save_results(all_latencies):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"benchmarks/previous_benchmark_results/multiple_orderbook/{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    results = {
        "seed": SEED,
        "latencies": all_latencies,
    }

    summary = generate_summary(all_latencies)
    results["summary"] = summary

    summary_file = f"{results_dir}/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    json_file = f"{results_dir}/results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    plot_latency_distribution(all_latencies[max(all_latencies.keys())], results_dir)
    plot_throughput_vs_orderbook_size(list(all_latencies.keys()), all_latencies, results_dir)

    return results_dir


def run_benchmarks():
    tick_size = Decimal('0.01')
    min_price = Decimal('90')
    max_price = Decimal('110')
    num_orderbooks = 10
    order_book_sizes = [10**4, 10**5, 10**6]
    num_operations = 100000

    all_latencies = {}

    for size in order_book_sizes:
        print(f"\nRunning benchmark for {num_orderbooks} orderbooks with size: {size}")
        
        setup_start = time.time()
        initial_orderbooks = setup_orderbooks(num_orderbooks, size, min_price, max_price, tick_size)
        setup_end = time.time()
        print(f"Setup time: {setup_end - setup_start:.2f} seconds")

        size_latencies = {}
        
        operations = [
            "Add limit order",
            "Cancel order",
            "Process market order",
            "Get best bid ask",
            "Get order book snapshot"
        ]

        print(f"{'Operation':<25} {'Mean (μs)':<12} {'Median (μs)':<12} {'95th % (μs)':<12} {'99th % (μs)':<12} {'Ops/sec':<12}")
        print("-" * 85)

        for operation in operations:
            orderbooks = copy.deepcopy(initial_orderbooks)

            if operation == "Add limit order":
                params = iter(zip(*generate_limit_order_params(num_operations, min_price, max_price, tick_size, orderbooks)))
            elif operation == "Process market order":
                params = iter(zip(*generate_market_order_params(num_operations, orderbooks)))
            else:
                params = None

            latencies = run_single_operation_benchmark(orderbooks, num_operations, operation, params)
            size_latencies[operation] = latencies
            print_latency_stats(operation, latencies)

        all_latencies[size] = size_latencies

    save_start = time.time()
    results_dir = save_results(all_latencies)
    save_end = time.time()
    print(f"\nSave time: {save_end - save_start:.2f} seconds")
    print(f"Results saved to: {results_dir}")

    with open(f"{results_dir}/summary.txt", "r", encoding='utf-8') as f:
        print("\nBenchmark Summary:")
        print(f.read())

if __name__ == "__main__":
    run_benchmarks()