from fastapi import FastAPI, File, UploadFile, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO
import base64
from omegaconf import OmegaConf
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Проверка существования файла конфигурации
if not os.path.exists("config/config.yml"):
    raise FileNotFoundError("Конфигурационный файл config/config.yml не найден.")

# Загрузка конфигурации из файла
config = OmegaConf.load("config/config.yml")

# Подстановка переменных окружения
config = OmegaConf.merge(config, {
    "services": {
        "car_detector": {
            "device": os.getenv("DEVICE", "cpu")
        },
        "server": {
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8000"))
        }
    }
})

model_path = config.services.car_detector.model_path
device = config.services.car_detector.device
host = config.services.server.host
port = config.services.server.port

logger.info(f"Model path: {model_path}")
logger.info(f"Device: {device}")
logger.info(f"Host: {host}")
logger.info(f"Port: {port}")

# Загружаем модель YOLO
model = YOLO(model_path, task='detect')

@app.get("/")
async def main():
    """
    Возвращает HTML-страницу для загрузки изображения.
    """
    with open("upload.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """
    Обрабатывает изображение, загруженное через форму.
    Возвращает JSON с bounding boxes и confidence scores, а также изображение с bounding boxes.
    """
    try:
        # Логирование информации о файле
        logger.info(f"Загружен файл: {file.filename}, размер: {file.size} байт")

        # Проверка MIME-типа
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Загруженный файл не является изображением.")

        # Чтение изображения
        file_content = await file.read()
        image = Image.open(BytesIO(file_content))
        image.verify()  # Проверка, что файл является изображением
        image = Image.open(BytesIO(file_content))  # Повторное открытие после verify

        # Выполнение inference
        results = model(image)

        # Обработка результатов
        result = []
        for detection in results[0].boxes:
            x1, y1, x2, y2 = map(int, detection.xyxy[0])  # Координаты bounding box
            confidence = round(float(detection.conf[0]), 1)  # Уверенность
            class_id = int(detection.cls[0])  # Класс объекта

            result.append({
                "box": [x1, y1, x2, y2],  # Координаты bounding box
                "score": confidence,  # Уверенность
                "class": class_id  # Класс
            })

        # Наложение bounding boxes на изображение
        output_image = results[0].plot()  # Автоматически рисует bounding boxes
        output_image = Image.fromarray(output_image[..., ::-1])  # Конвертация в PIL Image

        # Конвертация изображения в base64 для отображения на HTML-странице
        img_byte_arr = BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        # Возврат JSON с результатами и изображением в base64
        return JSONResponse(content={
            "result": result,
            "image": img_base64  # Изображение с bounding boxes в формате base64
        })
    except UnidentifiedImageError:
        logger.error("Загруженный файл не является изображением.")
        raise HTTPException(status_code=400, detail="Загруженный файл не является изображением.")
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_base64/")
async def predict_base64(image_base64: str = Body(..., embed=True)):
    """
    Обрабатывает изображение, переданное в виде base64-строки.
    Возвращает JSON с bounding boxes и изображением с наложенными bounding boxes.
    """
    try:
        # Декодирование base64
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

        # Выполнение inference
        results = model(image)

        # Обработка результатов
        result = []
        for detection in results[0].boxes:
            x1, y1, x2, y2 = map(int, detection.xyxy[0])  # Координаты bounding box
            confidence = round(float(detection.conf[0]), 1)  # Уверенность
            class_id = int(detection.cls[0])  # Класс объекта

            result.append({
                "box": [x1, y1, x2, y2],  # Координаты bounding box
                "score": confidence,  # Уверенность
                "class": class_id  # Класс
            })

        # Наложение bounding boxes на изображение
        output_image = results[0].plot()  # Автоматически рисует bounding boxes
        output_image = Image.fromarray(output_image[..., ::-1])  # Конвертация в PIL Image

        # Конвертация изображения в base64
        img_byte_arr = BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        # Возврат JSON с результатами и изображением в base64
        return JSONResponse(content={
            "image": img_base64,  # Изображение с bounding boxes в формате base64
            "result": result,  # Массив с bounding boxes
        })
    except Exception as e:
        logger.error(f"Ошибка при обработке base64-изображения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=host, port=port)