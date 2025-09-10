
import tensorflow as tf
from tensorflow.keras import layers, optimizers

def scale_width(base_filters, alpha):
    return max(8, int(base_filters * alpha))  # Ensure at least 8 filters

def scale_depth(base_layers, beta):
    return max(1, int(base_layers * beta))  # Ensure at least 1 residual block

def scale_resolution(base_size, gamma):
    return min(224, max(112, int(base_size * gamma)))  # Keep within 112-224

def residual(input_tensor, filters, kernel_size=3, strides=1):
    shortcut = input_tensor
    
    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', strides=strides, activation='relu')(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', activation=None)(x)
    x = layers.BatchNormalization()(x)
    
    if input_tensor.shape[-1] != filters or strides > 1:
        shortcut = layers.Conv2D(filters, kernel_size=(1,1), padding='same', strides=strides)(input_tensor)
        shortcut = layers.BatchNormalization()(shortcut)
    
    x = layers.Add()([shortcut, x])
    x = layers.Activation('relu')(x)
    return x

def create_model(phi=1.0):
    alpha, beta, gamma = 1.2 ** phi, 1.1 ** phi, 1.15 ** phi
    input_size = scale_resolution(224, gamma)
    inputs = tf.keras.Input(shape=(input_size, input_size, 3))
    
    x = layers.RandomRotation(0.33)(inputs)
    x = layers.RandomFlip("horizontal")(x)
    x = layers.Conv2D(scale_width(64, alpha), 7, strides=2, padding='same', activation='relu')(x)
    
    for _ in range(scale_depth(3, beta)):
        x = residual(x, scale_width(64, alpha), strides=2 if _ == 0 else 1)
    for _ in range(scale_depth(4, beta)):
        x = residual(x, scale_width(128, alpha), strides=2 if _ == 0 else 1)
    for _ in range(scale_depth(6, beta)):
        x = residual(x, scale_width(256, alpha), strides=2 if _ == 0 else 1)
    for _ in range(scale_depth(3, beta)):
        x = residual(x, scale_width(512, alpha), strides=2 if _ == 0 else 1)
    
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
    return tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)

