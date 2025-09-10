
import tensorflow as tf
from tensorflow.keras import layers, optimizers, regularizers

def residual(input_tensor, filters, kernel_size=3, strides=1):
    shortcut = input_tensor

    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', strides=strides, activation='relu')(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', activation=None)(x)  # No activation here
    x = layers.BatchNormalization()(x)

    if input_tensor.shape[-1] != filters or strides > 1:
        shortcut = layers.Conv2D(filters, kernel_size=(1,1), padding='same', strides=strides)(input_tensor)
        shortcut = layers.BatchNormalization()(shortcut)

    x = layers.Add()([shortcut, x])
    x = layers.Activation('relu')(x)
    return x



def create_model():
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = layers.RandomRotation(0.33)(inputs)
    x = layers.RandomFlip("horizontal")(x)
    x = layers.Conv2D(64, 7, strides=2, padding='same', activation='relu')(x)
    x = residual(x, 64, strides=2)  # Strided downsampling
    x = residual(x, 64)  # No unintended downsampling
    x = residual(x, 64)

    x = residual(x, 128, strides=2)  # Strided downsampling
    x = residual(x, 128)
    x = residual(x, 128)
    x = residual(x, 128)

    #x = residual(x, 256, strides=2)  # Strided downsampling
    #x = residual(x, 256)
    #x = residual(x, 256)
    #x = residual(x, 256)
    #x = residual(x, 256)
    #x = residual(x, 256)

    #x = residual(x, 512, strides=2)  # Strided downsampling
    #x = residual(x, 512)
    #x = residual(x, 512)

    x = layers.GlobalAveragePooling2D()(x)
    outputs = layers.Dense(14, activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)
    adam_opt = optimizers.Adam(learning_rate=0.0005)
    model.compile(optimizer=adam_opt,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    model.summary()
    return model


def callbacks():
    callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
    return callback
