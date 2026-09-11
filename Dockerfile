FROM python:3.14

WORKDIR /naive-bayes

COPY ./requirements.txt /naive-bayes/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /naive-bayes/requirements.txt

COPY ./app /naive-bayes/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]

