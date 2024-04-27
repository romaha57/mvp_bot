from PIL import Image, ImageDraw, ImageFont


def build_certificate(user_id: int, fullname: str, course_name: str):
    """Добавляем текст на сертификат"""

    if course_name == 'СУП: Секреты Успешных Продаж':
        image = Image.open('/app/static/sales_certificate.png')

    else:
        image = Image.open('/app/static/recruter_certificate.png')

    # выбираем шрифт и добавляем текст
    font_fullname = ImageFont.truetype("/app/static/roboto/Roboto-Bold.ttf", size=70)
    font_course = ImageFont.truetype("/app/static/roboto/Roboto-Bold.ttf", size=60)
    drawer = ImageDraw.Draw(image)
    drawer.text((image.width // 2, 680), fullname, font=font_fullname, fill=(0, 0, 0), anchor="mm")
    drawer.text((image.width // 2, 850), course_name, font=font_course, fill=(0, 0, 0), anchor="mm")
    image.save(f'/app/static/certificate_{user_id}.pdf')
