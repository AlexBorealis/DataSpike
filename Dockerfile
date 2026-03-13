FROM python:3.10-slim

# system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libgl1 libglib2.0-0 \
    procps htop vim curl wget net-tools iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv /home/appuser/.venv
ENV PATH="/home/appuser/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/

# install python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy application
COPY main.py .
COPY src ./src

# run service
CMD ["python", "-m", "main"]