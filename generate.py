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
    new_interval_vectors = []
    new_interval_weights = []
    window_vector = np.zeros(shape=(model.vector_size))
    weight_sum = 0
    start_generating = False
    for tweet in tweets.find({"timestamp": {"$gt": start, "$lt": end}}).sort("timestamp"):
        if "http" not in tweet["text"]:
            timestamps.append(tweet["timestamp"])
            sentence = nlp.preprocess_text(tweet["text"])
            sentence_vectors = nlp.get_sentence_vectors(model, sentence)
            sentence_weights = nlp.get_sentence_weights(model, sentence)

            vectors.extend(sentence_vectors)
            weights.extend(sentence_weights)
            new_interval_vectors.extend(sentence_vectors)
            new_interval_weights.extend(sentence_weights)
            lengths.append(len(sentence_vectors))

            new_interval_beginning = helper.get_interval_beginning(tweet["timestamp"], interval)
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning

                subtract_vector = np.zeros(shape=(model.vector_size))
                subtract_weight = 0
                while len(timestamps) and timestamps[0] + window <= interval_beginning:
                    if not start_generating:
                        start_generating = True
                    timestamps.popleft()
                    length = lengths.popleft()
                    for i in range(length):
                        popped_weight = weights.popleft()
                        subtract_weight += popped_weight
                        subtract_vector += popped_weight * vectors.popleft()
                
                window_vector = (window_vector * weight_sum) - subtract_vector
                weight_sum -= subtract_weight
                for i in range(len(new_interval_weights)):
                    weight_sum += new_interval_weights[i]
                    window_vector += new_interval_weights[i] * new_interval_vectors[i]
                window_vector = window_vector / weight_sum
                new_interval_vectors = []
                new_interval_weights = []

                if start_generating and len(timestamps) >= min_data_points:
                    yield interval_beginning, window_vector


def window_vectors_with_price(interval, window, future, start=0, end=10000000000000, min_data_points=500):
    for timestamp, vector in window_vectors(interval, window, start, end, min_data_points):
        price_entry = prices.find_one({"timestamp": timestamp})
        if price_entry != None:
            yield timestamp, vector, price_entry["price"]


def window_vectors_for_training(interval, window, future, start=0, end=10000000000000, min_data_points=500):
    while(True):
        first = True
        past_prices = deque()
        window_vector_generator = window_vectors(interval, window, start, end, min_data_points)
        for timestamp, vector in window_vector_generator:
            price_entry_now = prices.find_one({"timestamp": timestamp})
            
            if first:
                i = len(vector)
                past_step = window / i
                while i > 0:
                    past = helper.get_interval_beginning(timestamp - (past_step * i), 60000)
                    past_price = prices.find_one({"timestamp": past})
                    if past_price != None:
                        past_prices.append(past_price["price"])
                    i -= 1
                first = False

            price_entry_future = prices.find_one({"timestamp": (timestamp + future)})
            if price_entry_now != None and price_entry_future != None:
                price_now = price_entry_now["price"]
                price_future = price_entry_future["price"]

                past_prices.pop()
                past_prices.append(price_now)

                #limit = 0.1
                #change = (price_now - price_future) / price_now
                #label = max(min(limit, change), -limit) / limit

                label = 1 if price_future > price_now else 0
                #print(helper.str_from_timestamp(timestamp), label)
                
                input_vector = np.array(list(vector) + list(past_prices))
                print(input_vector, input_vector.shape)
                yield input_vector, label


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


def cycle_batch_training(generators, batch_size):
    input_vectors = []
    labels = []
    while(True):
        for generator in generators:
            input_vector, label = next(generator)
            input_vectors.append(input_vector)
            labels.append(label)

            if len(labels) == batch_size:
                print(input_vectors)
                print(np.array(input_vectors), np.array(input_vectors).shape)
                yield np.array(input_vectors), np.array(labels)
                input_vectors = []
                labels = []

