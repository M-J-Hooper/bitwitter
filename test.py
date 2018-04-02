import helper

tweets = helper.get_mongodb_collection("tweets")

def count_links():
    print("Counting links\n")
    total = 0
    links = 0
    for tweet in tweets.find():
        total += 1
        if "http" in tweet["text"]:
            links += 1
        
        if total % 100000 == 0:
            print("{0} links out of {1} total".format(links, total))

    print("\n{0} links out of {1} total".format(links, total))


if __name__ == "__main__":
    count_links()
