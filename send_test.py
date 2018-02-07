#send html email

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import smtplib

msg = MIMEMultipart('alternative')
msg['From'] = formataddr((str(Header('MyWebsite', 'utf-8')), 'from@mywebsite.com'))
msg['To'] = 'soyapark2535@gmail.com'

html = "email contents"

# Record the MIME types of text/html.
msg.attach(MIMEText(html, 'html'))

# Send the message via local SMTP server.
s = smtplib.SMTP('localhost')

# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail('from@mywebsite.com', msg['To'], msg.as_string())
s.quit()