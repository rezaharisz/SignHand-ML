# -*- coding: utf-8 -*-
"""Sign Hand Translator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n6vv12bcazQFj-rMtNODXET5Sxw30oGE
"""

!pip install tflite-model-maker

import matplotlib.pyplot as plt
import numpy as np

import os

import seaborn as sn
from sklearn.metrics import confusion_matrix

import tensorflow as tf
assert tf.__version__.startswith('2')

from tflite_model_maker import model_spec
from tflite_model_maker import image_classifier
from tflite_model_maker.config import ExportFormat
from tflite_model_maker.config import QuantizationConfig
from tflite_model_maker.image_classifier import DataLoader

!wget --no-check-certificate -r \
      "https://drive.google.com/u/0/uc?id=1JZlWO_ekSE2uQn-zTGEofB0NIJ2SxkCE&export=download" \
      -O signhand_datasets.zip

ds_path = "Datasets"

import os, zipfile


zip_archive = "signhand_datasets.zip"
zip_ref = zipfile.ZipFile(zip_archive, "r")
zip_ref.extractall(ds_path)
zip_ref.close()

datasets = DataLoader.from_folder(ds_path)

training, rest = datasets.split(0.8) # 80% for training
validation, testing = rest.split(0.5) # 10% for testing, 10% for validation

plt.figure(figsize=(15, 15))
for i, (image, label) in enumerate(
    datasets.gen_dataset().unbatch().take(25)):
  plt.subplot(5, 5, i+1)
  plt.xticks([])
  plt.yticks([])
  plt.grid(False)
  plt.imshow(image.numpy(), cmap=plt.cm.gray)
  plt.xlabel(datasets.index_to_label[label.numpy()])

plt.show()

efficientnet_model = model_spec.get("efficientnet_lite1")

model = image_classifier.create(training,
                                epochs=10,
                                validation_data=validation,
                                use_augmentation=True,
                                shuffle=True,
                                model_spec=efficientnet_model)

model.summary()

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

#Loss graph
plt.figure(figsize=(8, 6))
plt.plot(model.history.history["loss"])
plt.plot(model.history.history["val_loss"])
plt.title("Loss")
plt.ylabel("Losses")
plt.xlabel("Epochs")
plt.grid(True)
plt.legend(["training", "validation"], loc="upper left")
plt.show()

#Accuracy graph
plt.figure(figsize=(8, 6))
plt.plot(model.history.history["accuracy"])
plt.plot(model.history.history["val_accuracy"])
plt.title("Accuracy")
plt.ylabel("Accuracies")
plt.xlabel("Epochs")
plt.grid(True)
plt.legend(["training", "validation"], loc="upper left")
plt.show()

model.evaluate(testing)

def get_label_color(predict_label, actual_label):
  if predict_label == actual_label:
    return "black"
  else:
    return "red"

plt.figure(figsize=(20, 20))
predicts = model.predict_top_k(testing)
for i, (image, label) in enumerate(
    testing.gen_dataset().unbatch().take(30)):
  ax = plt.subplot(5, 6, i+1)
  plt.xticks([])
  plt.yticks([])
  plt.grid(False)
  plt.imshow(image.numpy(), cmap="Greys")

  predict_label = predicts[i][0][0]
  color = get_label_color(predict_label,
                          testing.index_to_label[label.numpy()])
  ax.xaxis.label.set_color(color)
  plt.xlabel("Predicted:\n{}".format(predict_label))

plt.show()

labels = os.listdir(os.path.join(ds_path))
labels.sort()

label_dicts = {}

for i in range(len(labels)):
  label_dicts[labels[i]] = i

predicts = model.predict_top_k(testing)
predict_labels = [ label_dicts[predicts[i][0][0]]
                  for i, (image, label) in enumerate(testing.gen_dataset().unbatch()) ]

actual_labels = [ label.numpy()
                  for i, (image, label) in enumerate(testing.gen_dataset().unbatch()) ]

plt.figure(figsize=(15, 10))
signhand_cm = confusion_matrix(y_true=actual_labels, y_pred=predict_labels)
signhand_cm = signhand_cm / signhand_cm.sum(axis=1) # To display conf. matrix in percetage %

sn.heatmap(signhand_cm, annot=True, cmap="Greens")

model.export(export_dir=".")

model.export(export_dir=".", export_format=ExportFormat.LABEL)

model.evaluate_tflite("model.tflite", testing)

quantizer = QuantizationConfig.for_int8(representative_data=testing)

model.export(export_dir=".", quantization_config=quantizer)

model.evaluate_tflite("model.tflite", testing)

from google.colab import files
files.download('model.tflite')