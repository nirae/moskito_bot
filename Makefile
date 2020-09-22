build:
	docker build -t moskito-bot .

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart
