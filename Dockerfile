FROM python:3.8.12-buster

WORKDIR /app

COPY . /app

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python", "-u", "index.py"]