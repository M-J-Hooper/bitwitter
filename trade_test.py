import helper
import process_historical_data as proc_hist

minute = 60*1000

params = helper.get_mongodb_collection("params")
param = params.find().sort("timestamp", -1)[0]
window = param["window"]
stdevs = param["stdevs"]

average, stdev, window_sentiments, window_closing_timestamps = proc_hist.process(minute, window, 500, False)
attempt = {"window": window, "average": average, "stdev": stdev, "stdevs": stdevs}
print(attempt)
attempt.update(proc_hist.trade(average, stdev, window_sentiments, window_closing_timestamps, 1.0, stdevs))
print(attempt)

