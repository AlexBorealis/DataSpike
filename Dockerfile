FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy application
COPY main.py .
COPY src ./src

# run service
CMD ["python", "-m", "main"]