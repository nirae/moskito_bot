build:
	make -C src/generateur_attestation_sortie build
	docker build -t moskito-bot .

up:
	docker-compose up -d

down:
	docker-compose down

test: down build up

setup:
	git submodule init
	git submodule update

restart:
	docker-compose restart
