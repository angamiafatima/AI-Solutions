import csv
import random
from datetime import datetime, timedelta
import uuid
import time
import threading
import os

# Constants
filename = "web_sales_logs.csv"

# Country-region mapping
countries_continents = {
    "UK": "Europe",
    "USA": "North America",
    "India": "Asia",
    "Germany": "Europe",
    "Japan": "Asia",
    "Canada": "North America",
    "Brazil": "South America"
}

# Simulated device/browser/job/product info
device_types = ["Desktop", "Mobile", "Tablet"]
browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
methods = ["GET", "POST"]
paths = ["/index.html", "/event.php", "/scheduledemo.php", "/prototype.php", "/chatbot.php"]

job_types = {
    "/index.html": "Browse",
    "/event.php": "Event",
    "/scheduledemo.php": "Demo",
    "/prototype.php": "Prototype",
    "/chatbot.php": "Assistant"
}

products_prices_costs = {
    "Browse": {"name": "Web Access", "price": 0, "cost": 0},
    "Event": {"name": "Event Access", "price": 0, "cost": 0},
    "Demo": {"name": "Demo Pack", "price": 19.99, "cost": 12.00},
    "Prototype": {"name": "AI Toolkit", "price": 49.99, "cost": 32.00},
    "Assistant": {"name": "ChatBot Pro", "price": 149.99, "cost": 98.00}
}

def random_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))

def weighted_random_hour(region):
    region_hour_weights = {
        "North America": [(6, 9, 0.1), (9, 17, 0.4), (17, 21, 0.3), (21, 24, 0.15), (0, 6, 0.05)],
        "Europe":        [(7, 9, 0.1), (9, 17, 0.5), (17, 21, 0.3), (21, 24, 0.07), (0, 6, 0.03)],
        "Asia":          [(8, 10, 0.1), (10, 18, 0.5), (18, 22, 0.3), (22, 24, 0.07), (0, 8, 0.03)],
        "South America": [(9, 12, 0.2), (12, 16, 0.5), (16, 20, 0.2), (20, 24, 0.08), (0, 9, 0.02)]
    }
    weights = region_hour_weights.get(region, [(0, 24, 1.0)])
    r = random.random()
    cumulative = 0
    for (start_hour, end_hour, weight) in weights:
        cumulative += weight
        if r < cumulative:
            return random.randint(start_hour, end_hour - 1)
    return random.randint(0, 23)

def random_timestamp(region, start_date=datetime(2024, 4, 20)):
    end_date = datetime.now()
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_day_offset = random.randint(0, days_between_dates)
    random_date = start_date + timedelta(days=random_day_offset)
    if random_date.weekday() >= 5 and random.random() < 0.6:
        random_date -= timedelta(days=random_date.weekday() - random.randint(0, 4))
    hour = weighted_random_hour(region)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(year=random_date.year, month=random_date.month, day=random_date.day, hour=hour, minute=minute, second=second)

def generate_entry(entry_id):
    uid = str(uuid.uuid4())
    country = random.choices(population=list(countries_continents.keys()), weights=[0.25, 0.2, 0.15, 0.1, 0.1, 0.1, 0.1])[0]
    continent = countries_continents[country]
    timestamp_dt = random_timestamp(continent)
    timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
    year, month, day, hour = timestamp_dt.year, timestamp_dt.month, timestamp_dt.day, timestamp_dt.hour
    day_of_week = timestamp_dt.strftime("%A")
    ip = random_ip()
    method = random.choice(methods)
    path = random.choice(paths)
    job = job_types[path]
    product_info = products_prices_costs[job]
    product_name, price, cost_per_item = product_info["name"], product_info["price"], product_info["cost"]
    quantity, revenue, cost = 0, 0.00, 0.00
    sales_status = "Not Applicable"
    if price > 0:
        sale_probability = 0.2 + (0.1 * random.random())
        if random.random() > sale_probability:
            sales_status = random.choice(["Complete", "In Progress"])
            quantity = random.randint(1, 5)
            revenue = round(quantity * price, 2)
            cost = round(quantity * cost_per_item, 2)
        else:
            sales_status = "Cancelled"
    else:
        sales_status = "Browse/Event"
    session_duration = round(random.uniform(5, 300), 2)
    device = random.choice(device_types)
    browser = random.choice(browsers)
    return [
        entry_id, uid, timestamp, year, month, day, hour, day_of_week,
        ip, country, continent, method, path,
        job, product_name, price, quantity, revenue, cost,
        sales_status, session_duration, device, browser
    ]

def generate_logs(filename=filename, count=5000):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            "id", "user_id", "timestamp", "year", "month", "day", "hour", "day_of_week",
            "ip_address", "country", "continent", "request_method", "request_path",
            "job_type", "product", "product_price", "quantity", "revenue", "cost",
            "sales_status", "session_duration", "device_type", "browser"
        ])
        for i in range(1, count + 1):
            writer.writerow(generate_entry(i))
    print(f"✅ Initial {count} log entries saved to '{filename}' successfully!")

def generate_single_record(record_id):
    return generate_entry(record_id)

def append_continuous_logs(start_id=5001):
    record_id = start_id
    while True:
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(generate_single_record(record_id))
        record_id += 1
        time.sleep(5)

def start_log_generation():
    if not os.path.exists(filename):
        generate_logs()
    log_thread = threading.Thread(target=append_continuous_logs, daemon=True)
    log_thread.start()
    print("🚀 Real-time log generation started in background thread.")

if __name__ == "__main__":
    generate_logs()
