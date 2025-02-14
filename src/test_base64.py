import requests
import base64
from io import BytesIO
from PIL import Image

# Закодируйте изображение в base64
with open("data/vid_4_2140.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# Отправка запроса
url = "http://127.0.0.1:8000/predict_base64/"
payload = {"image_base64": encoded_string}
response = requests.post(url, json=payload)

# Вывод результата
print(response.json())


# Декодирование base64-строки
#decoded_image = base64.b64decode(encoded_string)
# Преобразование в изображение
#image = Image.open(BytesIO(decoded_image))
# Сохранение изображения для проверки
#image.save("decoded_image.jpg")