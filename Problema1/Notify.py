import smtplib
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

COMMASPACE = ', '
# Define params
pngpath = ''

mailsender = "pruebas.redes.tres@gmail.com"
mailreceip = "aldom7673@gmail.com"
mailserver = 'smtp.gmail.com: 587'
password = 'pruebasRedes_3'

def send_alert_attached(subject, imagen, cuerpo = "El umbral ha sido superado, por favor, implemente las acciones correspondientes para atender el problema."):
    """ Will send e-mail, attaching png
    files in the flist.
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mailsender
    msg['To'] = mailreceip
    fp = open(pngpath + imagen + '.png', 'rb')
    img = MIMEImage(fp.read())
    fp.close()
    texto = MIMEText(cuerpo)
    msg.attach(img)
    msg.attach(texto)
    mserver = smtplib.SMTP(mailserver)
    mserver.starttls()
    # Login Credentials for sending the mail
    mserver.login(mailsender, password)

    mserver.sendmail(mailsender, mailreceip, msg.as_string())
    mserver.quit()
