import json
import tweepy
import helper
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = helper.init_logger()
conf = helper.get_config()
vader = SentimentIntensityAnalyzer()
tweets = helper.get_mongodb_collection("tweets")

class StreamListener(tweepy.StreamListener):    
    def on_connect(self):
        self.count = 0
        self.health_check_count = 10000
        self.health_check_rate = 0.5
        self.timer = helper.timestamp_from_datetime(datetime.now())
        logger.info("Tweet stream listener connected to twitter API")

    def on_error(self, status_code):
        logger.error("Tweet stream listener error with code {0}".format(status_code))
        return False

    def on_data(self, data):
        try:
            tweet = json.loads(data)
            text = tweet["text"]
            if not tweet["retweeted"] and "RT @" not in text:
                timestamp = tweet["timestamp_ms"]
                sentiment = vader.polarity_scores(text)["compound"]
                store = {"timestamp": timestamp, "sentiment": sentiment, "text": text}
                tweets.insert(store)
                print(store)

                self.count += 1
                if self.count == self.health_check_count:
                    rate = self.health_check_count * 1000 / (int(timestamp) - self.timer)
                    logger.info("Health check after {0} tweets yields {1} per second".format(self.health_check_count, rate))
                    if rate < self.health_check_rate:
                        logger.warning("Rate of {0} per second is lower than healthy threshold of {1}".format(rate, self.health_check_rate))

                    self.timer = int(timestamp)
                    self.count = 0

        except Exception as e:
            logger.exception("Error processing tweet")


if __name__ == "__main__":
    try:
        auth = helper.get_twitter_auth()
        listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True)) 
        streamer = tweepy.Stream(auth=auth, listener=listener)
        streamer.filter(track=conf["words"], languages=["en"]) 
    except Exception as e:
        logger.exception("Tweet stream listener error")
