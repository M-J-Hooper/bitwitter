import helper
import generate
from keras.models import Sequential
from keras.layers import Dense
import numpy as np
import time

tweets = helper.get_mongodb_collection("tweets")

def train_sequential(interval, window, future, validation_ratio):
    print("Calculating data ranges")
    start = tweets.find().sort("timestamp")[0]["timestamp"]
    end = tweets.find().sort("timestamp", -1)[0]["timestamp"]
    training_end = helper.get_interval_beginning(end - validation_ratio*(end - start), interval)
    validation_start = training_end - window
    print("Training", helper.str_from_timestamp(start), "-", helper.str_from_timestamp(training_end))
    print("Validation", helper.str_from_timestamp(validation_start), "-", helper.str_from_timestamp(end))
    
    print("Initialising generators")
    training_generator = generate.window_vectors_for_training(interval, window, future, start, training_end)
    validation_generator = generate.window_vectors_for_training(interval, window, future, validation_start, end)

    print("Initialising model")
    #np.random.seed(13)
    model = Sequential()
    model.add(Dense(100, input_dim=100, kernel_initializer='normal', activation='relu'))
    model.add(Dense(100, kernel_initializer='normal', activation='relu'))
    
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy', y_true, y_pred])
    #model.add(Dense(1, activation='tanh'))
    #model.compile(loss='mse', optimizer='adam', metrics=[y_true,y_pred])
    
    model.summary()

    print("Training")
    steps_per_epoch = (training_end - start - window) // interval
    validation_steps = (end - validation_start - window) // interval
    model.fit_generator(training_generator, steps_per_epoch=steps_per_epoch, validation_data=validation_generator, validation_steps=validation_steps, epochs=10)

def y_true(y_true, y_pred):
    return y_true

def y_pred(y_true, y_pred):
    return y_pred

if __name__ == "__main__":
    minute = 60 * 1000
    hour = 60 * minute
    day = 24 * hour

    train_sequential(hour, 7*day, 6*hour, 0.3)
