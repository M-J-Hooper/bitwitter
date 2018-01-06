import helper

tweets = helper.get_mongodb_collection("tweets")
tweet_data = {"sentiments": [], "timestamps": []}
include_links = False
for tweet in tweets.find().sort("timestamp"):
    if include_links or "http" not in tweet["text"]:
        tweet_data["timestamps"].append(tweet["timestamp"])
        tweet_data["sentiments"].append(tweet["sentiment"])
helper.save_data(tweet_data, "historical_tweets")

prices = helper.get_mongodb_collection("prices")
price_data = {"prices": [], "timestamps": []}
for price in prices.find().sort("timestamp"):
    price_data["timestamps"].append(price["timestamp"])
    price_data["prices"].append(price["price"])
helper.save_data(price_data, "historical_prices")



