import math
import gdax
import dateutil.parser as dp
import helper
import time
from datetime import datetime

prices = helper.get_mongodb_collection("prices")

class WebsocketClient(gdax.WebsocketClient):
    def on_open(self):
        print("Focus "+str(self.products))
        print("Connected to "+self.url)
        self.interval_beginning = 0
        self.interval = 60 * 1000
        self.last_message = 0

    def on_message(self, msg):
        try:
            if "type" in msg and msg["type"] == "match":
                timestamp =  helper.timestamp_from_datetime(dp.parse(msg["time"]))
                self.last_message = timestamp
                
                price = float(msg["price"])
                print(helper.str_from_timestamp(timestamp), ": Price", price)

                new_interval_beginning = helper.get_interval_beginning(timestamp, self.interval)
                if new_interval_beginning > self.interval_beginning:
                    if self.interval_beginning > 0:
                        store = {"timestamp": str(new_interval_beginning), "price": price}
                        prices.insert(store)
                        print(store)

                    self.interval_beginning = new_interval_beginning
        except Exception as e:
            print("Error:", e)

    def on_close(self):
        print("Client closed")

gdax_client = WebsocketClient(products="BTC-EUR")
gdax_client.start()

restart_threshold = 1000 * 30
while(True):
    try:
        if gdax_client.last_message > 0 and helper.timestamp_from_datetime(datetime.now()) - restart_threshold > gdax_client.last_message:
            raise Exception("Inactive client")
        else:
            time.sleep(1)
    except Exception as e:
        print("Restarting client")
        print(e)
        gdax_client.close()
        gdax_client.start()
