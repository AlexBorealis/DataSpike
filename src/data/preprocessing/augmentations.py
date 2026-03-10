import multiprocessing
import os
from pathlib import Path
from typing import List, Optional

import cv2
from albumentations import (
    Blur,
    Compose,
    RandomBrightnessContrast,
    RandomShadow,
    Rotate,
    ToGray,
)
from tqdm import tqdm


class AugmentImages:
    MODES = ["normal", "blur", "rotated", "shadow", "brightness"]

    def __init__(
        self,
        image_path: Optional[str] = None,
        label_path: Optional[str] = None,
    ):
        self.image_path = image_path
        self.label_path = label_path

    @staticmethod
    def _load_labels(label_path: str):
        bboxes = []
        class_labels = []

        if not os.path.exists(label_path):
            return bboxes, class_labels

        with open(label_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = list(map(float, line.split()))
                if len(parts) < 5:
                    continue
                cls = int(parts[0])
                bbox = parts[1:5]
                bboxes.append(bbox)
                class_labels.append(cls)

        return bboxes, class_labels

    @staticmethod
    def _save_labels(
        label_path: str,
        bboxes: list,
        class_labels: list,
    ):
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        with open(label_path, "w") as f:
            for cls, bbox in zip(class_labels, bboxes):
                line = [str(cls)] + [f"{x:.6f}" for x in bbox]
                f.write(" ".join(line) + "\n")

    @staticmethod
    def get_pipeline(mode: str) -> Optional[Compose]:
        if mode == "normal":
            return Compose([])

        elif mode == "blur":
            return Compose(
                [
                    ToGray(p=0.35),
                    Blur(blur_limit=(5, 21), p=1.0),
                ]
            )

        elif mode == "brightness":
            return Compose(
                [
                    ToGray(p=0.35),
                    RandomBrightnessContrast(
                        brightness_limit=0.5, contrast_limit=0.5, p=1.0
                    ),
                ]
            )

        elif mode == "shadow":
            return Compose(
                [
                    ToGray(p=0.35),
                    RandomShadow(
                        num_shadows_limit=(1, 2),
                        shadow_dimension=10,
                        shadow_roi=(0, 0.0, 1, 1),
                        shadow_intensity_range=(0.3, 0.8),
                        p=1.0,
                    ),
                ]
            )

        elif mode == "rotated":
            return Compose(
                [
                    ToGray(p=0.35),
                    Rotate(
                        limit=180,
                        border_mode=cv2.BORDER_REPLICATE,
                        p=1.0,
                    ),
                ],
                bbox_params={"format": "yolo", "label_fields": ["class_labels"]},
            )

        return None

    def augment_single(
        self,
        output_img: str,
        output_lbl: str,
        mode: str,
        suffix: Optional[str] = None,
    ):
        """
        Применяет одну аугментацию к одному изображению и сохраняет результат.

        Args:
            output_img: Папка для сохранения аугментированного изображения
            output_lbl: Папка для сохранения аугментированной метки (или None)
            mode: Режим аугментации (из self.modes)
            suffix: Суффикс для имени файла (по умолчанию = mode)

        Returns:
            aug_image: Аугментированное изображение (numpy array в BGR)
            img_save_path: Путь к сохранённому изображению
            lbl_save_path: Путь к сохранённой метке или None
        """
        image_bgr = cv2.imread(self.image_path)
        if image_bgr is None:
            raise ValueError(f"Не удалось загрузить: {self.image_path}")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        bboxes, class_labels = (
            self._load_labels(self.label_path) if self.label_path else ([], [])
        )

        pipeline = self.get_pipeline(mode)
        if pipeline is None:
            raise ValueError(f"Неизвестный режим: {mode}")

        if mode == "normal":
            aug_image_rgb = image_rgb
            final_bboxes = bboxes
            final_class_labels = class_labels
        else:
            augmented = pipeline(
                image=image_rgb, bboxes=bboxes, class_labels=class_labels
            )
            aug_image_rgb = augmented["image"]
            final_bboxes = augmented.get("bboxes", bboxes)
            final_class_labels = augmented.get("class_labels", class_labels)

        aug_image_bgr = cv2.cvtColor(aug_image_rgb, cv2.COLOR_RGB2BGR)

        os.makedirs(output_img, exist_ok=True)
        os.makedirs(output_lbl, exist_ok=True)

        base_name = Path(self.image_path).stem
        ext = Path(self.image_path).suffix
        suffix = suffix or mode

        img_name = f"{base_name}_{suffix}{ext}"
        img_path = os.path.join(output_img, img_name)
        cv2.imwrite(img_path, aug_image_bgr)

        lbl_name = f"{base_name}_{suffix}.txt"
        lbl_path = os.path.join(output_lbl, lbl_name)

        if final_bboxes:
            self._save_labels(lbl_path, final_bboxes, final_class_labels)
        else:
            open(lbl_path, "w").close()

    @staticmethod
    def _process_single_image(
        image_path: str,
        input_lbl_dir: str,
        output_img_dir: str,
        output_lbl_dir: Optional[str],
        modes: Optional[List[str]],
    ):
        """
        Вспомогательная функция для обработки одного изображения в отдельном процессе.
        """
        try:
            base_name = Path(image_path).stem
            label_path = os.path.join(input_lbl_dir, f"{base_name}.txt")
            if not os.path.exists(label_path):
                label_path = None

            augmentor = AugmentImages(image_path, label_path)
            for mode in modes:
                augmentor.augment_single(
                    output_img=output_img_dir,
                    output_lbl=output_lbl_dir,
                    mode=mode,
                    suffix=mode,
                )
        except Exception as e:
            print(f"Ошибка {image_path}: {e}")

    @classmethod
    def augment_all(
        cls,
        input_img_dir: str,
        input_lbl_dir: str,
        output_img_dir: str,
        output_lbl_dir: Optional[str] = None,
        modes: Optional[List[str]] = None,
        num_processes: int = 1,
    ):
        """
        Аугментирует ВСЕ изображения в папке, используя apply_single для каждого режима.
        """
        modes = modes or cls.MODES

        img_files = [
            f
            for f in os.listdir(input_img_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        image_paths = [os.path.join(input_img_dir, f) for f in img_files]

        print(f"Изображений: {len(image_paths)}")
        print(f"Режимы: {modes}")
        print(f"Процессов: {num_processes}")

        if num_processes > 1:
            with multiprocessing.Pool(num_processes) as pool:
                args = [
                    (p, input_lbl_dir, output_img_dir, output_lbl_dir, modes)
                    for p in image_paths
                ]
                list(
                    tqdm(
                        pool.starmap(cls._process_single_image, args),
                        total=len(image_paths),
                        desc="Аугментация",
                    )
                )
        else:
            for path in tqdm(image_paths, desc="Аугментация"):
                cls._process_single_image(
                    path, input_lbl_dir, output_img_dir, output_lbl_dir, modes
                )
