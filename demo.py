import os,sys
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import tensorflow_datasets as tfds

src_dir = os.path.dirname(os.path.realpath(__file__))
while not src_dir.endswith("Graph-FPN"):
    src_dir = os.path.dirname(src_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from detection.utils.Label import *
from model.network import get_backbone, RetinaNet
from detection.utils.preprocess import *
from model.network import DecodePredictions
from configs.configs import parse_configs
config = parse_configs()
    

def demo():
    weights_dir = "data_demo/data"
    resnet50_backbone = get_backbone()
    model = RetinaNet(config.num_classes, resnet50_backbone)
    # fine_tune_checkpoint_type
    ckpt = tf.train.Checkpoint(model)
    ckpt.restore(tf.train.latest_checkpoint(weights_dir)).expect_partial()

    # Building inference model
    image = tf.keras.Input(shape=[None, None, 3], name="image")
    predictions = model(image, training=False)
    detections = DecodePredictions(confidence_threshold=0.5)(
        image, predictions)
    inference_model = tf.keras.Model(inputs=image, outputs=detections)
    # inference_model.summary()

    val_dataset, dataset_info = tfds.load("coco/2017", split="validation", with_info=True, data_dir="data_demo/data", download=False)
    int2str = dataset_info.features["objects"]["label"].int2str

    for sample in val_dataset.take(2):
        image = tf.cast(sample["image"], dtype=tf.float32)
        input_image, ratio = prepare_image(image)
        detections = inference_model.predict(input_image)
        num_detections = detections.valid_detections[0]
        class_names = [
            int2str(int(x)) for x in detections.nmsed_classes[0][:num_detections]
        ]
        visualize_detections(
            image,
            detections.nmsed_boxes[0][:num_detections] / ratio,
            class_names,
            detections.nmsed_scores[0][:num_detections],
        )

if __name__ == "__main__":
    demo()