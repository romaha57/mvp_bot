from PIL import Image, ImageDraw, ImageFont


def build_certificate(user_id: int):
    """Добавляем текст на сертификат"""

    # открываем шаблон
    image = Image.open('../static/template_certificate.jpeg')

    # выбираем шрифт и добавляем текст
    font = ImageFont.truetype("../static/roboto/Roboto-Bold.ttf", 25)
    drawer = ImageDraw.Draw(image)
    drawer.text((50, 100), "Hello World!\nПривет мир!", font=font, fill='black')
    image.save(f'../static/{user_id}_certificate.jpg')
