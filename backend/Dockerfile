FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install -U pip &&\
    pip install -r requirements.txt --no-cache-dir

COPY foodgram .
COPY run_app.sh .

RUN chmod +x run_app.sh
CMD ["bash", "/app/run_app.sh"]
