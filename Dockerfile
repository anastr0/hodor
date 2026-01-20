FROM python:3.11-slim-bookworm


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./api /code/app 
COPY ./hodor /code/hodor

RUN ls

RUN echo "Build is running"

CMD ["fastapi", "run", "app/main.py", "--port", "5000"]

EXPOSE 5000
