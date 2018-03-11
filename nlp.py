import helper
import re
from gensim.models import Word2Vec, KeyedVectors

logger = helper.get_logger("nlp")
tweets = helper.get_mongodb_collection("tweets")

conf = helper.get_config()
model_file = conf["word_embedding"]["model_file"]


def load_model():
    return KeyedVectors.load_word2vec_format(model_file, binary=False)

def save_model(model):
    model.wv.save_word2vec_format(model_file, binary=False)


class SentenceIterable(object):
    def __init__(self, include_links = False):
        self.include_links = include_links

    def __iter__(self):
        for tweet in tweets.find().sort("timestamp"):
            if self.include_links or "http" not in tweet["text"]:
                yield preprocess_text(tweet["text"]).split()


def generate_model():
    try:
        logger.info("Started generating embeddings")
        sentences = SentenceIterable()
        
        model = Word2Vec(sentences)

        save_model(model)
        logger.info("Finished generating embeddings with a vocabulary of {0} words".format(len(model.wv.vocab)))
    except Exception as e:
        logger.exception("Error generating embeddings")

def preprocess_text(text):
    #TODO: problems with underscores at start of words (USERNAME???)
    text = text.lower()
    
    text = re.sub(r"(?<=^|(?<=[^a-z0-9-_\.]))@([a-z]+[a-z0-9]+)", " USERNAME ", text)      #replace usernames with token
    text = re.sub(r"\b[\w]+@[\w]+\.[\w]+\b", " EMAIL ", text)                                       #replace usernames with token
    
    text = re.sub(r"\'", "", text)                                                                  #keep apostrophe words together
    text = re.sub(r"\b\d+\,\d+\.\d+\b", " BIG_FLOAT ", text)                                        #replace comma separated floats with token
    text = re.sub(r"\b\d+\.\d+\b", " FLOAT ", text)                                                 #replace floats with token
    text = re.sub(r"\b\d+\,\d+\b", " BIG_INTEGER ", text)                                           #replace comma separated integers with token
    text = re.sub(r"\b\d+\b", " INTEGER ", text)                                                    #replace integers with token
    text = re.sub(r"[^\w]", " ", text)                                                              #remove special characters

    return " ".join(text.strip().split())

def get_sentence_vectors(model, sentence):
    return [model[word] for word in sentence.split() if word in model.vocab]

def get_sentence_weights(model, sentence):
    return [zipf_weight(model, word) for word in sentence.split() if word in model.vocab]

def zipf_weight(model, word):
    count = model.vocab[word].count
    rank = len(model.vocab) + 1 - count
    return  rank / count


if __name__ == "__main__":
    generate_model()
