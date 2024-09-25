import numpy as np
from decimal import Decimal
import json

SEED = 42
rng = np.random.default_rng(SEED)

def generate_preset_data(num_orders, num_operations, min_price, max_price, tick_size):
    order_ids = rng.integers(1, 10000001, size=num_orders)
    sides = rng.choice(["buy", "sell"], size=num_orders)
    
    # Generate prices that are exact multiples of tick_size
    num_ticks = int((max_price - min_price) / tick_size) + 1
    ticks = [str(min_price + i * tick_size) for i in range(num_ticks)]
    prices = rng.choice(ticks, size=num_orders)
    
    quantities = rng.integers(1, 101, size=num_orders)
    
    operations = rng.choice(["add", "cancel", "modify", "market", "best_bid_ask", "snapshot"], 
                            size=num_operations, 
                            p=[0.40, 0.20, 0.15, 0.05, 0.10, 0.10])
    
    return {
        "orders": [{"id": int(id), "side": side, "price": price, "quantity": int(quantity)} 
                   for id, side, price, quantity in zip(order_ids, sides, prices, quantities)],
        "operations": operations.tolist()
    }

if __name__ == "__main__":
    tick_size = Decimal('0.01')
    min_price = Decimal('90')
    max_price = Decimal('110')
    
    data = generate_preset_data(20000, 10000, min_price, max_price, tick_size)
    
    with open("test_data.json", "w") as f:
        json.dump(data, f)

    print("Test data generated and saved to test_data.json")