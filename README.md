# Document Classification Pipeline

Этот проект предназначен для извлечения страны происхождения документа с помощью конвейера, включающего этапы
предварительной обработки изображений, OCR (Optical Character Recognition) и классификации.

## Содержание

1. [Начало работы](#начало-работы)
2. [Структура проекта](#структура-проекта)
3. [Класс Checker](#класс-Checker)
4. [Конфигурация](#конфигурация)
5. [Запуск конвейера](#запуск-конвейера)
6. [Формат результата](#формат-результата)
7. [Настройка Docker](#настройка-docker)

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
   pip install -r requirements.txt
   ```

## Структура проекта

Проект организован следующим образом:

```
DataSpike/
├── src/  
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── checker.py
│   │   ├── classifier.classifier.py
│   │   ├── detector.detector.py
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
│      ├── __init__.py
│      ├── augment_images.py
│      └── prepare_to_classify.py
├── main.py
├── Dockerfile
└── Makefile
```

## Класс Checker

Класс `MRZChecker` используется для исправления возможных ошибок в строках MRZ (Machine Readable Zone). Он выполняет
следующие функции:

1. **Методы проверки и исправления символов**:
    - `char_value(c: str) -> int`: Возвращает значение символа, где буквы преобразуются в соответствующие цифры.
    - `mrz_checksum(field: str) -> int`: Вычисляет контрольную сумму для строки MRZ.
    - `validate_field(field: str, check_digit: str) -> bool`: Проверяет, является ли строка MRZ корректной по
      контрольной сумме.
    - `try_fix_field(field: str, check_digit: str) -> str`: Попытка исправить символ в строке MRZ по контрольной сумме.

2. **Метод для исправления строки MRZ**:
    - `fix_mrz(mrz_lines: list[str]) -> list[str]`: Исправляет строку MRZ TD3 (2 строки по 44 символа) на основе
      контрольных цифр.

Этот класс помогает улучшить точность распознавания

## Конфигурация

Конфигурация хранится в файле `config/params/config.yaml`. Вы можете изменить этот файл для изменения путей к моделям,
входному изображению и других параметров.

```yaml
input:
  images:
    - /data/images/USA_99.jpg
    - /data/images/USA_9.jpg
    - /data/images/USA_1.jpg
    - /data/images/UZB_93.jpg
    - /data/images/UZB_90.jpg

model:
  detector: /src/models/prod_models/yolo/mrz_detector_v2_int8_openvino_model
  classifier: /src/models/prod_models/yolo/best_classify.pt

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

## Результат

## Результат выполнения пайплайна

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