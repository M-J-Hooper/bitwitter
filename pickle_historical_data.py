import helper
from datetime import datetime

logger = helper.init_logger(__name__)

logger.info("Started pickling tweets")
tweets = helper.get_mongodb_collection("tweets")
tweet_data = {"sentiments": [], "timestamps": []}
include_links = False
count = 0
for tweet in tweets.find().sort("timestamp"):
    if include_links or "http" not in tweet["text"]:
        tweet_data["timestamps"].append(int(tweet["timestamp"]))
        tweet_data["sentiments"].append(tweet["sentiment"])
        count += 1
helper.save_data(tweet_data, "historical_tweets")
logger.info("Finished pickling {0} tweets".format(count))

logger.info("Started pickling prices")
prices = helper.get_mongodb_collection("prices")
price_data = {"prices": [], "timestamps": []}
count = 0
for price in prices.find().sort("timestamp"):
    price_data["timestamps"].append(int(price["timestamp"]))
    price_data["prices"].append(price["price"])
    count += 1
helper.save_data(price_data, "historical_prices")
logger.info("Finished pickling {0} prices".format(count))



