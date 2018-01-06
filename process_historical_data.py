import helper
from datetime import datetime
import time
import numpy as np

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
            if new_interval_beginning > interval_beginning:
                interval_beginning = new_interval_beginning
                if len(timestamps) > min_data_points:
                    window_sentiment = np.average(sentiments)
                    window_sentiments.append(window_sentiment)
                    window_closing_timestamps.append(interval_beginning)

                    start = helper.str_from_timestamp(timestamps[0])
                    end = helper.str_from_timestamp(timestamps[-1])
                    #print("Window "+start+" - "+end+", Average sentiment "+str(window_sentiment))

                    while len(timestamps) and timestamps[0] + window < interval_beginning + interval:
                        timestamps.pop(0)
                        sentiments.pop(0)

            
            timestamps.append(int(tweet["timestamp"]))
            sentiments.append(tweet["sentiment"])

    average = np.average(window_sentiments)     
    stdev = np.std(window_sentiments)
    return average, stdev, window_sentiments, window_closing_timestamps

def trade(average, stdev, window_sentiments, window_closing_timestamps, stdevs, starting_coins):
    buying = False
    money = 0.0
    coins = starting_coins * 1.0
    fee = 0.9975
    trades = 0
    for i in range(len(window_sentiments)):
        sentiment = window_sentiments[i]
        closing_timestamp = window_closing_timestamps[i]
        trade_timestamp = closing_timestamp #+ delay
        price_data = prices.find_one({"timestamp": str(trade_timestamp)})
        if price_data != None:
            price = price_data["price"]
            if buying:
                if sentiment > average + stdevs * stdev:
                    buying = False
                    coins = money * fee / price
                    trades += 1
            
            if not buying:
                if sentiment < average - stdevs * stdev:
                    buying = True
                    money = coins * fee * price
                    trades += 1

    change = (coins - starting_coins) * 100 / starting_coins
    return {"change": change, "trades": trades}
minute = 1000 * 60
hour = 60 * minute

param_intervals = 5
min_params = {"window": 5*minute, "stdevs": 0.5}#, "delay": 0}
max_params = {"window": 45*minute, "stdevs": 3.5}#, "delay": 20*minute}

attempts = [0,0]
attempt_batch = 0
while len(attempts) > 1:
    attempts = []
    attempt_batch += 1
    print("\nAttempt batch "+str(attempt_batch)+" from "+str(min_params)+" to "+str(max_params))
    attempt_start_time = time.time()
    for window in helper.param_range("window", min_params, max_params, param_intervals):
        window = helper.get_interval_beginning(window, minute)
        average, stdev, window_sentiments, window_closing_timestamps = process(minute, window, 50, False)
        print("Window "+str(window)+", Average "+str(average)+", Stdev "+str(stdev))
        
        start_time = time.time()
        for stdevs in helper.param_range("stdevs", min_params, max_params, param_intervals):
            attempt = {"window": window, "stdevs": stdevs, "average": average, "stdev": stdev, "stdevs": stdevs}#, "delay": delay}
            attempt.update(trade(average, stdev, window_sentiments, window_closing_timestamps, stdevs, 1.0))
            
            attempts.append(attempt)
            print(attempt)

            #print("Window "+str(window)+", Standard deviations "+str(stdevs)+", Delay "+str(delay))
            #print("Finished at "+str(coins)+"BTC with a percentage change of "+str(percentage_change)+" after "+str(num_trades)+" trades")
        print("Time taken "+str(time.time() - start_time)+" at "+str(datetime.now()))

    if len(attempts) > 1:
        changes = [attempt["change"] for attempt in attempts]
        average = np.average(changes)
        print("Average over all", average)
        stdev = np.std(changes)

        if stdev > 0:
            print("\nTop attempts") 
            top_attempts = []
            for attempt in attempts:
                if attempt["change"] >= average:
                    top_attempts.append(attempt)
                    print(attempt)
            attempts = list(top_attempts)
            #change_argmax = np.argmax([attempt["change"] for attempt in attempts])
            changes = [attempt["change"] for attempt in attempts]

            for key in min_params.keys():
                attempts_key = [attempt[key] for attempt in attempts]
                stdev = np.std(attempts_key)
                centre = np.average(attempts_key, weights=changes)
                print("Key", key, "Centre", centre)
                #centre = attempts[change_argmax][key] 
                min_params[key] = centre - stdev
                max_params[key] = centre + stdev
        else:
            attempts = [attempts[0]]

    print("Attempt time taken "+str(time.time() - attempt_start_time)+" at "+str(datetime.now()))


print("\nBest attempt")
store = attempts[0]
store["timestamp"] = str(helper.timestamp_from_datetime(datetime.now()))

params = helper.get_mongodb_collection("params")
params.insert(store)
print(store)




