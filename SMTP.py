from Account import *

import smtplib

from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """
    
    names = []
    emails = []
    with open(filename, mode='r') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails

def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.
    """
    
    with open(filename, 'r') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def send_message(sender=MY_ADDRESS, destination='kixlab.rally@gmail.com', subject='', content='Hello Murmur'): 
    # set up the SMTP server
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    names = [sender]
    emails = [destination]

    message_template = read_template('message.txt')
    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        # setup the parameters of the message
        msg['From']=sender
        msg['To']=destination
        msg['Subject']=subject

        # todo change with original sender
        msg.add_header('reply-to', "asdf" + ' <' + "test@mit.edu" + '>')
        # msg['From'] = "test@mit.edu" + ' <' + MY_ADDRESS + '>'
        # msg.add_header('From', "qwer" + ' <' + "test@mit.edu" + '>')

        # add in the message body
        msg.attach(MIMEText(content, 'plain'))
        
        # send the message via the server set up earlier.
        s.sendmail(sender, destination,msg.as_string())
        del msg

    # Terminate the SMTP session and close the connection
    s.quit()
    
if __name__ == '__main__':
    # send_message(subject="qwer")
    pass