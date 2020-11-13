FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir config_files

RUN apt-get update && apt-get install chromium chromium-l10n chromium-driver -y

ENV LC_ALL fr_FR.UTF-8

ENV TZ Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./src .

CMD [ "python", "./app.py" ]
