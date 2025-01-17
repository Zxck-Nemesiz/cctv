FROM python:3.12.3-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get -y install poppler-utils && apt-get -y install tesseract-ocr && apt-get install ffmpeg libsm6 libxext6  -y && pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD [ "python", "cctv.py" ]