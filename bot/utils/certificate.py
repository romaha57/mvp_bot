from PIL import Image, ImageDraw, ImageFont


def build_certificate(user_id: int, fullname: str, course_name: str):
    """Добавляем текст на сертификат"""

    # открываем шаблон
    image = Image.open('/app/static/template_certificate.jpeg')

    # выбираем шрифт и добавляем текст
    font = ImageFont.truetype("/app/static/roboto/Roboto-Bold.ttf", size=60)
    drawer = ImageDraw.Draw(image)
    drawer.text((400, 400), fullname, font=font, fill=(30, 132, 203))
    drawer.text((400, 570), course_name, font=font, fill=(30, 132, 203))
    image.save(f'/app/static/{user_id}_certificate.pdf')
