.PHONY: clean mssql create-db fastapi build

clean:
	docker system prune -a --volumes -f

mssql:
	docker-compose up -d mssql

create-db:
	docker exec -it strom_db_app /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "diwd238490ßccaujHUdhwo1A" -Q "CREATE DATABASE strom_db" -C

fastapi:
	docker-compose up -d fastapi

# Run all
build: mssql create-db fastapi