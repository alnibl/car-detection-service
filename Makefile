# Переменные
APP_PORT := 8000
DOCKER_TAG := latest
DOCKER_IMAGE := car-detection
DEVICE ?= cpu  # По умолчанию используем CPU
BASE64_IMAGE := ""

.PHONY: run
run:
	@echo "Запуск приложения на $(DEVICE)..."
	DEVICE=$(DEVICE) python3 -m uvicorn src.main:app --host=0.0.0.0 --port=$(APP_PORT)

.PHONY: predict_base64
predict_base64:
	@echo "Отправка изображения в формате base64-строки"
	curl -X POST "http://0.0.0.0:$(APP_PORT)/predict_base64/" \
		-H "Content-Type: application/json" \
		-d '{"image_base64": "$(BASE64_IMAGE)"}'

.PHONY: install
install:
	@echo "Установка зависимостей..."
	pip install -r requirements.txt

.PHONY: build
build:
	@echo "Сборка Docker-образа..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

.PHONY: run-docker
run-docker:
	@echo "Запуск Docker-контейнера на $(DEVICE)..."
	docker run -e DEVICE=$(DEVICE) -p $(APP_PORT):$(APP_PORT) $(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: run-docker-gpu
run-docker-gpu:
	@echo "Запуск Docker-контейнера на GPU..."
	docker run --gpus all -e DEVICE=cuda -p $(APP_PORT):$(APP_PORT) $(DOCKER_IMAGE):$(DOCKER_TAG)

#.PHONY: test
#test:
#	@echo "Запуск тестов..."
#	pytest tests/

.PHONY: clean
clean:
	@echo "Очистка Docker-образов..."
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: help
help:
	@echo "Использование: make [цель]"
	@echo ""
	@echo "Цели:"
	@echo "  run           - Запуск приложения локально"
	@echo "  install       - Установка зависимостей"
	@echo "  build         - Сборка Docker-образа"
	@echo "  run-docker    - Запуск Docker-контейнера на CPU"
	@echo "  run-docker-gpu - Запуск Docker-контейнера на GPU"
	@echo "  test          - Запуск тестов"
	@echo "  clean         - Удаление Docker-образов"
	@echo "  help          - Показать это сообщение"