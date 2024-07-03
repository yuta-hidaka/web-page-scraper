.PHONY: setup

up: 
	docker compose up -d
down: 
	docker compose down
run: 
	docker compose exec app bash -c "cd /app/src && python3 main.py"
diff: 
	docker compose exec app bash -c "cd /app/src && python3 diff.py"
