import helper
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

print("Loading pickled data")
price_data = helper.load_data("prices")
price_data["timestamps"] = [int(ts) for ts in price_data["timestamps"]]
tweet_data = helper.load_data("tweets")
tweet_data["timestamps"] = [int(ts) for ts in tweet_data["timestamps"]]

nth = 10

interval = 60 * 1000
min_data_points = 500
interval_beginning = 0
timestamps = []
sentiments = []
window_sentiments = []
window_closing_timestamps = []
window_closing_prices = []
price_i = 0
price_timestamp = 0

#window = 122520000
window = 100000000
stdevs = 0.598364873689
buy_stdevs = 1.0190376940114
sell_stdevs = -0.7340228396361

print("Calculating window stats")
for i in range(len(tweet_data["timestamps"])):
    timestamps.append(tweet_data["timestamps"][i])
    sentiments.append(tweet_data["sentiments"][i])

    new_interval_beginning = helper.get_interval_beginning(tweet_data["timestamps"][i], interval) 
    if new_interval_beginning > interval_beginning:
        interval_beginning = new_interval_beginning
        if len(timestamps) > min_data_points:
            while len(timestamps) and timestamps[0] + window < interval_beginning:
                timestamps.pop(0)
                sentiments.pop(0)

            while price_timestamp < interval_beginning and price_i + 1 < len(price_data["prices"]):
                price_i += 1
                price_timestamp = price_data["timestamps"][price_i]

            if price_timestamp == interval_beginning:
                window_sentiment = np.average(sentiments)
                if window_sentiment:
                    window_sentiments.append(window_sentiment)
                    window_closing_timestamps.append(interval_beginning)
                    window_closing_prices.append(price_data["prices"][price_i])
                else:
                    print(window_sentiment)

average = np.average(window_sentiments)     
stdev = np.std(window_sentiments)

print("Calculating min/max")
max_s, min_s = max(window_sentiments), min(window_sentiments)
max_p, min_p = max(window_closing_prices), min(window_closing_prices)
print(min_s, max_s, min_p, max_p)
diff = [(float(s - min_s)/float(max_s)) - (float(p - min_p)/float(max_p)) for s,p in zip(window_sentiments, window_closing_prices)]

print("Plotting")
fig = plt.figure()
ax = fig.add_subplot(2, 1, 1)
ax2 = ax.twinx()
ax3 = fig.add_subplot(2, 1, 2)

#for n in range(-1, 2):
#	value = average + n*stdevs*stdev
#	color = "blue" if n == 0 else "red"
#	ax.axhline(y=value,xmin=0,xmax=1,c=color)

#ax.axhline(y=average+buy_stdevs*stdev,xmin=0,xmax=1,c="green")
#ax2.axhline(y=average+sell_stdevs*stdev,xmin=0,xmax=1,c="green")

ax3.axhline(y=0,xmin=0,xmax=1,c="g")

ax.plot(window_closing_timestamps[0::nth], window_closing_prices[0::nth], "b")
ax2.plot(window_closing_timestamps[0::nth], window_sentiments[0::nth], "r")
ax3.plot(window_closing_timestamps[0::nth], diff[0::nth], "g")

plt.show()
