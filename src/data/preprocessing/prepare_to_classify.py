import os
import shutil

from tqdm import tqdm

FROM_IMAGES = os.path.join(os.getenv("DATA_DIR"), "processed", "detect", "images")
TO_IMAGES = os.path.join(os.getenv("DATA_DIR"), "processed", "classify", "images")

splits = ["train", "val", "test"]

for split in splits:
    src_dir = os.path.join(FROM_IMAGES, split)
    dst_dir = os.path.join(TO_IMAGES, split)

    os.makedirs(dst_dir, exist_ok=True)

    for file in tqdm(os.listdir(src_dir), desc=split):
        src_file = os.path.join(src_dir, file)

        if not os.path.isfile(src_file):
            continue

        name, ext = os.path.splitext(file)

        if "_" not in name:
            print("skip:", file)
            continue

        country = name.split("_")[0]

        class_dir = os.path.join(dst_dir, country)

        os.makedirs(class_dir, exist_ok=True)

        dst_file = os.path.join(class_dir, file)

        shutil.copy2(src_file, dst_file)

print("Done")
