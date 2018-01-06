import gdax
import helper
import time
from datetime import datetime

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")
params = helper.get_mongodb_collection("params")

interval_beginning = 0
include_links = False
minute = 60 * 1000
min_data_points = 50

buying = False
starting_coins = 1.0
money = 0.0
coins = 1.0
trades = 0
fee = 0.9975
while(True):
    try:
        current_timestamp = helper.timestamp_from_datetime(datetime.now()) 
        new_interval_beginning = helper.get_interval_beginning(current_timestamp, minute) 
        if new_interval_beginning > interval_beginning:
            interval_beginning = new_interval_beginning
            
            param = params.find().sort("timestamp", -1)[0]
            trade_timestamp = interval_beginning
            earliest_timestamp = trade_timestamp - param["window"]

            count = 0
            sentiment = 0.0
            for tweet in tweets.find({"timestamp": {"$gt": str(earliest_timestamp)}}):
                if include_links or "http" not in tweet["text"]:
                    count += 1
                    sentiment += tweet["sentiment"]
            sentiment = sentiment / count
            
            price = prices.find().sort("timestamp", -1)[0]["price"]
            buy_sentiment = param["average"] + param["stdevs"] * param["stdev"]
            sell_sentiment = param["average"] - param["stdevs"] * param["stdev"]
            print(helper.str_from_timestamp(earliest_timestamp), "-", helper.str_from_timestamp(trade_timestamp), ":", sell_sentiment, "-", buy_sentiment, ": Tweets", count, "Sentiment", sentiment, "Price", price, "Coins", coins, "Trades", trades)
            
            was_buying = buying
            if count >= min_data_points:
                if buying:
                    if sentiment > buy_sentiment:
                        buying = False
                        coins = money * fee / price
                        print("Buying", coins, "for", price, "due to a", sentiment, "at", helper.str_from_timestamp(trade_timestamp))
                
                if not buying:
                    if sentiment < sell_sentiment:
                        buying = True
                        money = coins * fee * price
                        print("Selling", coins, "for", price, "due to a", sentiment, "at", helper.str_from_timestamp(trade_timestamp))

            if buying != was_buying:
                trades += 1
                change = (coins - starting_coins) * 100 / starting_coins
                print("Change of", change, "after", trades, "trades using:")
                print(param)
    
    
    except Exception as e:
        print(e)
    time.sleep(1)
