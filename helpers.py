import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

# Generate price history graph
def generate_price_chart(prices, product_name):
    plt.figure(figsize=(6,3))
    plt.plot(prices["dates"], prices["values"], marker='o')
    plt.title(f"Price History: {product_name}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_bytes = buf.read()
    buf.close()
    return img_bytes  # Can be sent as Telegram image

# Format price change message
def format_price_alert(product, old_price, new_price):
    change = new_price - old_price
    percent = (change / old_price) * 100 if old_price else 0
    arrow = "⬇️" if change < 0 else "⬆️"
    return f"{product['name']}\nOld: ₹{old_price} -> New: ₹{new_price} {arrow} ({percent:.1f}%)\n{product['url']}"
