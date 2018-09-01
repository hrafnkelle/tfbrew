FROM python:3.5-slim

WORKDIR /usr/local/tfbrew

COPY *.py ./
COPY plugins plugins/
COPY config.yaml ./
COPY static static/
COPY requirements_docker.txt .
RUN pip3 install -r requirements_docker.txt

EXPOSE 8080
CMD ["python3", "tfbrew.py"]