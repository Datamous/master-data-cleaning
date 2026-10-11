"""Generate the deliberately messy capstone dataset for Chapter 12.

Run from this folder:  py make_data.py
Writes orders.csv and customers.csv. The seed is fixed, so the files
come out identical every time.
"""
import csv
from datetime import date, timedelta

import numpy as np

rng = np.random.default_rng(42)

# ---------------------------------------------------------------- customers
FIRST = ['Aisha', 'Daniel', 'Mei', 'Arjun', 'Fatima', 'Kevin',
         'Nora', 'Ravi', 'Sofia', 'Jason', 'Priya', 'Marcus', 'Grace',
         'Omar', 'Wei', 'Lena', 'Amir', 'Chloe', 'Diego', 'Anita']
LAST = ['Tan', 'Lopez', 'Rahman', 'Kumar', 'Wong', 'Garcia', 'Lee',
        'Nair', 'Smith', 'Johnson', 'Chen', 'Patel', 'Brown', 'Nguyen']

customer_ids = [f'C{n:03d}' for n in range(1, 51)]
customers = []
for cid in customer_ids:
    name = f'{rng.choice(FIRST)} {rng.choice(LAST)}'
    segment = rng.choice(['Consumer', 'Business'], p=[0.7, 0.3])
    customers.append([cid, name, segment])

with open('customers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'customer_name', 'segment'])
    writer.writerows(customers)

# ------------------------------------------------------------------- orders
PRODUCTS = {'Mouse': 49.90, 'Keyboard': 129.00, 'Monitor': 1099.00,
            'USB Cable': 19.90, 'Headset': 189.00, 'Webcam': 259.00}
CITIES = ['New York', 'Philadelphia', 'Los Angeles', 'Denver',
          'San Francisco', 'Seattle']
CITY_P = [0.35, 0.2, 0.15, 0.1, 0.1, 0.1]
CITY_VARIANTS = {
    'New York': [' new york', 'NYC', 'new york',
                     'NEW YORK'],
    'Philadelphia': ['philadelphia ', 'Philly', 'PHILADELPHIA'],
    'Los Angeles': ['LA', 'los angeles', 'Los Angeles '],
    'Denver': ['denver', ' Denver'],
    'San Francisco': ['san francisco', 'San Francisco '],
    'Seattle': ['seattle', 'SEATTLE'],
}
N_BASE = 194
START = date(2025, 1, 1)


def price_text(price):
    """Write a price the way a careless export might."""
    style = rng.integers(0, 4)
    if style == 0:
        return f'$ {price:,.2f}'
    if style == 1:
        return f'${price:.2f}'
    if style == 2:
        return f'{price:.2f}'
    return f'{price:,.0f}' if price == round(price) else f'{price:.1f}'


def date_text(day):
    style = rng.choice(3, p=[0.6, 0.25, 0.15])
    if style == 0:
        return day.strftime('%Y-%m-%d')
    if style == 1:
        return day.strftime('%d/%m/%Y')
    return day.strftime('%d %b %Y')


rows = []
for n in range(N_BASE):
    day = START + timedelta(days=int(rng.integers(0, 181)))
    product = str(rng.choice(list(PRODUCTS)))
    city = str(rng.choice(CITIES, p=CITY_P))
    rows.append({
        'order_id': f'ORD-{1001 + n}',
        'order_date': date_text(day),
        'customer_id': str(rng.choice(customer_ids)),
        'product': product,
        'city': city,
        'quantity': str(int(rng.integers(1, 6))),
        'unit_price': price_text(PRODUCTS[product]),
    })

# Pick disjoint sets of rows for each planted problem.
order = [int(i) for i in rng.permutation(N_BASE)]
picks = {}
for name, size in [('city_messy', 45), ('city_missing', 8),
                   ('id_messy', 6), ('id_unknown', 3),
                   ('qty_missing', 3), ('qty_outlier', 2),
                   ('price_missing', 5), ('price_negative', 2),
                   ('date_missing', 3), ('exact_dup', 4),
                   ('near_dup', 2)]:
    picks[name], order = order[:size], order[size:]

for i in picks['city_messy']:
    rows[i]['city'] = str(rng.choice(CITY_VARIANTS[rows[i]['city']]))
for k, i in enumerate(picks['city_missing']):
    rows[i]['city'] = ['', 'N/A', '-'][k % 3]
for k, i in enumerate(picks['id_messy']):
    cid = rows[i]['customer_id']
    rows[i]['customer_id'] = cid.lower() if k % 2 else f' {cid}'
for k, i in enumerate(picks['id_unknown']):
    rows[i]['customer_id'] = ['C051', 'C052', 'C051'][k]
for k, i in enumerate(picks['qty_missing']):
    rows[i]['quantity'] = ['', '-', ''][k]
for i in picks['qty_outlier']:
    rows[i]['quantity'] = '9999'
for k, i in enumerate(picks['price_missing']):
    rows[i]['unit_price'] = ['', 'N/A', '-', 'N/A', ''][k]
for i in picks['price_negative']:
    price = PRODUCTS[rows[i]['product']]
    rows[i]['unit_price'] = f'-{price:.2f}'
for k, i in enumerate(picks['date_missing']):
    rows[i]['order_date'] = ['', 'N/A', ''][k]

# Near duplicates: the same order exported twice with a different
# spelling of the city.
extra = []
for i in picks['near_dup']:
    copy = dict(rows[i])
    copy['city'] = str(rng.choice(CITY_VARIANTS[rows[i]['city']]))
    extra.append((i, copy))
for i in picks['exact_dup']:
    extra.append((i, dict(rows[i])))

# Insert each copy a few rows after its original.
for i, copy in sorted(extra, key=lambda pair: -pair[0]):
    rows.insert(i + 1 + int(rng.integers(0, 4)), copy)

with open('orders.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f'orders.csv: {len(rows)} rows, customers.csv: '
      f'{len(customers)} rows')
