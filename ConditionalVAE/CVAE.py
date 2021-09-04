# -*- coding: utf-8 -*-
"""Untitled22.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wX-GIoYhqTa2JQNBYCcKvGhsw49jyzF6

Path for Dataset and Pretrained Model.
"""

!git clone https://github.com/Harvard-IACS/2019-computefest.git

import os
os.chdir("/content/2019-computefest/Wednesday/auto_encoder")

# Commented out IPython magic to ensure Python compatibility.
import keras
from keras import Model
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Concatenate, Reshape, Dense, Lambda, Flatten
from keras import backend as K

import warnings
warnings.filterwarnings('ignore')
import numpy as np
import glob
import skimage
import skimage.transform
import skimage.io
import PIL
import numpy as np
import os
from IPython.display import clear_output
import pandas as pd
import matplotlib.pyplot as plt
# %matplotlib inline
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import imageio
import utils

"""VAE encoder-decoder architecture"""

def define_encoder_block(x, num_filters):  
    """
    Todo: Define two sequential 2D convolutional layers (Conv2D) with the following properties:
          - num_filters many filters
          - kernel_size 3
          - activation "relu"
          - padding "same"
          - kernel_initializer "he_normal"
          Also define a 2D max pooling layer (MaxPooling2D) (you can keep default arguments).
    """
    x = Conv2D(num_filters, 3, activation='relu', padding='same', kernel_initializer='he_normal')(x)
    x = Conv2D(num_filters, 3, activation='relu', padding='same', kernel_initializer='he_normal')(x)
    x = MaxPooling2D()(x)
    return x

def define_decoder_block(x, num_filters):
    """
    Todo: Define one 2D upsampling layer (UpSampling2D) (you can keep default arguments).
          Also, define two sequential 2D convolutional layers (Conv2D) with the following properties:
          - num_filters many filters
          - kernel_size 3
          - activation "relu"
          - padding "same"
          - kernel_initializer "he_normal"
    """
    x = UpSampling2D()(x)
    x = Conv2D(num_filters, 3, activation='relu', padding = 'same', kernel_initializer = 'he_normal')(x)
    x = Conv2D(num_filters, 3, activation='relu', padding = 'same', kernel_initializer = 'he_normal')(x)
    return x

def define_net(variational, height, width, batch_size, latent_dim, conditioning_dim=0,
               start_filters=8):
    """Defines a (variational) encoder-decoder architecture.
    
    Args:
        variational: Whether a variational autoencoder should be defined.
        height: The height of the image input and output.
        width: The width of the image input and output.
        batch_size: The batchsize that is used during training. Must also be used for inference on the encoder side.
        latent_dim: The dimension of the latent space.
        conditioning_dim: The dimension of the space of variables to condition on. Can be zero for an unconditional VAE.
        start_filters: The number of filters to start from. Multiples of this value are used across the network. Can be used
            to change model capacity.
        
    Returns:
        Tuple of keras models for full VAE, encoder part and decoder part only.
    """
    
    # Prepare the inputs.
    inputs = Input((height, width, 3))
    if conditioning_dim > 0:
        # Define conditional VAE. Note that this is usually not the preferred way
        # of incorporating the conditioning information in the encoder.
        condition = Input([conditioning_dim])
        condition_up = Dense(height * width)(condition)
        condition_up = Reshape([height, width, 1])(condition_up)
        inputs_new = Concatenate(axis=3)([inputs, condition_up])
    else:
        inputs_new = inputs
    
    # Define the encoder.
    eblock1 = define_encoder_block(inputs_new, start_filters)
    eblock2 = define_encoder_block(eblock1, start_filters*2)
    eblock3 = define_encoder_block(eblock2, start_filters*4)
    eblock4 = define_encoder_block(eblock3, start_filters*8)
    _, *shape_spatial = eblock4.get_shape().as_list()
    eblock4_flat = Flatten()(eblock4)
    
    if not variational:
        z = Dense(latent_dim)(eblock4_flat)
    else:
        # Perform the sampling.
        def sampling(args):
            """Samples latent variable from a normal distribution using the given parameters."""
            z_mean, z_log_sigma = args
            epsilon = K.random_normal(shape=(batch_size, latent_dim), mean=0., stddev=1.)
            return z_mean + K.exp(z_log_sigma) * epsilon
        
        z_mean = Dense(latent_dim)(eblock4_flat)
        z_log_sigma = Dense(latent_dim)(eblock4_flat)
        z = Lambda(sampling, output_shape=(latent_dim,))([z_mean, z_log_sigma])
    
    if conditioning_dim > 0:
        z_ext = Concatenate()([z, condition])

    # Define the decoder.
    inputs_embedding = Input([latent_dim + conditioning_dim])
    embedding = Dense(np.prod(shape_spatial), activation='relu')(inputs_embedding)
    embedding = Reshape(eblock4.shape.as_list()[1:])(embedding)
    
    dblock1 = define_decoder_block(embedding, start_filters*8)
    dblock2 = define_decoder_block(dblock1, start_filters*4)
    dblock3 = define_decoder_block(dblock2, start_filters*2)
    dblock4 = define_decoder_block(dblock3, start_filters)
    output = Conv2D(3, 1, activation = 'tanh')(dblock4)
    
    # Define the models.
    decoder = Model(inputs = inputs_embedding, outputs = output)
    if conditioning_dim > 0:
        encoder_with_sampling = Model(inputs = [inputs, condition], outputs = z)
        encoder_with_sampling_ext = Model(inputs = [inputs, condition], outputs = z_ext)
        vae_out = decoder(encoder_with_sampling_ext([inputs, condition]))
        vae = Model(inputs = [inputs, condition], outputs = vae_out)
    else:
        encoder_with_sampling = Model(inputs = inputs, outputs = z)
        vae_out = decoder(encoder_with_sampling(inputs))
        vae = Model(inputs = inputs, outputs = vae_out)
    
    # Define the VAE loss.
    def vae_loss(x, x_decoded_mean):
        """Defines the VAE loss functions as a combination of MSE and KL-divergence loss."""
        mse_loss = K.mean(keras.losses.mse(x, x_decoded_mean), axis=(1,2)) * height * width
        kl_loss = - 0.5 * K.mean(1 + z_log_sigma - K.square(z_mean) - K.exp(z_log_sigma), axis=-1)
        return mse_loss + kl_loss
    
    if variational:
        vae.compile(loss=vae_loss, optimizer='adam')
    else:
        vae.compile(loss='mse', optimizer='adam')    
        
    print('done,', vae.count_params(), 'parameters.')
    return vae, encoder_with_sampling, decoder

def encode_image(img, conditioning, encoder, height, width, batch_size):
    '''Encodes an image that is given in RGB-channel order with value range of [0, 255].
    
    Args:
        img: The image input. If shapes differ from (height, width), it will be resized.
        conditoning: The set of values to condition on, if any. Can be None.
        encoder: The keras encoder model to use.
        height: The target image height.
        width: The target image width.
        batch_size: The batchsize that the encoder expects.
        
    Returns:
        The latent representation of the input image.
    '''
    if img.shape[0] != height or img.shape[1] != width:
        img = skimage.transform.resize(img, (height, width))
    img_single = np.expand_dims(img, axis=0)
    img_single = img_single.astype(np.float32)
    img_single = np.repeat(img_single, batch_size, axis=0)
    if conditioning is None:
        z = encoder.predict(img_single)
    else:
        z = encoder.predict([img_single, np.repeat(np.expand_dims(conditioning, axis=0), batch_size, axis=0)])
    return z

def decode_embedding(z, conditioning, decoder):
    '''Decodes the given representation into an image.
    
    Args:
        z: The latent representation.
        conditioning: The set of values to condition on, if any. Can be None.
        decoder: The keras decoder model to use.
    '''
    if z.ndim < 2:
        z = np.expand_dims(z, axis=0) # Single-batch
    if conditioning is not None:
        z = np.concatenate((z, np.repeat(np.expand_dims(conditioning, axis=0), z.shape[0], axis=0)), axis=1)
    return decoder.predict(z)

Load Weights

def load_weights(folder):
    vae.load_weights(folder + '/vae.w')
    encoder.load_weights(folder + '/encoder.w')
    decoder.load_weights(folder + '/decoder.w')
    
def save_weights(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)
    vae.save_weights(folder + '/vae.w')
    encoder.save_weights(folder + '/encoder.w')
    decoder.save_weights(folder + '/decoder.w')

VARIATIONAL = True
HEIGHT = 128
WIDTH = 128
BATCH_SIZE = 16
LATENT_DIM = 16
START_FILTERS = 32
CONDITIONING = True

import tensorflow
class CustomDataGenerator(tensorflow.keras.utils.Sequence):
    def __init__(self, files, batch_size, target_height, target_width, conditioning_dim=0, conditioning_data=None):
        '''
        Intializes the custom generator.
        
        Args:
            files: The list of paths to images that should be fed to the network.
            batch_size: The batchsize to use.
            target_height: The target image height. If different, the images will be resized.
            target_width: The target image width. If different, the images will be resized.
            conditioning_dim: The dimension of the conditional variable space. Can be 0.
            conditioning_data: Optional dictionary that maps from the filename to the data to be
                conditioned on. Data must be numeric. Can be None. Otherwise, len must be equal to
                conditioning_dim.
        '''
        self.files = files
        self.batch_size = batch_size
        self.target_height = target_height
        self.target_width = target_width
        self.conditioning_dim = conditioning_dim
        self.conditioning_data = conditioning_data

    def on_epoch_end(self):
        '''Shuffle list of files after each epoch.'''
        np.random.shuffle(self.files)
        
    def __getitem__(self, index):
        cur_files = self.files[index*self.batch_size:(index+1)*self.batch_size]
        # Generate data
        X, y = self.__data_generation(cur_files)
        return X, y
    
    def __data_generation(self, cur_files):
        X = np.empty(shape=(self.batch_size, self.target_height, self.target_width, 3))
        Y = np.empty(shape=(self.batch_size, self.target_height, self.target_width, 3))
        if self.conditioning_data != None:
            C = np.empty(shape=(self.batch_size, self.conditioning_dim))
        
        for i, file in enumerate(cur_files):
            img = skimage.io.imread(file)
            if img.shape[0] != self.target_height or img.shape[1] != self.target_width:
                img = skimage.transform.resize(img, (self.target_height, self.target_width)) # Resize.
            img = img.astype(np.float32) / 255.
            X[i] = img
            Y[i] = img
            if self.conditioning_data != None:
                C[i] = self.conditioning_data[os.path.basename(file)]
                
        if self.conditioning_data != None:
            return [X, C], Y
        else:
            return X, Y
    
    def __len__(self):
        return int(np.floor(len(self.files) / self.batch_size))

"""Conditions"""

# Find image files.
files = glob.glob('celeba/img_align_celeba/*.jpg')
print(len(files), 'images found.')

df = utils.load_celeba('celeba/list_attr_celeba.txt')
columns = df.columns
df.head(3)

dd = {}
selected_conditionals = list(columns[1:])
for i, row in df.iterrows():
    dd[row['Filename']] = [int(row[c]) for c in selected_conditionals]

gen = CustomDataGenerator(files=files, 
                          batch_size=BATCH_SIZE, 
                          target_height=HEIGHT, 
                          target_width=WIDTH, 
                          conditioning_dim=len(selected_conditionals),
                          conditioning_data=dd if CONDITIONING else None)

"""Define CVAE"""

vae, encoder, decoder = define_net(variational=VARIATIONAL,
                                   height=HEIGHT, 
                                   width=WIDTH, 
                                   batch_size=BATCH_SIZE, 
                                   latent_dim=LATENT_DIM,
                                   conditioning_dim=len(selected_conditionals) if CONDITIONING else 0, 
                                   start_filters=START_FILTERS)

load_weights(folder='models/celeba_vae')

"""Let's look at some examples. First, we will select a random image from the CelebA dataset, and read the related annotation data."""

rnd_file = np.random.choice(files)
file_id = os.path.basename(rnd_file)
init_meta = dd[file_id]
img = skimage.io.imread(rnd_file)
plt.imshow(img)
plt.show()

"""Encode Image to Latent Dimension"""

z = encode_image(img.astype(np.float32) / 255., np.array(init_meta), encoder, HEIGHT, WIDTH, BATCH_SIZE)
print('latent sample:\n', z[0])

"""Decode Latent information to Image"""

ret = decode_embedding(z, init_meta, decoder)
plt.imshow(ret[0])
plt.show()

"""HeatMAP"""

example_batch = next(data_flow)
example_batch = example_batch[0]
example_images = example_batch[:10]
img_array = example_images[0]
matplotlib.pyplot.imshow(img_array)
img_array = tf.keras.preprocessing.image.img_to_array(img_array)
img_array = np.expand_dims(img_array, axis=0)
res = vae_model.predict(img_array)

import matplotlib
res = res.reshape((128,128,3))
matplotlib.pyplot.imshow(res[1:])

last_conv_layer_name = "encoder_conv_3"
encoder_out = "encoder_output"

def make_gradcam_heatmap(img_array, model, last_conv_layer_name, encoder_out, pred_index=None):
    grad_model = tf.keras.models.Model(
        [model.inputs], [model.get_layer(last_conv_layer_name).output, model.get_layer(encoder_out).output]
    )
    with tf.GradientTape() as tape:
        last_conv_layer_output, preds = grad_model(img_array)
    
    grads = tape.gradient(preds, last_conv_layer_output)

    # This is a vector where each entry is the mean intensity of the gradient
    # over a specific feature map channel
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # We multiply each channel in the feature map array
    # by "how important this channel is" with regard to the top predicted class
    # then sum all the channels to obtain the heatmap class activation
    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = tf.matmul(last_conv_layer_output, pooled_grads[..., tf.newaxis])
    heatmap = tf.squeeze(heatmap)

    # For visualization purpose, we will also normalize the heatmap between 0 & 1
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap, grads, pooled_grads, preds, last_conv_layer_output
In [ ]:

heatmap, grads, pooled_grads, preds, last_conv_layer_output = make_gradcam_heatmap(img_array, vae_model, last_conv_layer_name, encoder_out)

print(preds)
print(last_conv_layer_output)
print(grads)
print(pooled_grads)

def save_and_display_gradcam(img, heatmap,cam_path="superimposed_img.jpg", alpha=0.4):
    heatmap = np.uint8(255 * heatmap)
    jet = cm.get_cmap("jet")
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]
    jet_heatmap = keras.preprocessing.image.array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = keras.preprocessing.image.img_to_array(jet_heatmap)
    superimposed_img = cv2.addWeighted(jet_heatmap, 0.005, img, 0.995, 0)
    superimposed_img = keras.preprocessing.image.array_to_img(superimposed_img)
    superimposed_img.save(cam_path)

save_and_display_gradcam(img_array.squeeze(), heatmap)