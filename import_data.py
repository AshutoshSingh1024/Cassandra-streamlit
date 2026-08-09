
import csv
from cassandra.cluster import Cluster
from decimal import Decimal
from datetime import datetime

# Connect to Cassandra
cluster = Cluster(["127.0.0.1"])
session = cluster.connect("sales")

# Prepare the INSERT statement
insert_query = """
INSERT INTO sales_by_order (
    order_id,
    country,
    item_type,
    order_date,
    order_priority,
    region,
    sales_channel,
    ship_date,
    total_cost,
    total_profit,
    total_revenue,
    unit_cost,
    unit_price,
    units_sold
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

prepared = session.prepare(insert_query)

# Open CSV
with open("data/sales_10000.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    count = 0

    for row in reader:

        order_date = datetime.strptime(
            row["Order Date"], "%Y-%m-%d"
        ).date()

        ship_date = datetime.strptime(
            row["Ship Date"], "%Y-%m-%d"
        ).date()

        session.execute(
            prepared,
            (
                int(row["Order ID"]),
                row["Country"],
                row["Item Type"],
                order_date,
                row["Order Priority"],
                row["Region"],
                row["Sales Channel"],
                ship_date,
                Decimal(row["Total Cost"]),
                Decimal(row["Total Profit"]),
                Decimal(row["Total Revenue"]),
                Decimal(row["Unit Cost"]),
                Decimal(row["Unit Price"]),
                int(row["Units Sold"])
            )
        )

        count += 1

        if count % 500 == 0:
            print(f"Imported {count} records...")

print(f"Import complete. {count} records imported.")

cluster.shutdown()
