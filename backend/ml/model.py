import tensorflow as tf
from tensorflow.keras import layers, models


def build_cnn_lstm(input_shape, horizon: int = 1, filters: int = 32, kernel_size: int = 5, lstm_units: int = 64, dropout: float = 0.2):
inp = layers.Input(shape=input_shape)
x = layers.Conv1D(filters, kernel_size, padding="causal", activation="relu")(inp)
x = layers.Conv1D(filters, kernel_size, padding="causal", activation="relu")(x)
x = layers.MaxPooling1D(2)(x)
x = layers.LSTM(lstm_units)(x)
x = layers.Dropout(dropout)(x)
out = layers.Dense(horizon)(x)
model = models.Model(inp, out)
model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
return model