import os
import shutil
from typing import Optional

from sklearn.model_selection import train_test_split
from tqdm import tqdm


def split_dataset(
    input_images_dir: str,
    input_labels_dir: Optional[str],
    output_images_dir: str,
    output_labels_dir: Optional[str] = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.2,
    test_ratio: float = 0.0,
) -> None:
    """
    Разделяет датасет на train / val / (опционально test).
    test_ratio может быть 0.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-5:
        raise ValueError("Сумма долей должна быть равна 1.0")

    # Список сплитов, которые будем создавать
    splits = ["train", "val"]
    if test_ratio > 0:
        splits.append("test")

    for split in splits:
        os.makedirs(os.path.join(output_images_dir, split), exist_ok=True)
        if output_labels_dir:
            os.makedirs(os.path.join(output_labels_dir, split), exist_ok=True)

    # Собираем пары
    image_files = {
        f.split(".")[0]
        for f in os.listdir(input_images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"))
    }

    label_files = set()
    if input_labels_dir:
        label_files = {
            f.split(".")[0]
            for f in os.listdir(input_labels_dir)
            if f.lower().endswith(".txt")
        }

    common_names = image_files
    if input_labels_dir:
        common_names = image_files & label_files

    if not common_names:
        print("Нет пар изображение-аннотация → сплит пропущен")
        return

    paired_files = []
    for name in common_names:
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            img_path = os.path.join(input_images_dir, f"{name}{ext}")
            if os.path.exists(img_path):
                paired_files.append((f"{name}{ext}", f"{name}.txt"))
                break

    print(f"Найдено пар: {len(paired_files)}")

    # Разделение
    train_files, temp_files = train_test_split(
        paired_files, train_size=train_ratio, random_state=42, shuffle=True
    )

    if test_ratio > 0:
        test_size = test_ratio / (test_ratio + val_ratio)
        test_files, val_files = train_test_split(
            temp_files, train_size=test_size, random_state=42, shuffle=True
        )
    else:
        val_files = temp_files
        test_files = []

    split_mapping = {
        "train": train_files,
        "val": val_files,
        "test": test_files,
    }

    for split in splits:
        files = split_mapping[split]
        if not files:
            continue

        for img_file, lbl_file in tqdm(files, desc=split):
            shutil.copy(
                os.path.join(input_images_dir, img_file),
                os.path.join(output_images_dir, split, img_file),
            )
            if output_labels_dir and input_labels_dir:
                src_lbl = os.path.join(input_labels_dir, lbl_file)
                if os.path.exists(src_lbl):
                    shutil.copy(
                        src_lbl,
                        os.path.join(output_labels_dir, split, lbl_file),
                    )
