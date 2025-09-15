import tensorflow as tf
from tensorflow.keras import layers, models


def build_cnn_lstm(input_shape, horizon: int = 1) -> tf.keras.Model:
    """
    Build a simple hybrid CNN + LSTM model for time series forecasting.
    input_shape: (lookback, num_features)
    horizon: number of steps to predict ahead
    """
    inp = layers.Input(shape=input_shape)

    # CNN part
    x = layers.Conv1D(filters=32, kernel_size=3, activation="relu")(inp)
    x = layers.Conv1D(filters=32, kernel_size=3, activation="relu")(x)
    x = layers.MaxPooling1D(pool_size=2)(x)

    # LSTM part
    x = layers.LSTM(64, return_sequences=False)(x)

    # Dense output
    x = layers.Dense(64, activation="relu")(x)
    out = layers.Dense(horizon)(x)

    model = models.Model(inputs=inp, outputs=out)
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model
