import os
import shutil

from src.data.preprocessing.augmentations import AugmentImages
from src.utils.datasets import split_dataset

# Paths
IMAGES = os.path.join(os.getenv("DATA_DIR"), "raw", "images")
LABELS = os.path.join(os.getenv("DATA_DIR"), "raw", "labels")

PROCESSED_IMAGES = os.path.join(os.getenv("DATA_DIR"), "processed", "detect", "images")
PROCESSED_LABELS = os.path.join(os.getenv("DATA_DIR"), "processed", "detect", "labels")

TEMP_IMAGES = os.path.join(PROCESSED_IMAGES, "temp")
TEMP_LABELS = os.path.join(PROCESSED_LABELS, "temp")

os.makedirs(PROCESSED_IMAGES, exist_ok=True)
os.makedirs(PROCESSED_LABELS, exist_ok=True)
os.makedirs(TEMP_IMAGES, exist_ok=True)
os.makedirs(TEMP_LABELS, exist_ok=True)

# Augmentations
AugmentImages.augment_all(
    input_img_dir=IMAGES,
    input_lbl_dir=LABELS,
    output_img_dir=TEMP_IMAGES,
    output_lbl_dir=TEMP_LABELS,
    modes=AugmentImages.MODES,
    num_processes=8,
)

# Splitting samples
split_dataset(
    input_images_dir=TEMP_IMAGES,
    input_labels_dir=TEMP_LABELS,
    output_images_dir=PROCESSED_IMAGES,
    output_labels_dir=PROCESSED_LABELS,
    train_ratio=0.7,
    val_ratio=0.2,
    test_ratio=0.1,
)

# Cleaning
shutil.rmtree(TEMP_IMAGES, ignore_errors=True)
shutil.rmtree(TEMP_LABELS, ignore_errors=True)
