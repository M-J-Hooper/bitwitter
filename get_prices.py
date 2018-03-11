import helper
import api
from datetime import datetime

logger = helper.get_logger("get_prices")
tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")


def get_prices(interval, product, bulk=False):
    logger.info("Started getting prices")
    limit = 200 if bulk else 1

    last_price = prices.find().sort("timestamp", -1)[0]
    day = 1000 * 60 * 60 * 24
    beginning = helper.get_interval_beginning(last_price["timestamp"], interval) - 7*day

    last_tweet = tweets.find().sort("timestamp", -1)[0]
    end = helper.get_interval_beginning(last_tweet["timestamp"], interval)

    skipped_temp = 0
    skipped = 0
    failed = 0
    succeded = 0
    price_sum = 0
    volume_sum = 0
    request_timestamps = []
    for timestamp in range(beginning, end, interval):
        try:
            response = None
            price_data = prices.find_one({"timestamp": str(timestamp)})
            if price_data == None:
                skipped_temp = 0
                request_timestamps.append(timestamp)
                if len(request_timestamps) >= limit:
                    response = api.get_prices(request_timestamps[0], request_timestamps[-1], interval, product)

            else:
                if bulk and skipped_temp == 0 and len(request_timestamps) > 0:
                    response = api.get_prices(request_timestamps[0], request_timestamps[-1], interval, product)
                skipped_temp += 1
                skipped += 1
            
            if response != None:
                for i in range(len(response)):
                    response_timestamp = int(response[i][0]) * 1000
                    price = float(response[i][4])
                    volume = float(response[i][5])
                    store = {"timestamp": response_timestamp, "price": price, "volume": volume}
                    prices.insert(store)
                    
                    succeded += 1
                    price_sum += price
                    volume_sum += volume


                failed += len(request_timestamps) - len(response)
                request_timestamps = []
                print("Succeded:", succeded, "Skipped:", skipped, "Failed:", failed)

        except Exception as e:
            print("Exception:", e)
            failed += len(request_timestamps)
            request_timestamps = []
    
    price_avg = price_sum / succeded
    volume_avg = volume_sum / succeded
    logger.info("Finished getting {0} prices with {1} skipped, {2} failed, average volume of {3} and price of {4}".format(succeded, skipped, failed, volume_avg, price_avg))


if __name__ == "__main__":
    interval = 60 * 1000
    product = "BTC-EUR"
    try:
        get_prices(interval, product, bulk=True) #Bulk is broken, response is out of order
    except Exception as e:
        logger.exception("Error getting prices")
