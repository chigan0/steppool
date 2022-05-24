from smtplib import SMTP_SSL,SMTP
from ssl import create_default_context,SSLCertVerificationError
from hashlib import pbkdf2_hmac

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from time import time


def send_mail(email_to, 
		title, mail_username, 
		mail_server, mail_port, 
		mail_password, message = "", 
		path_template = False, kwargs = None):	
	
	s = time()
	
	context = create_default_context()
	msg = MIMEMultipart('alternative')
	msg['Subject'] = title
	msg['From'] = mail_username
	msg['To'] = email_to
	msg['Subject'] = "Dawdawd"

	if path_template:
		html = open(f"templates/{path_template}").read()
		template = Template(html)
		part2 = MIMEText(template.render(kwargs=kwargs), 'html')

	else:
		part2 = MIMEText(message)

	msg.attach(part2)
	try:
		with SMTP_SSL(mail_server, mail_port, context=context) as server:
			server.login(mail_username, mail_password)
			server.send_message(msg)
			server.quit()

	except SSLCertVerificationError as ssl:
		print(ssl)
		
		smtpObj = SMTP(mail_server)
		smtpObj.login(mail_username, mail_password)
		smtpObj.send_message(msg)
		smtpObj.quit()

	except Exception as e:
		print(e)

	finally:
		print(time()-s)
		return

def get_password_hash(password, config):
	return pbkdf2_hmac('sha256', password.encode('utf-8'), config['SECRET_KEY'].encode('utf-8'),100000).hex()