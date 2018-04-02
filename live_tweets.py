import json
import tweepy
import helper
import api
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = helper.get_logger("live_tweets")
conf = helper.get_config()
vader = SentimentIntensityAnalyzer()
tweets = helper.get_mongodb_collection("tweets")

class StreamListener(tweepy.StreamListener):    
    def on_connect(self):
        self.count = 0
        self.succeded = 0
        self.failed = 0
        self.sentiment_sum = 0
        self.health_check_count = 50000
        self.health_check_rate = 0.1
        self.health_check_failure_percent = 1
        self.timer = helper.timestamp_from_datetime(datetime.now())
        logger.info("Tweet stream listener connected to twitter API")

    def on_error(self, status_code):
        logger.critical("Tweet stream listener error with code {0}".format(status_code))
        return False

    def on_data(self, data):
        try:
            self.count += 1
            tweet = json.loads(data)
            text = tweet["text"]
            timestamp = int(tweet["timestamp_ms"])
            
            if not tweet["retweeted"] and "RT @" not in text and "http" not in text:
                sentiment = vader.polarity_scores(text)["compound"]
                self.sentiment_sum += sentiment

                store = {"timestamp": timestamp, "sentiment": sentiment, "text": text}
                tweets.insert(store)
                print(self.count, self.succeded, self.failed, store)
                self.succeded += 1
            
            if self.count == self.health_check_count:
                sentiment_avg = self.sentiment_sum / self.succeded
                rate = self.count * 1000 / (timestamp - self.timer)
                success_percent = self.succeded * 100 / self.count
                failure_percent = self.failed * 100 / self.count
                logger.info("Health check yields {0} per second with {1}% stored, {2}% failed, and average sentiment of {3}".format(rate, success_percent, failure_percent, sentiment_avg))
                if rate < self.health_check_rate:
                    logger.warning("Unhealthy rate (less than {0} per second)".format(self.health_check_rate))
                if failure_percent > self.health_check_failure_percent:
                    logger.warning("Unhealthy failure percentage (greater than {0}%)".format(self.health_check_failure_percent))

                self.timer = timestamp
                self.count = 0
                self.succeded = 0
                self.failed = 0
                self.sentiment_sum = 0

        except Exception as e:
            self.failed += 1


if __name__ == "__main__":
    try:
        auth = api.get_twitter_auth()
        words = conf["api"]["twitter"]["words"]
        listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True)) 
        streamer = tweepy.Stream(auth=auth, listener=listener)
        streamer.filter(track=words, languages=["en"]) 
    except Exception as e:
        logger.critical("Tweet stream listener error because {0}".format(str(e)))
