import PyPDF2
import pdfkit

from bot.users.models import Users


def from_html_to_pdf(html_text: str, image_url: str, user_chat_id: int, username: str):
    """Преобразовывает html в pdf (для сертификата)"""
    html_text_with_param = html_text.format(
        image_url,
        username

    )

    pdfkit.from_string(html_text_with_param, f'./{user_chat_id}_certificate.pdf')
    format_pdf(user_chat_id)


def format_pdf(user_chat_id):
    pdf_path = f'./{user_chat_id}_certificate.pdf'

    pdf = PyPDF2.PdfReader(pdf_path)
    page0 = pdf.pages[0]
    page0.mediabox.upper_right = (1280, 904)
    page0.scale_by(0.7) # float representing scale factor - this happens in-place
    writer = PyPDF2.PdfWriter()  # create a writer to save the updated results
    writer.add_page(page0)
    with open(pdf_path, 'wb+') as f:
        writer.write(f)

# res = from_html_to_pdf(f"""<html lang="ru-RU" class="no-js" itemscope itemtype="https://schema.org/WebPage">
# <head>
#   <meta charset="UTF-8" />
# </head>
# <body style="background-image: url('https://zbots.samoletplus.ru/uploads/sertifikat-botov-gorizont-01_562d5.jpg');background-repeat: no-repeat; background-attachment: fixed; background-size: 100% 100%;font-family:Calibri, sans-serif;">
# <div style="padding-top:300px; text-align:center; font-size:35px; color:#1d85c7;"><b></b></div>
# <div style="padding-top:50px; text-indent:80px; font-size:40px;color:black;color:#1d85c7;"><b>%NAME%</b></div>
# <div style="padding-top:100px; text-indent:80px; font-size:40px; color:black;color:#1d85c7;"><b>Агент по работе с недвижимостью</b></div>
# </body>
# </html>""")