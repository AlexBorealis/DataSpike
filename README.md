# Document Classification Pipeline

Этот проект предназначен для извлечения страны происхождения документа с помощью конвейера, включающего этапы
предварительной обработки изображений, OCR (Optical Character Recognition) и классификации.

## Содержание

1. [Начало работы](#начало-работы)
2. [Структура проекта](#структура-проекта)
3. [Конфиг](#конфиг)
4. [Запуск пайплайна](#запуск-пайплайна)
5. [Результат](#результат)
6. [Makefile](#makefile)

## Начало работы

### Требования

- Python 3.10 или выше
- pip (Python пакетный менеджер)

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/AlexBorealis/DataSpike.git
   cd DataSpike
   ```

2. Создайте виртуальное окружение и активируйте его:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # На Windows используйте `.venv\Scripts\activate`
   ```

3. Установите необходимые пакеты:
   ```bash
   pip install -r requirements/requirements.txt
   ```

## Структура проекта

Проект организован следующим образом:

```
DataSpike/
├── src/  
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── preprocessor.py
│   │   ├── classifier.classifier.py
│   │   ├── detector.detector.py
│   │   ├── pipeline.py
│   │   └── ocr/
│   │      ├── __init__.py
│   │      ├── base.py
│   │      ├── easyocr_ocr.py
│   │      └── tesseract_ocr.py
│   ├── serializers/
│   │   ├── __init__.py
│   │   └── serializers.py
│   └── utils/
│       ├── __init__.py
│       ├── datasets.py
│       └── utils.py
├── config/
│   └── params/
│       └── config.yaml
├── data/
│   └──preprocessing/
│      ├── __init__.py
│      ├── augment_images.py
│      ├── augmentations.py
│      └── prepare_to_classify.py
├── main.py
├── .gitignore
├── .dockerignore
├── requirements.txt
├── Dockerfile
└── Makefile
```

## [Конфиг](config/params/config.yaml)

Конфиг хранится в папке `config`. Вы можете изменить этот файл для изменения путей к моделям,
входному изображению и других параметров.

```yaml
input:
  images:
    - input/BEL_11.jpg
    - input/BLR_29.jpg
    - input/UZB_83.jpg
    - input/UZB_94.jpg
    - input/BLR_6.jpg
    - input/BLR_26.jpg
    - input/BLR_29.jpg
    - input/UZB_92.jpg
    - input/UZB_93.jpg

model:
  detector: /src/models/prod_models/yolo/mrz_detector_v2_openvino_model
  classifier: /src/models/prod_models/yolo/best_classify.pt

pipeline:
  ocr: easyocr
  checker: true

run:
  device: cuda
  verbose: false
  imgsz: 640
  batch_size: 8
```

## Запуск пайплайна

### Обычный запуск

```bash
python -m main --config config/params/config.yaml
```

#### Сервис:

1) обработает изображения из config.yaml

2) перейдёт в интерактивный режим

```
Image path:
```

## При запуске сервиса в контейнере нужно указывать такой путь к изображению `app/input/image_name.jpg`

### Переопределение изображения

```bash
python -m main --config config/params/config.yaml --image /path/to/new/image.jpg
```

CLI аргумент имеет приоритет над конфигом.

### Интерактивный режим

После обработки конфигурации сервис ожидает новые изображения:

```
Image path: /path/to/image.jpg
```

## Пример изображения

![image0.jpg](output/image0.jpg)
**Синим выделена зона MRZ (Machine Readable Zone); код страны по ICAO - первые 3 буквы после символа `<`**

## Результат

После запуска сервис выполняет полный конвейер обработки MRZ (Machine Readable Zone) документа
и возвращает структурированный JSON-ответ с результатом определения страны документа.

Пайплайн включает следующие этапы:

1. Чтение изображения документа
2. Проверка качества изображения (blur и contrast)
3. Если качество плохое → используется классификатор страны
4. Если качество нормальное:
    - детекция MRZ зоны
    - предобработка MRZ
    - OCR распознавание строк
    - постобработка MRZ
    - извлечение страны из MRZ
5. Если OCR не смог извлечь страну → используется fallback классификация.

---

## Формат результата

Pipeline возвращает JSON со следующими полями:

| Поле     | Описание                                                         |
|----------|------------------------------------------------------------------|
| mode     | режим работы                                                     |
| result   | страна документа/уверенность классификатора (если использовался) |
| blur     | метрика размытия изображения                                     |
| contrast | метрика контраста изображения                                    |
| timings  | время выполнения этапов (в миллисекундах)                        |

---

## Пример ответа (OCR режим)

```json
{
  "mode": "ocr",
  "result": {
    "country": "USA",
    "confidence": null
  },
  "blur": 142.51,
  "contrast": 54.32,
  "timings": {
    "read_image_ms": 3.2,
    "quality_check_ms": 4.1,
    "mrz_detection_ms": 12.7,
    "preprocessing_ms": 8.4,
    "ocr_ms": 25.6,
    "postprocess_ms": 1.3,
    "total_ms": 55.9
  }
}
```

## Пример ответа (классификация)

```json
{
  "mode": "classification",
  "result": {
    "country": "USA",
    "confidence": 0.97
  },
  "blur": 18.4,
  "contrast": 12.3,
  "timings": {
    "read_image_ms": 3.2,
    "quality_check_ms": 4.1,
    "classification_ms": 21.5,
    "total_ms": 30.1
  }
}
```

## Пример ответа (fallback классификация)

```json
{
  "mode": "classification_fallback",
  "result": {
    "country": "USA",
    "confidence": 0.97
  },
  "blur": 110.2,
  "contrast": 45.8,
  "timings": {
    "read_image_ms": 3.1,
    "quality_check_ms": 4.0,
    "mrz_detection_ms": 13.2,
    "preprocessing_ms": 7.8,
    "ocr_ms": 24.5,
    "postprocess_ms": 1.2,
    "classification_ms": 20.4,
    "total_ms": 74.6
  }
}
```

### Завершение сервиса

Можно завершить сервис:

```

exit
quit

```

или

```

Ctrl+C

```

### [Makefile](Makefile)

`Makefile` содержит команды для быстрой сборки и запуска образа Docker.

### 3) Использование Makefile

```makefile
IMAGE_NAME=dataspike
CONTAINER_NAME=dataspike_service

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		--gpus all --cpus=6 --memory=6g \
		-e DATA_DIR=/app \
		-e SOURCE_DIR=/app \
		-v $(PWD)/config/params:/app/config \
		-v $(PWD)/input:/app/input \
		$(IMAGE_NAME)

start: build run

shell:
	docker exec -it $(CONTAINER_NAME) bash

stop:
	docker stop $(CONTAINER_NAME)

clean:
	-docker rmi -f $(IMAGE_NAME)
	docker system prune -a --volumes -f

.PHONY: build run start stop clean
```

```
make build # только сборка образа
make run # только запуск контейнера
make start # build + run
make shell # shell внутри контейнера
make stop # остановка контейнера dataspike_service
make clean # удаление образа dataspike
```

Этот набор позволяет легко управлять проектом и запускать его в любой среде с использованием Docker.