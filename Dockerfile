FROM python:3

RUN echo "Europe/Berlin" > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime
RUN dpkg-reconfigure -f noninteractive tzdata

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY collector.py ./

CMD [ "python3", "./collector.py" ]
