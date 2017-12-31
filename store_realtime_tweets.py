import json
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import helper

vader = SentimentIntensityAnalyzer()
tweets = helper.get_mongodb_collection("tweets")

class StreamListener(tweepy.StreamListener):    
    def on_connect(self):
        print("Connected to tweet streaming API")

    def on_error(self, status_code):
        print("Error " + repr(status_code))
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
        except Exception as e:
            print(e)

auth = helper.get_twitter_auth()
listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True)) 
streamer = tweepy.Stream(auth=auth, listener=listener)

conf = helper.get_config()
print("Focus " + str(conf["words"]))
streamer.filter(track=conf["words"], languages=["en"])
print("Stopped")
