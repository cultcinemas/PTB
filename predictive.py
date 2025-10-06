import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime
from db_manager import MongoManager
from notifications import send_price_alert

db = MongoManager()

class PricePredictor:
    def __init__(self):
        # You can load a pre-trained model if available
        self.model = LinearRegression()

    def prepare_data(self, price_history):
        """
        Convert price history into features for prediction.
        price_history: list of dicts [{"date": datetime, "price": float}, ...]
        """
        if not price_history:
            return None, None
        df = pd.DataFrame(price_history)
        df['timestamp'] = df['date'].apply(lambda x: x.timestamp())
        X = df['timestamp'].values.reshape(-1, 1)
        y = df['price'].values
        return X, y

    def predict_next_price(self, price_history):
        X, y = self.prepare_data(price_history)
        if X is None or len(X) < 2:
            return None  # Not enough data
        self.model.fit(X, y)
        next_timestamp = X[-1][0] + 86400  # Predict for next day
        predicted_price = self.model.predict([[next_timestamp]])[0]
        return round(predicted_price, 2)

    async def send_predictive_alerts(self):
        # Check all products with price history
        products = list(db.products.find({"active": True, "price_history": {"$exists": True}}))
        for product in products:
            predicted = self.predict_next_price(product["price_history"])
            if predicted is None:
                continue
            current_price = product.get("price", 0)
            # Send alert if predicted drop > 3%
            if current_price > 0 and ((current_price - predicted)/current_price*100) >= 3:
                await send_price_alert(
                    product["user_id"],
                    product,
                    current_price,
                    predicted
                )
