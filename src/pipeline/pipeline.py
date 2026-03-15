import time

import cv2

from src.utils.utils import extract_country_from_mrz


class Pipeline:
    def __init__(
            self,
            detector,
            preprocessor=None,
            ocr=None,
            classifier=None,
            ocr_kwargs=None,
            checker=None,
    ):
        """
        MRZ processing pipeline.

        Pipeline выполняет полный цикл извлечения страны документа из изображения:

        1. Загрузка изображения
        2. Проверка качества изображения (blur / contrast)
        3. Если качество плохое → запуск классификатора страны
        4. Если качество нормальное:
            - детекция MRZ зоны
            - предобработка MRZ
            - OCR распознавание строк
            - исправление MRZ (опционально)
            - извлечение страны из MRZ
        5. Если OCR не смог извлечь страну → fallback на классификатор.

        Pipeline возвращает результат и подробную статистику времени выполнения
        каждого этапа (в миллисекундах).

        Parameters
        ----------
        detector : MRZDetector
            Модель детекции MRZ зоны (обычно YOLO).

        preprocessor : MRZPreprocessor, optional
            Класс предобработки MRZ изображения:
            - анализ качества
            - подготовка строк MRZ для OCR.

        ocr : class, optional
            Класс OCR ридера (например TesseractOCRReader или EasyOCRReader).
            Передается как класс, а не экземпляр.

        classifier : DocumentClassifier, optional
            Классификатор страны документа по изображению.
            Используется:
            - при плохом качестве изображения
            - как fallback если OCR не смог извлечь страну.

        ocr_kwargs : dict, optional
            Параметры для инициализации OCR класса.

        checker : MRZChecker, optional
            Класс постобработки MRZ для исправления возможных OCR ошибок.
        """
        self.detector = detector
        self.preprocessor = preprocessor
        self.classifier = classifier
        self.checker = checker

        if ocr is not None:
            self.ocr = ocr(**(ocr_kwargs or {}))
        else:
            self.ocr = None

    def run(self, image_path: str, n: int = 2, **model_kwargs):
        """
        Run full MRZ processing pipeline.

        Parameters
        ----------
        image_path : str
            Путь к файлу изображения.

        n: int (default 2)
            Количество знаков после запятой.

        model_kwargs : dict
            Дополнительные параметры модели
            (например device='cpu').

        Returns
        -------
        dict
            Результат обработки.

            Форматы ответа:

            OCR режим:
            {
                "mode": "ocr",
                "image_path": ...,
                "result": "USA",
                "blur": float,
                "contrast": float,
                "timings": {...}
            }

            Классификация:
            {
                "mode": "classification",
                "image_path": ...,
                "result": "USA",
                "confidence": float,
                "blur": float,
                "contrast": float,
                "timings": {...}
            }

            Fallback классификация:
            {
                "mode": "classification_fallback",
                "image_path": ...,
                "result": "USA",
                "confidence": float,
                "blur": float,
                "contrast": float,
                "timings": {...}
            }
        """
        t0 = time.perf_counter()
        timings = {}

        # ---------- READ IMAGE ----------
        t = time.perf_counter()
        img = cv2.imread(image_path)
        timings["read_image_ms"] = round((time.perf_counter() - t) * 1000, n)

        # ---------- QUALITY CHECK ----------
        t = time.perf_counter()
        blur, contrast = self.preprocessor.analyze_quality(img)
        timings["quality_check_ms"] = round((time.perf_counter() - t) * 1000, n)

        blur = round(blur, n)
        contrast = round(contrast, n)

        # ---------- CLASSIFICATION BRANCH ----------
        if (
                blur < self.preprocessor.BLUR_THRESHOLD
                or contrast < self.preprocessor.CONTRAST_THRESHOLD
        ):
            if not self.classifier:
                raise ValueError("Classifier not configured")

            t = time.perf_counter()
            result_cls = self.classifier.classify(image_path, n, **model_kwargs)
            timings["classification_ms"] = round((time.perf_counter() - t) * 1000, n)

            timings["total_ms"] = round((time.perf_counter() - t0) * 1000, n)

            return {
                "mode": "classification",
                "image_path": image_path,
                "result": result_cls,
                "blur": blur,
                "contrast": contrast,
                "timings": timings,
            }

        # ---------- MRZ DETECTION ----------
        t = time.perf_counter()
        crop = self.detector.detect(image_path, **model_kwargs)
        timings["mrz_detection_ms"] = round((time.perf_counter() - t) * 1000, n)

        # ---------- PREPROCESS ----------
        t = time.perf_counter()
        lines = self.preprocessor.process(crop)
        timings["preprocessing_ms"] = round((time.perf_counter() - t) * 1000, n)

        # ---------- OCR ----------
        t = time.perf_counter()

        texts = []

        for line in lines:
            text = self.ocr.read_line(line)
            text = text.strip().replace(" ", "")

            if not text:
                continue

            texts.append(text)

        timings["ocr_ms"] = round((time.perf_counter() - t) * 1000, n)

        # ---------- CHECKER ----------
        t = time.perf_counter()

        if self.checker and len(texts) == 2:
            texts = self.checker.fix_mrz(texts)

        timings["postprocess_ms"] = round((time.perf_counter() - t) * 1000, n)

        mrz_text = "\n".join(texts)

        country = extract_country_from_mrz(mrz_text)

        # ---------- OCR FAILED → FALLBACK ----------
        if country is None and self.classifier:
            t = time.perf_counter()
            result_cls = self.classifier.classify(image_path, n, **model_kwargs)
            timings["classification_ms"] = round((time.perf_counter() - t) * 1000, n)

            timings["total_ms"] = round((time.perf_counter() - t0) * 1000, n)

            return {
                "mode": "classification_fallback",
                "image_path": image_path,
                "result": result_cls,
                "blur": blur,
                "contrast": contrast,
                "timings": timings,
            }

        timings["total_ms"] = round((time.perf_counter() - t0) * 1000, n)

        return {
            "mode": "ocr",
            "image_path": image_path,
            "result": {"country": country, "confidence": None},
            "blur": blur,
            "contrast": contrast,
            "timings": timings,
        }
