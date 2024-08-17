FROM python:3.8

WORKDIR /echobot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY echobot/ .

CMD ["python", "./echobot.py"]
