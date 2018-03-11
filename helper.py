import json
import math
import tweepy
import decimal
from pymongo import MongoClient
from datetime import datetime
import logging

def get_config():
    with open("conf.json") as conf_json:
        conf = json.load(conf_json)
    return conf

def get_logger(name):
    conf = get_config()
    filename = conf["logging"]["file"]
    formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(module)s : %(message)s", "%Y-%m-%d %H:%M:%S")
    
    fh = logging.FileHandler(filename)
    fh.setFormatter(formatter)
   
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

def get_mongodb_collection(name):
    conf = get_config()
    connection_str = "mongodb://" + conf["mongo"]["host"] + "/" + conf["mongo"]["db"]
    client = MongoClient(connection_str)
    db = client[conf["mongo"]["db"]]
    return db[name]

def str_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000.0).strftime("%Y-%m-%d %H:%M:%S")

def iso_from_timestamp(timestamp):
    ms = str(timestamp)[-3:] + "000Z"
    return datetime.fromtimestamp(timestamp / 1000.0).strftime("%Y-%m-%dT%H:%M:%S.") + ms

def timestamp_from_datetime(dt):
    return int(float(dt.strftime("%s.%f")) * 1000)

def get_interval_beginning(timestamp, interval):
    return int(math.floor(timestamp / float(interval))) * interval

