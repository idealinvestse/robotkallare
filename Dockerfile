FROM python:3.12-slim

WORKDIR /app

ADD . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3003

CMD ["python3", "-m", "app.api"]
