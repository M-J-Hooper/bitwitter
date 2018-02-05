import helper
import gdax
import time
from datetime import datetime

interval = 60 * 1000
product = "BTC-EUR"
gdax_client = gdax.PublicClient()

tweets = helper.get_mongodb_collection("tweets")
prices = helper.get_mongodb_collection("prices")

logger = helper.init_logger()

def make_request(request_beginning, request_end):
    iso_beginning = helper.iso_from_timestamp(request_beginning - interval)
    iso_end = helper.iso_from_timestamp(request_end)
    
    response = None
    first_request = True
    while response == None or "message" in response:
        if first_request == True:
            first_request = False
        else:
            time.sleep(1)
        response = gdax_client.get_product_historic_rates(product, iso_beginning, iso_end, granularity=60)
    return response 


def get_prices(bulk):
    logger.info("Started collecting prices")
    limit = 200 if bulk else 1

    first_tweet = tweets.find().sort("timestamp")[0]
    beginning = helper.get_interval_beginning(first_tweet["timestamp"], interval) + interval

    last_tweet = tweets.find().sort("timestamp", -1)[0]
    end = helper.get_interval_beginning(last_tweet["timestamp"], interval)

    skipped = 0
    skipped_total = 0
    failed = 0
    succeded = 0
    request_timestamps = []
    for timestamp in range(beginning, end, interval):
        try:
            response = None
            price_data = prices.find_one({"timestamp": str(timestamp)})
            if price_data == None:
                if skipped > 0:
                    skipped = 0
                
                request_timestamps.append(timestamp)
                if len(request_timestamps) >= limit:
                    response = make_request(request_timestamps[0], request_timestamps[-1])

            else:
                if bulk and skipped == 0 and len(request_timestamps) > 0:
                    response = make_request(request_timestamps[0], request_timestamps[-1])
                skipped += 1
                skipped_total += 1
            
            if response != None:
                for i in range(len(request_timestamps)):
                    store = {"timestamp": str(request_timestamps[i]), "price": float(response[i][4])}
                    prices.insert(store)
                    print("Stored missing price", response[i][4], "at", helper.str_from_timestamp(request_timestamps[i]))
                    succeded += 1
                request_timestamps = []

        except Exception as e:
            skipped = 0
            failed += 1
            request_timestamps = []
    
    logger.info("Finished collecting {0} prices with {1} skipped and {2} failures".format(succeded, skipped_total, failed))


get_prices(False) #Bulk is broken, response is out of order
