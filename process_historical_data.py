import statistics
import helper

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")

def process(interval, window, min_data_points, include_links):
    timestamps = []
    sentiments = []
    interval_beginning = 0
    window_sentiments = []
    window_closing_timestamps = []
    
    for tweet in tweets.find().sort("timestamp"):
        if include_links or "http" not in tweet["text"]:
            new_interval_beginning = helper.get_interval_beginning(tweet["timestamp"], interval) 
            diff_interval = new_interval_beginning > interval_beginning
            if diff_interval:
                interval_beginning = new_interval_beginning
                if len(timestamps) > min_data_points:
                    window_sentiment = statistics.mean(sentiments)
                    window_sentiments.append(window_sentiment)
                    window_closing_timestamps.append(interval_beginning)

                    start = helper.str_from_timestamp(timestamps[0])
                    end = helper.str_from_timestamp(timestamps[-1])
                    #print("Window "+start+" - "+end+", Average sentiment "+str(window_sentiment))

                    while len(timestamps) and timestamps[0] + window < interval_beginning + interval:
                        timestamps.pop(0)
                        sentiments.pop(0)

                #else:
                    #print(str(len(timestamps))+" data points is insufficient")
            
            timestamps.append(int(tweet["timestamp"]))
            sentiments.append(tweet["sentiment"])

    average = statistics.mean(window_sentiments) #overcounting due to sliding window????
    stdev = statistics.stdev(window_sentiments)
    
    #print("\nAverage sentiment "+str(average)+", Standard deviation "+str(stdev)+"\n")
    return average, stdev, window_sentiments, window_closing_timestamps

def trade(average, stdev, window_sentiment, window_closing_timestamps, stdevs, delay, starting_coins):
    buying = False
    money = 0.0
    coins = starting_coins * 1.0
    fee = 0.9975
    num_trades = 0
    for i in range(len(window_sentiments)):
        sentiment = window_sentiments[i]
        closing_timestamp = window_closing_timestamps[i]
        trade_timestamp = closing_timestamp + delay
        price_data = prices.find_one({"timestamp": str(trade_timestamp)})
        if price_data != None:
            price = price_data["price"]
            if buying:
                if sentiment > average + stdevs * stdev:
                    buying = False
                    coins = money * fee / price
                    num_trades += 1
                    #print("Buying "+str(coins)+" at "+str(price)+" due to a "+str(sentiment)+" at "+helper.str_from_timestamp(trade_timestamp))
            
            if not buying:
                if sentiment < average - stdevs * stdev:
                    buying = True
                    money = coins * fee * price
                    num_trades += 1
                    #print("Selling "+str(coins)+" at "+str(price)+" due to a "+str(sentiment)+" at "+helper.str_from_timestamp(trade_timestamp))
        #else:
            #print("Price not available for "+str(closing_timestamp))

    percentage_change = (coins - starting_coins) * 100 / starting_coins
    return coins, percentage_change, num_trades

minute = 1000 * 60
hour = 60 * minute


results = []
for window in range(5*minute, 2*hour, 5*minute):
    average, stdev, window_sentiments, window_closing_timestamps = process(minute, window, 100, False)
    for stdevs in helper.frange(0.6, 4.6, 0.2):
        for delay in range(0, 2*hour, 5*minute):
            coins, percentage_change, num_trades = trade(average, stdev, window_sentiments, window_closing_timestamps, stdevs, delay, 1.0)
            result = {"window": window, "stdevs": stdevs, "delay": delay, "coins": coins, "percentage_change": percentage_change, "num_trades": num_trades}
            if result["percentage_change"] > 15:
                results.append(result)
            print(result)

            #print("Window "+str(window)+", Standard deviations "+str(stdevs)+", Delay "+str(delay))
            #print("Finished at "+str(coins)+"BTC with a percentage change of "+str(percentage_change)+" after "+str(num_trades)+" trades")

print("\nResults:")
for result in results:
    print(result)
