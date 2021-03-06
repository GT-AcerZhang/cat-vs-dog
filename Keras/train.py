#coding=utf-8
import os,glob,shutil,keras
import numpy as np
from keras.models import *
from keras.layers import *
from keras.applications import *
from keras.preprocessing.image import *
from keras.utils import plot_model
from keras.optimizers import SGD
from keras.preprocessing import image

num_classes=2
cls_list = ['cats', 'dogs']
IMAGE_SIZE    = (256, 256)
CROP_LENGTH   = 224

MODEL_WEIGHTS="model.h5"

import tensorflow as tf
from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.allow_growth=True
set_session(tf.Session(config=config))

def random_crop(img, random_crop_size):
    # Note: image_data_format is 'channel_last'
    assert img.shape[2] == 3
    height, width = img.shape[0], img.shape[1]
    dy, dx = random_crop_size
    x = np.random.randint(0, width - dx + 1)
    y = np.random.randint(0, height - dy + 1)
    return img[y:(y+dy), x:(x+dx), :]
def crop_generator(batches, crop_length):
    '''
    Take as input a Keras ImageGen (Iterator) and generate random
    crops from the image batches generated by the original iterator
    '''
    while True:
        batch_x, batch_y = next(batches)
        batch_crops = np.zeros((batch_x.shape[0], crop_length, crop_length, 3))
        for i in range(batch_x.shape[0]):
            batch_crops[i] = random_crop(batch_x[i], (crop_length, crop_length))
        yield (batch_crops, batch_y)

def simple_net():
    model=Sequential()
    model.add(Convolution2D(4,5,5,input_shape=(224,224,3)))
    model.add(Activation("relu"))
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Convolution2D(8,3,3))
    model.add(Activation("relu"))
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Flatten())
    model.add(Dense(128))
    model.add(Activation("relu"))
    #model.add(Dropout(0.5))
    model.add(Dense(num_classes))
    model.add(Activation("softmax"))
    return model

def get_model():    
    input_tensor = Input(shape=(224, 224, 3))
    #base_model = keras.applications.resnet50.ResNet50(input_tensor=input_tensor,weights='imagenet', include_top=False)
    #base_model =keras.applications.vgg19.VGG19(input_tensor=input_tensor,weights='imagenet', include_top=False)
    #base_model = InceptionResNetV2(input_shape=(229,229,3),weights='imagenet', include_top=False)
    base_model =keras.applications.mobilenet.MobileNet(input_shape=(224,224,3),weights='imagenet', include_top=False)
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(1024, activation='relu')(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=base_model.input, outputs=predictions)
    return model

def train():
    #model=simple_net()
    model=get_model()
    #for layer in model.layers[:25]:
        #layer.trainable = False
    sgd = SGD(lr=0.0001, decay=1e-6, momentum=0.9)
    #sgd=rmsprop'
    model.compile(optimizer=sgd,loss='categorical_crossentropy', metrics=['accuracy'])
    train_datagen=ImageDataGenerator(
                    preprocessing_function=keras.applications.resnet50.preprocess_input,
                    rotation_range=40,
                    width_shift_range=0.2,
                    height_shift_range=0.2,
                    shear_range=0.2,
                    zoom_range=0.2,
                    channel_shift_range=10,
                    horizontal_flip=True,
                    fill_mode='nearest')  
    train_generator=train_datagen.flow_from_directory("../data/train2",target_size=(224,224),batch_size=32)
    print(train_generator.class_indices)
    #json_string = model.to_json()
    #open('model.json','w').write(json_string)
    earlystop=keras.callbacks.EarlyStopping(monitor='val_loss', patience=20, verbose=1, mode='auto')
    checkpoints=keras.callbacks.ModelCheckpoint(MODEL_WEIGHTS, monitor='acc', save_best_only=True)
    tensorboard=keras.callbacks.TensorBoard(log_dir='logs', histogram_freq=0, write_graph=True, write_images=False, embeddings_freq=0,embeddings_layer_names=None, embeddings_metadata=None)
    callbacks = [earlystop,checkpoints,tensorboard]
    model.fit_generator(train_generator,callbacks = callbacks,samples_per_epoch=25000,nb_epoch=100)
    
    #model.save_weights(MODEL_WEIGHTS)
    model.save(MODEL_WEIGHTS)

def evaluate():
    #model = model_from_json(open('model.json').read())
    #model.load_weights(MODEL_WEIGHTS)
    model=load_model(MODEL_WEIGHTS)
    sgd = SGD(lr=0.0001, decay=1e-6, momentum=0.9)
    model.compile(optimizer=sgd,loss='categorical_crossentropy', metrics=['accuracy'])
    test_datagen=ImageDataGenerator(preprocessing_function=preprocess_input)
    validation_generator=test_datagen.flow_from_directory("../data/train2",target_size=(224,224),batch_size=50)
    score=model.evaluate_generator(validation_generator,5000)
    print(score[1])
    plot_model(model,to_file="model.png")

def test_one_image(imgpath="../data/train/cat.0.jpg"):
    net = load_model(MODEL_WEIGHTS)
    img=image.load_img(imgpath, target_size=(224,224))
    x = image.img_to_array(img)
    x = preprocess_input(x)
    x = np.expand_dims(x, axis=0)
    pred = net.predict(x)[0]
    top_inds = pred.argsort()[::-1][:]
    for i in top_inds:
        print('    {:.3f}  {}'.format(pred[i], cls_list[i]))

if __name__=="__main__":
    train()
    evaluate()
    test_one_image()