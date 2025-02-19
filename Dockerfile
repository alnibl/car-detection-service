# образ Python 3.10 с поддержкой CUDA
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Указываем переменные окружения по умолчанию
ENV DEVICE=cpu
ENV HOST=0.0.0.0
ENV PORT=8000

# Команда для запуска приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
