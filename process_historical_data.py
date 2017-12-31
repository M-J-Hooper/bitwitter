import statistics
import helper

tweets = helper.get_mongodb_collection("tweets")

def process(interval, window, stdevs, min_data_points):
    timestamps = []
    sentiments = []
    interval_beginning = 0
    window_sentiments = []
    window_closing_timestamps = []
    
    for tweet in tweets.find().sort("timestamp"):
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
                print("Window "+start+" - "+end+", Sentiment "+str(window_sentiment))

                while len(timestamps) and timestamps[0] + window < interval_beginning + interval:
                    timestamps.pop(0)
                    sentiments.pop(0)

            else:
                print(str(len(timestamps))+" data points is insufficient")
        
        timestamps.append(int(tweet["timestamp"]))
        sentiments.append(tweet["sentiment"])

    average = statistics.mean(window_sentiments)
    stdev = statistics.stdev(window_sentiments)
    print("\nAverage "+str(average)+", Standard deviation "+str(stdev)+"\n")
    
    starting_coins = 1.0
    buying = False
    money = 0.0
    coins = starting_coins * 1.0
    price = 15000.0
    fee = 0.9975
    for i in range(len(window_sentiments)):
        sentiment = window_sentiments[i]
        closing_timestamp = window_closing_timestamps[i]
        
        if buying:
            if sentiment > average + stdevs * stdev:
                buying = False
                coins = money * fee / price
                print("Buying "+str(coins)+" at "+str(price)+" due to a "+str(sentiment)+" at "+helper.str_from_timestamp(closing_timestamp))
        
        if not buying:
            if sentiment < average - stdevs * stdev:
                buying = True
                money = coins * fee * price
                print("Selling "+str(coins)+" at "+str(price)+" due to a "+str(sentiment)+" at "+helper.str_from_timestamp(closing_timestamp))
    
    percentage_change = (coins - starting_coins) * 100 / starting_coins
    print("\nEnds with "+str(coins)+", Percentage change "+str(percentage_change))


minute = 1000 * 60
process(minute, 30 * minute, 2, 1000)


