from PIL import Image, ImageDraw, ImageFont


def build_certificate(user_id: int, fullname: str, course_name: str):
    """Добавляем текст на сертификат"""

    # открываем шаблон
    image = Image.open('/app/static/template_certificate.png')

    # выбираем шрифт и добавляем текст
    font_fullname = ImageFont.truetype("/app/static/roboto/Roboto-Bold.ttf", size=50)
    font_course = ImageFont.truetype("/app/static/roboto/Roboto-Bold.ttf", size=70)
    drawer = ImageDraw.Draw(image)
    drawer.text((500, 660), fullname, font=font_fullname, fill=(184, 134, 11))
    drawer.text((500, 810), course_name, font=font_course, fill=(184, 134, 11))
    image.save(f'/app/static/certificate_{user_id}.pdf')
