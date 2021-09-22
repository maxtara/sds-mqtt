FROM python:alpine3.14

RUN pip install paho-mqtt pyserial

COPY cronjobs /etc/crontabs/root
COPY aqi.py /

# start crond with log level 8 in foreground, output to stderr
CMD ["crond", "-f", "-d", "8"]
