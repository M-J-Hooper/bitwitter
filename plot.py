import helper
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import nlp
from sklearn.manifold import TSNE
from collections import deque
from random import randint
import time
import cProfile

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")

def plot_timeline(interval, window, min_data_points=500):
    print("Calculating window stats")
    interval_beginning = 0
    timestamps = []
    sentiments = []
    window_sentiments = []
    window_closing_timestamps = []
    window_closing_prices = []
    for tweet in tweets.find().sort("timestamp"):
        if "http" not in tweet["text"]:
            timestamps.append(int(tweet["timestamp"]))
            sentiments.append(tweet["sentiment"])

            new_interval_beginning = helper.get_interval_beginning(int(tweet["timestamp"]), interval) 
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning
                if len(timestamps) >= min_data_points:
                    while len(timestamps) and timestamps[0] + window < interval_beginning:
                        timestamps.pop(0)
                        sentiments.pop(0)

                    price_data = prices.find_one({"timestamp": str(interval_beginning)})
                    if price_data != None:
                        window_sentiment = np.average(sentiments)

                        if window_sentiment:
                            window_sentiments.append(window_sentiment)
                            window_closing_timestamps.append(interval_beginning)
                            window_closing_prices.append(price_data["price"])
                            print(helper.str_from_timestamp(window_closing_timestamps[-1]), window_closing_timestamps[-1], window_closing_prices[-1], window_sentiments[-1])
                        else:
                            print("Weird average sentiment?", window_sentiment)

    average = np.average(window_sentiments)     
    stdev = np.std(window_sentiments)

    print("Calculating min/max")
    max_s, min_s = max(window_sentiments), min(window_sentiments)
    max_p, min_p = max(window_closing_prices), min(window_closing_prices)
    print(min_s, max_s, min_p, max_p)
    diff = [(float(s - min_s)/float(max_s)) - (float(p - min_p)/float(max_p)) for s,p in zip(window_sentiments, window_closing_prices)]

    print("Plotting")
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = ax1.twinx()
    ax3 = fig.add_subplot(2, 1, 2)
    ax3.axhline(y=0,xmin=0,xmax=1,c="g")

    ax1.plot(window_closing_timestamps, window_closing_prices, "b")
    ax2.plot(window_closing_timestamps, window_sentiments, "r")
    ax3.plot(window_closing_timestamps, diff, "g")

    plt.show()

def plot_window_vectors(interval, window, min_data_points=500, use_tsne=False):
    print("Loading model")
    model = nlp.load_model()

    print("Calculating window vectors")
    interval_beginning = 0
    timestamps = deque()
    lengths = deque()
    vectors = deque()
    weights = deque()
    window_vectors = deque()
    start_recording = False
    for tweet in tweets.find().sort("timestamp"):
        if "http" not in tweet["text"]:
            timestamps.append(int(tweet["timestamp"]))
            sentence = nlp.preprocess_text(tweet["text"])
            sentence_vectors = nlp.get_sentence_vectors(model, sentence)
            sentence_weights = nlp.get_sentence_weights(model, sentence)

            vectors.extend(sentence_vectors)
            weights.extend(sentence_weights)
            lengths.append(len(sentence_vectors))

            new_interval_beginning = helper.get_interval_beginning(int(tweet["timestamp"]), interval)
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning
                if len(timestamps) >= min_data_points:
                    while len(timestamps) and timestamps[0] + window < interval_beginning:
                        if not start_recording:
                            start_recording = True
                        timestamps.popleft()
                        length = lengths.popleft()
                        for i in range(length):
                            vectors.popleft()
                            weights.popleft()
                    
                    if start_recording:
                        window_vectors.append(np.average(vectors, axis=0, weights=weights))
                        print(helper.str_from_timestamp(interval_beginning), window_vectors[-1][0], window_vectors[-1][1])
    
    print("Plotting")
    width = 4
    fig, axs = plt.subplots(width, width)
    axs = axs.ravel()
    colors = cm.viridis(np.linspace(0, 1, len(window_vectors)))

    subplot_pairs = []
    max_i = len(vectors[0]) - 1
    for i in range(width**2):
        subplot_pairs.append([randint(0,max_i), randint(0,max_i)])

    first  = True
    for vector, c in zip(window_vectors, colors):
        for i in range(width**2):
            if first:
                axs[i].set_title("{0}, {1}".format(subplot_pairs[i][0], subplot_pairs[i][1]))
            axs[i].scatter(vector[subplot_pairs[i][0]], vector[subplot_pairs[i][1]], color=c)
        if first:
            first = False

    plt.show()
    
def plot_word_embedding(use_tsne=False, sample=1.0):
    print("Processing model")
    model = nlp.load_model()
    words = list(model.vocab)
    
    sample_size = int(len(words) * sample)
    words = np.random.choice(words, sample_size)
    
    vectors = model[words]
    
    print("Converting to 2D")
    if use_tsne:
        tsne = TSNE(n_components=2)
        vectors = tsne.fit_transform(vectors)
    else:
        vectors = [[vector[0],vector[1]] for vector in vectors]

    print("Plotting")
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    for label, vector in zip(words, vectors):
        x, y = vector[0], vector[1]
        plt.scatter(x, y)
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')

    plt.show()
if __name__ == "__main__":
    profile = False
    minute = 60 * 1000
    hour = 60 * minute
    day = 24 * hour
    
    pr = cProfile.Profile()
    if profile:
        pr.enable()

    #plot_timeline(10*minute, 3*day)
    plot_window_vectors(day, 3*day)
    #plot_word_embedding(True, 0.01)
    
    if profile:
        pr.disable()
        pr.print_stats(sort='time')
