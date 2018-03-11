import helper
import nlp
from collections import deque
import numpy as np

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")

def window_vectors(interval, window, start=0, end=10000000000000, min_data_points=500):
    model = nlp.load_model()
    interval_beginning = 0
    timestamps = deque()
    lengths = deque()
    vectors = deque()
    weights = deque()
    start_generating = False
    for tweet in tweets.find({"timestamp": {"$gt": start, "$lt": end}}).sort("timestamp"):
        if "http" not in tweet["text"]:
            timestamps.append(tweet["timestamp"])
            sentence = nlp.preprocess_text(tweet["text"])
            sentence_vectors = nlp.get_sentence_vectors(model, sentence)
            sentence_weights = nlp.get_sentence_weights(model, sentence)

            vectors.extend(sentence_vectors)
            weights.extend(sentence_weights)
            lengths.append(len(sentence_vectors))

            new_interval_beginning = helper.get_interval_beginning(tweet["timestamp"], interval)
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning
                while len(timestamps) and timestamps[0] + window <= interval_beginning:
                    if not start_generating:
                        start_generating = True
                    timestamps.popleft()
                    length = lengths.popleft()
                    for i in range(length):
                        vectors.popleft()
                        weights.popleft()
                
                if start_generating and len(timestamps) >= min_data_points:
                    yield interval_beginning, np.average(vectors, axis=0, weights=weights)


def window_vectors_with_future_price_change(interval, window, future, start=0, end=10000000000000, min_data_points=500):
    for timestamp, vector in window_vectors(interval, window, start, end, min_data_points):
        price_entry_now = prices.find_one({"timestamp": timestamp})
        price_entry_future = prices.find_one({"timestamp": (timestamp + future)})
        if price_entry_now != None and price_entry_future != None:
            price_now = price_entry_now["price"]
            price_future = price_entry_future["price"]
            change = (price_now - price_future) / price_now
            yield vector, change


def window_sentiments(interval, window, start=0, end=10000000000000, min_data_points=500):
    interval_beginning = 0
    timestamps = deque()
    sentiments = deque()
    start_generating = False
    for tweet in tweets.find({"timestamp": {"$gt": start, "$lt": end}}).sort("timestamp"):
        if "http" not in tweet["text"]:
            timestamps.append(tweet["timestamp"])
            sentiments.append(tweet["sentiment"])

            new_interval_beginning = helper.get_interval_beginning(tweet["timestamp"], interval) 
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning
                while len(timestamps) and timestamps[0] + window <= interval_beginning:
                    if not start_generating:
                        start_generating = True
                    timestamps.popleft()
                    sentiments.popleft()

                if start_generating and len(timestamps) >= min_data_points:
                    yield interval_beginning, np.average(sentiments)


def window_sentiments_with_price(interval, window, start=0, end=10000000000000, min_data_points=500):
    for timestamp, sentiment in window_sentiments(interval, window, start, end, min_data_points):
        price_entry = prices.find_one({"timestamp": timestamp})
        if price_entry != None:
            yield timestamp, sentiment, price_entry["price"]


