import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from bot.core import settings

def send_bug_report_email(subject: str, body: str, image_data: bytearray) -> bool:
    """Envia um email de relatório de bug com um anexo de imagem."""
    
    if not all([settings.EMAIL_HOST, settings.EMAIL_SENDER, settings.EMAIL_SENDER_PASSWORD, settings.EMAIL_RECEIVER]):
        print("ERRO: Variáveis de ambiente de e-mail não configuradas.")
        return False

    # Configura a mensagem
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_SENDER
    msg['To'] = settings.EMAIL_RECEIVER
    msg['Subject'] = subject
    
    # Corpo do email
    msg.attach(MIMEText(body, 'plain'))
    
    # Anexo da imagem
    image = MIMEImage(image_data, name="screenshot.jpg")
    msg.attach(image)
    
    try:
        # Conecta e envia
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls() # Habilita segurança
        server.login(settings.EMAIL_SENDER, settings.EMAIL_SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.EMAIL_SENDER, settings.EMAIL_RECEIVER, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False