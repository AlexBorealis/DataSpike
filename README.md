Конечно! Вот перевод на русский и файл `Dockerfile` для сборки образа:

# MRZ Extraction and Document Classification Pipeline

Этот проект предназначен для извлечения страны происхождения документа с помощью конвейера, включающего этапы
предварительной обработки изображений, OCR (Optical Character Recognition) и классификации.

## Содержание

1. [Начало работы](#начало-работы)
2. [Структура проекта](#структура-проекта)
3. [Конфигурация](#конфигурация)
4. [Запуск конвейера](#запуск-конвейера)
5. [Настройка Docker](#настройка-docker)

## Начало работы

### Требования

- Python 3.8 или выше
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
   source .venv/bin/activate  # На Windows используйте `venv\Scripts\activate`
   ```

3. Установите необходимые пакеты:
   ```bash
   pip install -r requirements.txt
   ```

## Структура проекта

Проект организован следующим образом:

```
DataSpike/
├── src/│   
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── checker.py
│   │   ├── classifier.py
│   │   ├── detector.py
│   │   ├── ocr/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── easyocr_ocr.py
│   │   │   └── tesseract_ocr.py
│   │   ├── preprocessor.py
│   │   └── pipeline.py
│   ├── serializers/
│   │   ├── __init__.py
│   │   └── serializers.py
│   └── utils/
│       ├── datasets.py
│       └── utils.py
├── config/
│   └── params/
│       └── config.yaml
├── data/
│   └──preprocessing/
│      ├── augment_images.py
│      └── prepare_to_classify.py
├── main.py
├── Dockerfile
└── Makefile
```

## Конфигурация

Конфигурация хранится в файле `config/params/config.yaml`. Вы можете изменить этот файл для изменения путей к моделям,
входному изображению и других параметров.

```yaml
input:
  images:
    - /data/images/USA_99.jpg
    - /data/images/USA_9.jpg
    - /data/images/USA_1.jpg

model:
  detector: /models/mrz_detector_v2_int8_openvino_model
  classifier: /models/best_classify.pt

pipeline:
  ocr: easyocr
  checker: true

run:
  device: cpu
  verbose: false
  imgsz: 320
```

## Запуск конвейера

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

### Переопределение изображения

```bash
python -m main --config config/params/config.yaml --image /path/to/new/image.jpg
```

CLI аргумент имеет приоритет над конфигом.

## Интерактивный режим

После обработки конфигурации сервис ожидает новые изображения:

```
Image path: /path/to/image.jpg
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

## Настройка Docker

### Docker

```
docker build -t dataspike .
```

### Запуск контейнера

```
docker run \
-v $(pwd):/app \
dataspike
```

### Makefile

`Makefile` содержит цели для сборки и запуска образа Docker.

```makefile
# Сборка образа Docker
docker-build:
	docker build -t dataspike .

# Запуск контейнера Docker
docker-run:
	docker run --rm -v $(PWD):/app -w /app dataspike python -m main --config config/params/config.yaml
```

Этот набор позволяет легко управлять вашим проектом и запускать его в стабильной среде с использованием Docker.

Упрощённые команды:

```
make build
make run
make shell
```