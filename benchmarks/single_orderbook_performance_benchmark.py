import sys
import os
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

def setup_orderbook(num_initial_orders, min_price, max_price, tick_size):
    ticker = Ticker("TEST", str(tick_size))
    orderbook = Orderbook(ticker)
    
    sides = rng.choice(["buy", "sell"], size=num_initial_orders)
    prices = generate_tick_appropriate_prices(num_initial_orders, min_price, max_price, tick_size)
    quantities = rng.integers(1, 101, size=num_initial_orders)
    
    for i in range(num_initial_orders):
        order = Order(i, "limit", sides[i], Decimal(str(prices[i])), Decimal(str(quantities[i])), "TEST")
        orderbook.add_order(order)
    
    return orderbook

def generate_tick_appropriate_prices(num_prices, min_price, max_price, tick_size):
    ticks = np.arange(min_price, max_price + tick_size, tick_size)
    return rng.choice(ticks, size=num_prices)

def generate_order_params(num_orders, min_price, max_price, tick_size):
    order_ids = rng.integers(1, 10000001, size=num_orders)
    sides = rng.choice(["buy", "sell"], size=num_orders)
    prices = generate_tick_appropriate_prices(num_orders, min_price, max_price, tick_size)
    quantities = rng.integers(1, 101, size=num_orders)
    return order_ids, sides, prices, quantities

def benchmark_add_limit_order(orderbook, params):
    order_id, side, price, quantity = next(params)
    order = Order(order_id, "limit", side, Decimal(str(price)), Decimal(str(quantity)), "TEST")
    orderbook.add_order(order)

def benchmark_cancel_order(orderbook):
    if orderbook.orders:
        order_id = rng.choice(list(orderbook.orders.keys()))
        try:
            orderbook.cancel_order(order_id)
        except OrderNotFoundException:
            pass  # Ignore if the order was already removed

def benchmark_process_market_order(orderbook, params):
    order_id, side, _, quantity = next(params)
    order = Order(order_id, "market", side, None, Decimal(str(quantity)), "TEST")
    try:
        orderbook.add_order(order)
    except InsufficientLiquidityException:
        pass

def benchmark_get_best_bid_ask(orderbook):
    _ = orderbook.best_bid_ask

def benchmark_get_order_book_snapshot(orderbook):
    orderbook.get_order_book_snapshot(10)

def run_mixed_workload(orderbook, num_operations, params):
    operations = [
        ("Add limit order", lambda: benchmark_add_limit_order(orderbook, params)),
        ("Cancel order", lambda: benchmark_cancel_order(orderbook)),
        ("Process market order", lambda: benchmark_process_market_order(orderbook, params)),
        ("Get best bid ask", lambda: benchmark_get_best_bid_ask(orderbook)),
        ("Get order book snapshot", lambda: benchmark_get_order_book_snapshot(orderbook))
    ]
    
    op_sequence = rng.choice(len(operations), size=num_operations, p=[0.45, 0.25, 0.10, 0.10, 0.10])
    
    latencies = defaultdict(list)
    
    for op_index in op_sequence:
        op_name, op = operations[op_index]
        start_time = timeit.default_timer()
        op()
        end_time = timeit.default_timer()
        latencies[op_name].append(end_time - start_time)
    
    return latencies

def print_latency_stats(latencies):
    print(f"{'Operation':<25} {'Mean (μs)':<12} {'Median (μs)':<12} {'95th % (μs)':<12} {'99th % (μs)':<12} {'Ops/sec':<12}")
    print("-" * 75)
    
    sorted_operations = sorted(latencies.keys())
    
    for op in sorted_operations:
        times = latencies[op]
        times_us = np.array(times) * 1e6
        mean = np.mean(times_us)
        median = np.median(times_us)
        percentile_95 = np.percentile(times_us, 95)
        percentile_99 = np.percentile(times_us, 99)
        ops_per_sec = len(times) / sum(times)
        print(f"{op:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}")

def plot_latency_distribution(latencies, results_dir):
    fig = make_subplots(rows=2, cols=3, subplot_titles=list(latencies.keys()))
    row, col = 1, 1
    for op, times in latencies.items():
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

        sorted_operations = sorted(latencies.keys())
        
        for op in sorted_operations:
            times = latencies[op]
            times_us = np.array(times) * 1e6
            mean = np.mean(times_us)
            median = np.median(times_us)
            percentile_95 = np.percentile(times_us, 95)
            percentile_99 = np.percentile(times_us, 99)
            ops_per_sec = len(times) / sum(times)

            summary += f"{op:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}\n"

        summary += "\n"

    summary += "Overall Performance Summary\n"
    summary += "-" * 80 + "\n"
    summary += f"{'Operation':<25} {'Avg Time (s)':<15} {'Ops/sec':<12}\n"
    summary += "-" * 80 + "\n"

    overall_latencies = defaultdict(list)
    for size in all_latencies:
        for op in all_latencies[size]:
            overall_latencies[op].extend(all_latencies[size][op])

    sorted_operations = sorted(overall_latencies.keys())
    
    for op in sorted_operations:
        times = overall_latencies[op]
        avg_time = np.mean(times)
        ops_per_sec = len(times) / sum(times)
        summary += f"{op:<25} {avg_time:<15.6f} {ops_per_sec:<12.2f}\n"

    return summary

def save_results(all_latencies):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"benchmarks/previous_benchmark_results/single_orderbook/{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    results = {
        "seed": SEED,
        "latencies": {size: {op: times for op, times in latencies.items()} for size, latencies in all_latencies.items()},
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
    order_book_sizes = [10**4, 10**5, 10**6]
    num_operations = 100000

    all_latencies = {}

    for size in order_book_sizes:
        print(f"\nRunning benchmark for order book size: {size}")
        
        setup_start = time.time()
        orderbook = setup_orderbook(size, min_price, max_price, tick_size)
        setup_end = time.time()
        print(f"Setup time: {setup_end - setup_start:.2f} seconds")

        params = zip(*generate_order_params(num_operations, min_price, max_price, tick_size))

        workload_start = time.time()
        latencies = run_mixed_workload(orderbook, num_operations, params)
        workload_end = time.time()
        print(f"Workload time: {workload_end - workload_start:.2f} seconds")

        all_latencies[size] = latencies
        print_latency_stats(latencies)

    save_start = time.time()
    results_dir = save_results(all_latencies)
    save_end = time.time()
    print(f"Save time: {save_end - save_start:.2f} seconds")
    print(f"Results saved to: {results_dir}")

    with open(f"{results_dir}/summary.txt", "r", encoding='utf-8') as f:
        print("\nBenchmark Summary:")
        print(f.read())

if __name__ == "__main__":
    run_benchmarks()