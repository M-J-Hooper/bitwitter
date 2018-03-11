import helper
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import nlp
from sklearn.manifold import TSNE
from random import randint
import cProfile
import generate

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")

def plot_timeline(interval, window, min_data_points=500):
    print("Calculating window stats")
    window_sentiments = []
    window_prices = []       
    for timestamp, sentiment, price in generate.window_sentiments_with_price(interval, window, 1518024388000):
        print(helper.str_from_timestamp(timestamp), price, sentiment)
        window_sentiments.append(sentiment)                    
        window_prices.append(price)                    

    print("Calculating min/max")
    max_s, min_s = max(window_sentiments), min(window_sentiments)
    max_p, min_p = max(window_prices), min(window_prices)
    print(min_s, max_s, min_p, max_p)
    diff = [(float(s - min_s)/float(max_s)) - (float(p - min_p)/float(max_p)) for s,p in zip(window_sentiments, window_prices)]

    print("Plotting")
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = ax1.twinx()
    ax3 = fig.add_subplot(2, 1, 2)
    ax3.axhline(y=0,xmin=0,xmax=1,c="g")
    
    linspace = np.linspace(0, 1, len(window_prices))
    ax1.plot(linspace, window_prices, "b")
    ax2.plot(linspace, window_sentiments, "r")
    ax3.plot(linspace, diff, "g")

    plt.show()

def plot_window_vectors(interval, window, use_tsne=False):
    print("Calculating window vectors")
    window_vectors = []
    for timestamp, vector in generate.window_vectors(interval, window):
        print(helper.str_from_timestamp(timestamp))
        window_vectors.append(vector)
    
    print("Plotting")
    pairs = False
    width = 4
    fig, axs = plt.subplots(width, width)
    axs = axs.ravel()
    linspace = np.linspace(0, 1, len(window_vectors))
    colors = cm.viridis(linspace)

    subplot_pairs = []
    max_i = len(window_vectors[0]) - 1
    for i in range(width**2):
        subplot_pairs.append([randint(0,max_i), randint(0,max_i)])

    first  = True
    for vector, c, l in zip(window_vectors, colors, linspace):
        for i in range(width**2):
            if first:
                axs[i].set_title("{0}, {1}".format(subplot_pairs[i][0], subplot_pairs[i][1]))
            if pairs:
                axs[i].scatter(vector[subplot_pairs[i][0]], vector[subplot_pairs[i][1]], color=c)
            else:
                axs[i].scatter(l, vector[subplot_pairs[i][1]], color=c)
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

    plot_timeline(3*hour, 3*day)
    #plot_window_vectors(day, 7*day)
    #plot_word_embedding(True, 0.01)
    
    if profile:
        pr.disable()
        pr.print_stats(sort='time')
