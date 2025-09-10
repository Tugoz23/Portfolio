
import tensorflow as tf
from tensorflow.keras import layers, optimizers, regularizers

def residual_se_block(input_tensor, filters, kernel_size=3, se_reduction_ratio=8):
    """
    Residual block with Squeeze-and-Excitation (SE) mechanism.
    """
    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', activation='relu',kernel_regularizer=regularizers.l2(0.01))(input_tensor)
    x = layers.dropout = layers.Dropout(0.1)(x)
    x = layers.Conv2D(filters, kernel_size=kernel_size, padding='same', activation='relu',kernel_regularizer=regularizers.l2(0.01))(x)
    x = layers.dropout = layers.Dropout(0.1)(x)
    #x = se_block(x, reduction_ratio=se_reduction_ratio)
    
    if input_tensor.shape[-1] != filters: 
        input_tensor = layers.Conv2D(filters, kernel_size=(1, 1), padding='same')(input_tensor)
    
    x = layers.Add()([input_tensor, x])
    return x

def se_block(input_tensor, reduction_ratio=8):
    channels = input_tensor.shape[-1]
    se = layers.GlobalAveragePooling2D()(input_tensor) 
    se = layers.Dense(channels // reduction_ratio, activation='relu')(se)
    se = layers.Dense(channels, activation='sigmoid')(se) 
    se = layers.Reshape([1, 1, channels])(se)
    return layers.Multiply()([input_tensor, se]) 

def create_model():
    inputs = tf.keras.Input(shape=(224, 224, 3))

    x = layers.RandomRotation(0.33)(inputs)
    x = layers.RandomFlip("horizontal")(x)

    x = layers.Conv2D(filters=32, kernel_size=(3, 3), activation='relu')(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Conv2D(filters=32, kernel_size=(3, 3), activation='relu')(x)  
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Conv2D(filters=64, kernel_size=(3, 3), activation='relu')(x) 
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Conv2D(filters=64, kernel_size=(3, 3), activation='relu')(x)  
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Conv2D(filters=128, kernel_size=(3, 3), activation='relu')(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Conv2D(filters=128, kernel_size=(3, 3), activation='relu')(x)
    x = layers.GlobalAveragePooling2D()(x)

    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dense(64, activation='relu')(x)
    outputs = layers.Dense(14, activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)

    adam_opt = optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=adam_opt,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    model.summary()
    return model

def callbacks():
    callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)

    return callback

create_model()