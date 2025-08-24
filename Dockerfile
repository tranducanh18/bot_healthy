FROM python:3.11-slim

RUN python -m pip install --upgrade pip

RUN apt-get update && apt-get install -y git && apt-get clean

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir \
    torch \
    transformers \
    flask \
    flask-cors \
    gunicorn

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "1"]
