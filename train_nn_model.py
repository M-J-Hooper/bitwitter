import helper
import generate

def train_sequential(interval, window, future):
    for vector, change in generate.window_vectors_with_future_price_change(interval, window, future):
        print(vector[0], change)


if __name__ == "__main__":
    minute = 60 * 1000
    hour = 60 * minute
    day = 24 * hour

    train_sequential(hour, 3*day, hour)
