import math
import gdax
import dateutil.parser as dp
import helper

prices = helper.get_mongodb_collection("prices")

class WebsocketClient(gdax.WebsocketClient):
    def on_open(self):
        print("Focus "+str(self.products))
        print("Connected to "+self.url)
        self.interval_beginning = 0
        self.interval = 60 * 1000

    def on_message(self, msg):
        try:
            if "type" in msg and msg["type"] == "match":
                timestamp =  helper.timestamp_from_datetime(dp.parse(msg["time"]))
                price = float(msg["price"])
                print(helper.str_from_timestamp(timestamp), ": Price", price)

                new_interval_beginning = int(math.floor(timestamp / float(self.interval))) * self.interval
                diff_interval = new_interval_beginning > self.interval_beginning
                if diff_interval:
                    if self.interval_beginning > 0:
                        store = {"timestamp": str(new_interval_beginning), "price": price}
                        prices.insert(store)
                        print(store)

                    self.interval_beginning = new_interval_beginning
        except Exception as e:
            print(e)

    def on_close(self):
        print("Finished")


gdax_client = WebsocketClient(products="BTC-EUR")
gdax_client.start()
