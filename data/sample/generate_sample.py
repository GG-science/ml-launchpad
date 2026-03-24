"""
Generate a realistic e-commerce sample dataset for ml-launchpad demos.
Produces: data/sample/ecommerce.csv (~5k rows)

Columns:
  customer_id, order_id, order_date, product_category, product_price,
  quantity, discount_pct, channel, country, days_since_last_order,
  total_orders, total_revenue, converted (target for supervised)
"""
import random
import csv
from datetime import date, timedelta

random.seed(42)

CATEGORIES = ["electronics", "clothing", "home_garden", "sports", "beauty", "books", "toys"]
CHANNELS = ["organic_search", "paid_search", "social", "email", "direct", "referral"]
COUNTRIES = ["US", "UK", "CA", "AU", "DE", "FR"]

N_CUSTOMERS = 1000
N_ROWS = 5000

rows = []
for i in range(N_ROWS):
    customer_id = f"C{random.randint(1, N_CUSTOMERS):05d}"
    order_id = f"ORD{i+1:06d}"
    order_date = date(2023, 1, 1) + timedelta(days=random.randint(0, 364))
    category = random.choice(CATEGORIES)
    price = round(random.uniform(5.0, 500.0), 2)
    quantity = random.randint(1, 5)
    discount = round(random.uniform(0, 0.4), 2)
    channel = random.choice(CHANNELS)
    country = random.choice(COUNTRIES)
    days_since = random.randint(0, 365)
    total_orders = random.randint(1, 50)
    total_revenue = round(random.uniform(10, 5000), 2)
    # converted: higher probability for email + high total_orders
    p_convert = 0.3
    if channel == "email":
        p_convert += 0.2
    if total_orders > 20:
        p_convert += 0.15
    if discount > 0.2:
        p_convert += 0.1
    converted = int(random.random() < p_convert)

    rows.append([
        customer_id, order_id, order_date.isoformat(), category,
        price, quantity, discount, channel, country,
        days_since, total_orders, total_revenue, converted
    ])

header = [
    "customer_id", "order_id", "order_date", "product_category",
    "product_price", "quantity", "discount_pct", "channel", "country",
    "days_since_last_order", "total_orders", "total_revenue", "converted"
]

out = "data/sample/ecommerce.csv"
with open(out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"Generated {N_ROWS} rows → {out}")
