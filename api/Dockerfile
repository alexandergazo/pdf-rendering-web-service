FROM python:3.9

EXPOSE 8000

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["uwsgi", "app.ini"]
