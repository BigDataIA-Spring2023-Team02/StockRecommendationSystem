FROM python:3.8.10

RUN pip install --upgrade pip

WORKDIR /FastAPI

COPY . /FastAPI

RUN pip install -r requirements.txt
RUN pip install bcrypt

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "1000", "mainapiapp:app"]
