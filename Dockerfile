FROM attestation_generator

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir config_files

COPY ./src .

CMD [ "python", "./app.py" ]
