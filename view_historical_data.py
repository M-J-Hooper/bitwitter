import helper
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

price_data = helper.load_data("historical_prices")
price_data["timestamps"] = [int(ts) for ts in price_data["timestamps"]]
tweet_data = helper.load_data("historical_tweets")
nth = 10

interval = 60 * 1000
min_data_points = 500
interval_beginning = 0
timestamps = []
sentiments = []
window_sentiments = []
window_closing_timestamps = []
#window = 122520000
window = 160320000
stdevs = 0.598364873689
buy_stdevs = 1.0190376940114
sell_stdevs = -0.7340228396361

for i in range(len(tweet_data["timestamps"])):
	new_interval_beginning = helper.get_interval_beginning(tweet_data["timestamps"][i], interval) 
	if new_interval_beginning > interval_beginning:
		interval_beginning = new_interval_beginning
		if len(timestamps) > min_data_points:
			window_sentiment = np.average(sentiments)
			window_sentiments.append(window_sentiment)
			window_closing_timestamps.append(interval_beginning)

			while len(timestamps) and timestamps[0] + window < interval_beginning + interval:
				timestamps.pop(0)
				sentiments.pop(0)


	timestamps.append(int(tweet_data["timestamps"][i]))
	sentiments.append(tweet_data["sentiments"][i])

average = np.average(window_sentiments)     
stdev = np.std(window_sentiments)


fig = plt.figure()
ax = fig.add_subplot(111)
ax2 = ax.twinx()

for n in range(-1, 2):
	value = average + n*stdevs*stdev
	color = "blue" if n == 0 else "red"
	ax.axhline(y=value,xmin=0,xmax=1,c=color)

ax.axhline(y=average+buy_stdevs*stdev,xmin=0,xmax=1,c="green")
ax.axhline(y=average+sell_stdevs*stdev,xmin=0,xmax=1,c="green")

ax.plot(window_closing_timestamps[0::nth], window_sentiments[0::nth], "r")
ax2.plot(price_data["timestamps"][0::nth], price_data["prices"][0::nth])

plt.show()
