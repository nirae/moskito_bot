build:
	docker build -t moskito-bot .

up:
	docker-compose up -d

down:
	docker-compose down

test: down build up

restart:
	docker-compose restart
