import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import timeit
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
from src.exceptions import InsufficientLiquidityException

rng = np.random.default_rng(42)

def setup_orderbook(num_initial_orders, price_levels, tick_size):
    ticker = Ticker("TEST", str(tick_size))
    orderbook = Orderbook(ticker)
    
    for i in range(num_initial_orders):
        side = rng.choice(["buy", "sell"])
        price = generate_random_price(price_levels, tick_size)
        quantity = Decimal(str(rng.integers(1, 100)))
        order = Order(i, "limit", side, price, quantity, "TEST")
        orderbook.add_order(order)
    
    return orderbook

def generate_random_price(price_levels, tick_size):
    base_price = rng.choice(price_levels)
    tick_count = int(rng.integers(-50, 50))
    return (base_price + (Decimal(tick_count) * tick_size)).quantize(tick_size)

def benchmark_add_limit_order(orderbook, price_levels):
    order_id = rng.integers(1, 10000000)
    side = rng.choice(["buy", "sell"])
    price = generate_random_price(price_levels, orderbook.ticker.tick_size)
    quantity = Decimal(str(rng.integers(1, 100)))
    order = Order(order_id, "limit", side, price, quantity, "TEST")
    orderbook.add_order(order)

def benchmark_cancel_order(orderbook):
    if orderbook.orders:
        order_id = rng.choice(list(orderbook.orders.keys()))
        orderbook.cancel_order(order_id)

def benchmark_modify_order(orderbook, price_levels):
    if orderbook.orders:
        order_id = rng.choice(list(orderbook.orders.keys()))
        new_price = generate_random_price(price_levels, orderbook.ticker.tick_size)
        new_quantity = Decimal(str(rng.integers(1, 100)))
        orderbook.modify_order(order_id, new_price, new_quantity)

def benchmark_process_market_order(orderbook):
    order_id = rng.integers(1, 10000000)
    side = rng.choice(["buy", "sell"])
    quantity = Decimal(str(rng.integers(1, 50)))
    order = Order(order_id, "market", side, None, quantity, "TEST")
    try:
        orderbook.add_order(order)
    except InsufficientLiquidityException:
        pass  # Ignore insufficient liquidity errors
    except Exception as e:
        print(f"Unexpected error processing market order: {e}")

def benchmark_get_best_bid_ask(orderbook):
    _ = orderbook.best_bid_ask

def benchmark_get_order_book_snapshot(orderbook):
    orderbook.get_order_book_snapshot(10)

def run_mixed_workload(orderbook, num_operations, price_levels):
    operations = [
        ("Add limit order", lambda: benchmark_add_limit_order(orderbook, price_levels)),
        ("Cancel order", lambda: benchmark_cancel_order(orderbook)),
        ("Modify order", lambda: benchmark_modify_order(orderbook, price_levels)),
        ("Process market order", lambda: benchmark_process_market_order(orderbook)),
        ("Get best bid ask", lambda: benchmark_get_best_bid_ask(orderbook)),
        ("Get order book snapshot", lambda: benchmark_get_order_book_snapshot(orderbook))
    ]
    
    latencies = defaultdict(list)
    
    for _ in range(num_operations):
        op_name, op = rng.choice(operations, p=[0.40, 0.20, 0.15, 0.05, 0.10, 0.10])
        start_time = timeit.default_timer()
        op()
        end_time = timeit.default_timer()
        latencies[op_name].append(end_time - start_time)

    return latencies

def print_latency_stats(latencies):
    print(f"{'Operation':<25} {'Mean (μs)':<12} {'Median (μs)':<12} {'95th % (μs)':<12} {'99th % (μs)':<12} {'Ops/sec':<12}")
    print("-" * 75)
    
    # Sort the operations by name
    sorted_operations = sorted(latencies.keys())
    
    for op in sorted_operations:
        times = latencies[op]
        times_us = np.array(times) * 1e6  # Convert to microseconds
        mean = np.mean(times_us)
        median = np.median(times_us)
        percentile_95 = np.percentile(times_us, 95)
        percentile_99 = np.percentile(times_us, 99)
        ops_per_sec = len(times) / sum(times)
        print(f"{op:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}")

def plot_latency_distribution(latencies, benchmark_type, results_dir):
    fig = make_subplots(rows=2, cols=3, subplot_titles=list(latencies.keys()))
    row, col = 1, 1
    for op, times in latencies.items():
        times_us = np.array(times) * 1e6  # Convert to microseconds
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

def plot_throughput_vs_orderbook_size(sizes, throughputs, benchmark_type, results_dir):
    fig = go.Figure()
    for op in throughputs[sizes[0]].keys():
        y = [throughputs[size][op] for size in sizes]
        fig.add_trace(go.Scatter(x=sizes, y=y, mode='lines+markers', name=op))
    fig.update_layout(title='Throughput vs Order Book Size',
                      xaxis_title='Order Book Size',
                      yaxis_title='Throughput (ops/sec)',
                      xaxis_type="log")
    
    filename = f"{results_dir}/throughput.png"
    fig.write_image(filename)
    print(f"Throughput plot saved to: {filename}")

def generate_summary(all_latencies, throughputs):
    summary = "Benchmark Summary\n"
    summary += "=" * 80 + "\n\n"
    summary += f"Random Seed: {rng.bit_generator.state['state']['state']}\n\n"

    for size, latencies in all_latencies.items():
        summary += f"Order Book Size: {size}\n"
        summary += "-" * 80 + "\n"
        summary += f"{'Operation':<25} {'Mean (μs)':<12} {'Median (μs)':<12} {'95th % (μs)':<12} {'99th % (μs)':<12} {'Ops/sec':<12}\n"
        summary += "-" * 80 + "\n"

        sorted_operations = sorted(latencies.keys())
        
        for op in sorted_operations:
            times_us = np.array(latencies[op]) * 1e6
            mean = np.mean(times_us)
            median = np.median(times_us)
            percentile_95 = np.percentile(times_us, 95)
            percentile_99 = np.percentile(times_us, 99)
            ops_per_sec = throughputs[size][op]

            summary += f"{op:<25} {mean:<12.2f} {median:<12.2f} {percentile_95:<12.2f} {percentile_99:<12.2f} {ops_per_sec:<12.2f}\n"

        summary += "\n"

    summary += "Overall Performance Summary\n"
    summary += "-" * 80 + "\n"
    summary += f"{'Operation':<25} {'Avg Time (s)':<15} {'Ops/sec':<12}\n"
    summary += "-" * 80 + "\n"

    overall_latencies = defaultdict(list)
    overall_throughputs = defaultdict(list)
    for size in all_latencies:
        for op in all_latencies[size]:
            overall_latencies[op].extend(all_latencies[size][op])
            overall_throughputs[op].append(throughputs[size][op])

    sorted_operations = sorted(overall_latencies.keys())
    
    for op in sorted_operations:
        avg_time = np.mean(overall_latencies[op])
        avg_ops_per_sec = np.mean(overall_throughputs[op])
        summary += f"{op:<25} {avg_time:<15.6f} {avg_ops_per_sec:<12.2f}\n"

    return summary

def save_results(all_latencies, throughputs, benchmark_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"benchmarks/previous_benchmark_results/{benchmark_type}_orderbook/{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    results = {
        "seed": rng.bit_generator.state['state']['state'],  # Add this line
        "latencies": {size: {op: times for op, times in latencies.items()} for size, latencies in all_latencies.items()},
        "throughputs": {size: {op: float(tput) for op, tput in size_throughputs.items()}
                        for size, size_throughputs in throughputs.items()}
    }

    # Generate and save summary
    summary = generate_summary(all_latencies, throughputs)
    results["summary"] = summary

    summary_file = f"{results_dir}/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    # Save JSON results
    json_file = f"{results_dir}/results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    # Save plots
    plot_latency_distribution(all_latencies[max(all_latencies.keys())], benchmark_type, results_dir)
    plot_throughput_vs_orderbook_size(list(throughputs.keys()), throughputs, benchmark_type, results_dir)

    return results_dir

def run_benchmarks():
    tick_size = Decimal('0.01')
    price_levels = [Decimal(str(p)) for p in np.arange(90, 110.01, float(tick_size))]
    order_book_sizes = [10**3, 10**4, 10**5, 10**6]
    num_operations = 10000

    all_latencies = {}
    throughputs = {}

    for size in order_book_sizes:
        print(f"\nRunning benchmark for order book size: {size}")
        orderbook = setup_orderbook(size, price_levels, tick_size)
        latencies = run_mixed_workload(orderbook, num_operations, price_levels)
        all_latencies[size] = latencies
        print_latency_stats(latencies)

        throughputs[size] = {op: num_operations / sum(times) for op, times in latencies.items()}

    # Save results
    results_dir = save_results(all_latencies, throughputs, "single")
    print(f"Results saved to: {results_dir}")

    # Print the summary (which is already generated and saved in save_results)
    with open(f"{results_dir}/summary.txt", "r", encoding='utf-8') as f:
        print("\nBenchmark Summary:")
        print(f.read())

if __name__ == "__main__":
    run_benchmarks()