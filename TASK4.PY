pip install yfinance matplotlib pandas
import yfinance as yf
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import logging
import threading
import time
from datetime import datetime

# ----------- CONFIGURATION -----------
DB_NAME = "stock_history.db"
LOG_FILE = "stock_monitor.log"
PLOT_INTERVAL = 60  # seconds
FETCH_INTERVAL = 60  # seconds
# -------------------------------------

# ----------- SETUP -----------
# Logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

# Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    ticker TEXT,
                    price REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

def save_price(ticker, price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO history (ticker, price) VALUES (?, ?)", (ticker, price))
    conn.commit()
    conn.close()

def generate_report():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM history", conn)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_stock_report.csv"
    df.to_csv(filename, index=False)
    print(f"\n✅ Report saved as {filename}")

# ----------- CORE FUNCTIONS -----------

def fetch_price(ticker):
    data = yf.Ticker(ticker).history(period="1d", interval="1m")
    if not data.empty:
        return data['Close'].iloc[-1]
    return None

def start_tracking(ticker, high=None, low=None):
    print(f"\n📡 Tracking {ticker}... Press Ctrl+C to stop.")
    try:
        while True:
            price = fetch_price(ticker)
            if price:
                print(f"{datetime.now().strftime('%H:%M:%S')} - {ticker}: ${price:.2f}")
                logging.info(f"{ticker} price: ${price:.2f}")
                save_price(ticker, price)
                if high and price >= high:
                    print("📈 ALERT: Price crossed upper threshold!")
                if low and price <= low:
                    print("📉 ALERT: Price dropped below lower threshold!")
            else:
                print("❌ Failed to fetch price.")
            time.sleep(FETCH_INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Stopped tracking.")

def live_plot(ticker):
    prices = []
    timestamps = []
    plt.ion()
    fig, ax = plt.subplots()
    
    try:
        while True:
            price = fetch_price(ticker)
            if price:
                prices.append(price)
                timestamps.append(datetime.now().strftime('%H:%M:%S'))
                ax.clear()
                ax.plot(timestamps, prices, marker='o', color='blue')
                ax.set_title(f"Live Price for {ticker}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Price ($)")
                ax.grid(True)
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.pause(0.01)
            time.sleep(PLOT_INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Plotting stopped.")
        plt.ioff()
        plt.show()

# ----------- MAIN -----------

def main():
    init_db()
    print("📊 Real-Time Stock Monitor")
    ticker = input("Enter stock ticker (e.g., AAPL): ").upper()

    use_plot = input("Do you want to see a live graph? (y/n): ").strip().lower() == 'y'

    try:
        high = float(input("Set HIGH alert threshold (or leave blank): ") or 0)
        low = float(input("Set LOW alert threshold (or leave blank): ") or 0)
    except ValueError:
        high = low = None

    if use_plot:
        plot_thread = threading.Thread(target=live_plot, args=(ticker,), daemon=True)
        plot_thread.start()

    start_tracking(ticker, high if high > 0 else None, low if low > 0 else None)

    if input("Generate report? (y/n): ").strip().lower() == 'y':
        generate_report()

if __name__ == "__main__":
    main()
