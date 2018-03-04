import helper
import tweepy
import gdax
import time

conf = helper.get_config()
gdax_client = gdax.PublicClient(conf["api"]["gdax"]["url"])

def get_twitter_auth():
    secrets = conf["api"]["twitter"]["auth"]
    auth = tweepy.OAuthHandler(secrets["consumer_key"], secrets["consumer_secret"])
    auth.set_access_token(secrets["access_token"], secrets["access_token_secret"])
    return auth

def get_prices(request_beginning, request_end, interval, product):
    response = None
    first_request = True
    while response == None or "message" in response:
        print(response)
        if first_request == True:
            first_request = False
        else:
            time.sleep(1)
        response = request_gdax_prices(request_beginning, request_end, interval, product)
    return response

def request_gdax_prices(request_beginning, request_end, interval, product):
    iso_beginning = helper.iso_from_timestamp(request_beginning - interval)
    iso_end = helper.iso_from_timestamp(request_end)
    granularity = int(interval / 1000)
    
    print("Price request:", product, iso_beginning, iso_end, granularity)
    return gdax_client.get_product_historic_rates(product, iso_beginning, iso_end, granularity)





