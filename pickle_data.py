import helper
import pickle
from datetime import datetime

logger = helper.get_logger("pickle_data")

def save(obj, name):
    with open(name + ".pkl", "wb") as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load(name):
    with open(name + ".pkl", "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    include_links = False
    try:
        logger.info("Started pickling tweets")
        tweets = helper.get_mongodb_collection("tweets")
        tweet_data = {"sentiments": [], "timestamps": [], "texts": []}
        count = 0
        for tweet in tweets.find().sort("timestamp"):
            if include_links or "http" not in tweet["text"]:
                tweet_data["timestamps"].append(int(tweet["timestamp"]))
                tweet_data["sentiments"].append(tweet["sentiment"])
                tweet_data["texts"].append(tweet["text"])
                count += 1
        save(tweet_data, "tweets")
        logger.info("Finished pickling {0} tweets".format(count))
    except Exception as e:
        logger.exception("Error pickling tweets")
        
    try:
        logger.info("Started pickling prices")
        prices = helper.get_mongodb_collection("prices")
        price_data = {"prices": [], "timestamps": []}
        count = 0
        for price in prices.find().sort("timestamp"):
            price_data["timestamps"].append(int(price["timestamp"]))
            price_data["prices"].append(price["price"])
            count += 1
        save(price_data, "prices")
        logger.info("Finished pickling {0} prices".format(count))
    except Exception as e:
        logger.exception("Error pickling prices")


