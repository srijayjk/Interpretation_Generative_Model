# Interpretation_Generative_Model
This repo contains the project done in Fachpraktikum for Machine Learning and Computer Vision for HCI.
The repo contains files related to 3 different implementations with different configuration of Variational AutoEncoder with Grad_CAM.

## Towards Visually Explaining Variational Autoencoders.

![GRAD_VAE](https://user-images.githubusercontent.com/23414920/132089652-2400d112-ef2b-4903-9837-68e37f845991.JPG)


link  : https://arxiv.org/abs/1911.07389

Our work is based on the paper mentioned here.

The Grad_CAM is implemented on Variational AutoEncoder model. The model is trained on Celeb_A_MaskHQ dataset.

## Requirements

* Python 3.9.5
* Tensorflow 2.5.0
* Numpy 1.20.2
* Keras 2.4.3

## Models

There are 3 different models as mentioned with different tasks.
We have used VAE and CVAE for implementation with Grad-CAM.

* **Model 1** : VAE model trained on CelebAMask-HQ with Grad-CAM for interpretation.
* **Model 2** : CVAE model trained on CelebAMask-HQ with Grad-CAM.
* **Model 3** : VAE model tarined on CelebAMask-HQ for Semantic Segmentation application with Grad-CAM.


## Running codes

Start training a VAE with default settings by call:

```python example.py```

Jupyter Notebook Files are also avaiable with ipynb extension.

### For the detailed information, refer to our ICML format based report in the descripition.

## Results


![CVAE_Op_1](https://user-images.githubusercontent.com/23414920/132098179-69dd3089-6a99-4a09-9e2b-cc6f5a968427.JPG)


### Latent Space Exploration

![gif](https://user-images.githubusercontent.com/23414920/132098139-8276b272-cbc2-441a-bb90-c8c342e17f2f.gif)

![ezgif](https://user-images.githubusercontent.com/23414920/132098162-81e81d45-8333-488d-ae41-8388bc304eca.gif)

