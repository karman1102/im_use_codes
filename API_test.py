# gmail api
from __future__ import print_function

import base64
import mimetypes
import os.path
import pickle
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import dateutil.parser as parser
from apiclient import errors
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']


# -------------------- fetch credentials for service ------------------------- #

def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    return service


def create_Message_with_attachment(sender, to, subject, message_text_plain, message_text_html, attached_file):
    """Create a message for an email.

    message_text: The text of the email message.
    attached_file: The path to the file to be attached.

    Returns:
    An object containing a base64url encoded email object.
    """

    # An email is composed of 3 part :
    # part 1: create the message container using a dictionary { to, from, subject }
    # part 2: attach the message_text with .attach() (could be plain and/or html)
    # part 3(optional): an attachment added with .attach()

    # Part 1
    message = MIMEMultipart()  # when alternative: no attach, but only plain_text
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Part 2   (the message_text)
    # The order count: the first (html) will be use for email, the second will be attached (unless you comment it)
    message.attach(MIMEText(message_text_html, 'html'))
    message.attach(MIMEText(message_text_plain, 'plain'))

    # Part 3 (attachment)
    # # to attach a text file you containing "test" you would do:
    # # message.attach(MIMEText("test", 'plain'))

    # -----About MimeTypes: It tells gmail which application it should use to read the attachment (it acts like an
    # extension for windows). If you dont provide it, you just wont be able to read the attachment (eg. a text)
    # within gmail. You'll have to download it to read it (windows will know how to read it with it's extension).

    # -----3.1 get MimeType of attachment
    # option 1: if you want to attach the same file just specify it’s mime types

    # option 2: if you want to attach any file use mimetypes.guess_type(attached_file)

    my_mimetype, encoding = mimetypes.guess_type(attached_file)

    # If the extension is not recognized it will return: (None, None)
    # If it's an .mp3, it will return: (audio/mp3, None) (None is for the encoding)
    # for unrecognized extension it set my_mimetypes to  'application/octet-stream' (so it won't return None again).
    if my_mimetype is None or encoding is not None:
        my_mimetype = 'application/octet-stream'

    main_type, sub_type = my_mimetype.split('/', 1)  # split only at the first '/'
    # if my_mimetype is audio/mp3: main_type=audio sub_type=mp3

    # -----3.2  creating the attachment you don't really "attach" the file but you attach a variable that contains
    # the "binary content" of the file you want to attach

    # option 1: use MIMEBase for all my_mimetype (cf below)  - this is the easiest one to understand
    # option 2: use the specific MIME (ex for .mp3 = MIMEAudio)   - it's a shorcut version of MIMEBase

    # this part is used to tell how the file should be read and stored (r, or rb, etc.)
    if main_type == 'text':
        print("text")
        temp = open(attached_file, 'r')  # 'rb' will send this error: 'bytes' object has no attribute 'encode'
        attachment = MIMEText(temp.read(), _subtype=sub_type)
        temp.close()

    elif main_type == 'image':
        print("image")
        temp = open(attached_file, 'rb')
        attachment = MIMEImage(temp.read(), _subtype=sub_type)
        temp.close()

    elif main_type == 'audio':
        print("audio")
        temp = open(attached_file, 'rb')
        attachment = MIMEAudio(temp.read(), _subtype=sub_type)
        temp.close()

    elif main_type == 'application' and sub_type == 'pdf':
        temp = open(attached_file, 'rb')
        attachment = MIMEApplication(temp.read(), _subtype=sub_type)
        temp.close()

    else:
        attachment = MIMEBase(main_type, sub_type)
        temp = open(attached_file, 'rb')
        attachment.set_payload(temp.read())
        temp.close()

    # -----3.3 encode the attachment, add a header and attach it to the message
    # encoders.encode_base64(attachment)  #not needed (cf. randomfigure comment)
    # https://docs.python.org/3/library/email-examples.html

    filename = os.path.basename(attached_file)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)  # name preview in email
    message.attach(attachment)

    ## Part 4 encode the message (the message should be in bytes)
    message_as_bytes = message.as_bytes()  # the message should converted from string to bytes.
    message_as_base64 = base64.urlsafe_b64encode(message_as_bytes)  # encode in base64 (printable letters coding)
    raw = message_as_base64.decode()  # need to JSON serializable (no idea what does it means)
    return {'raw': raw}


def get_attachments(service, user_id, msg_id, store_dir):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        for part in message['payload']['parts']:
            if part['filename'] and part['body'] and part['body']['attachmentId']:
                attachment = service.users().messages().attachments().get(id=part['body']['attachmentId'],
                                                                          userId=user_id, messageId=msg_id).execute()

                file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))
                path = ''.join([store_dir, part['filename']])

                f = open(path, 'wb')
                f.write(file_data)
                f.close()
    except Exception as error:
        print('An error occurred: %s' % error)


# def create_message(sender, to, subject, message_text):
#     """Create a message for an email.
#
#     Args:
#       sender: Email address of the sender.
#       to: Email address of the receiver.
#       subject: The subject of the email message.
#       message_text: The text of the email message.
#
#     Returns:
#       An object containing a base64url encoded email object.
#     """
#     message = MIMEText(message_text)
#     message['to'] = to
#     message['cc'] = 'karman.singh@indiamart.com'
#     message['from'] = sender
#     message['subject'] = subject
#     message['In-Reply-To'] = '177483d828463646'
#     message['References'] = '177483d828463646'
#     return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

# --------------- code to create message in the same thread ----------------------------
def create_message(sender, to, subject, thread_id, message_text, service):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    if type(message_text) != str:
        message_text = str(message_text)

    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw, 'threadId': thread_id}
    messages = service.users().messages()
    send = messages.send(userId='me', body=body).execute()


def create_message2(sender, to, cc, bcc, subject, message_text, thread, service):
    message = MIMEMultipart()
    message['to'] = to
    if cc:
        message['cc'] = cc
    if bcc:
        message['bcc'] = bcc
    message['from'] = sender
    message['subject'] = subject
    msg = MIMEText(message_text, 'html')
    message.attach(msg)
    output = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
    if thread:
        output['threadId'] = thread
    messages = service.users().messages()
    messages.send(userId='me', body=output).execute()


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print("An error occurred:", error)


def create_message_label(remove_label=None, add_label=None):
    """Create object to update labels.

    Returns:
    A label update object.
    """
    return {'removeLabelIds': remove_label, 'addLabelIds': add_label}


# ---------------- modifying labels -----------------------#
def add_label_to_email(service, user_id, msg_id, msg_labels):
    """Modify the Labels on the given Message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The id of the message required.
    msg_labels: The change in labels.

    Returns:
    Modified message, containing updated labelIds, id and threadId.
    """
    try:
        message = service.users().messages().modify(userId=user_id,
                                                    id=msg_id,
                                                    body=msg_labels).execute()

        label_ids = message['labelIds']

        print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
        return message
    except Exception as error:
        print('An error occurred: %s' % error)


def get_message_content(message_list, service):
    message_list = message_list[:2]
    for msg in message_list:
        temp_dict = {}
        m_id = msg['id']  # get id of individual message
        message = service.users().messages().get(userId='me', id=m_id, format='full').execute()  # fetch the message using API
        print(message)
        payld = message['payload']  # get payload of the message
        headr = payld['headers']  # get header of the payload


        for one in headr:  # getting the Subject
            if one['name'] == 'Subject':
                msg_subject = one['value']
                temp_dict['Subject'] = msg_subject
            else:
                pass

        for two in headr:  # getting the date
            if two['name'] == 'Date':
                msg_date = two['value']
                date_parse = (parser.parse(msg_date))
                m_date = (date_parse.date())
                temp_dict['Date'] = str(m_date)
            else:
                pass

        for three in headr:  # getting the Sender
            if three['name'] == 'From':
                msg_from = three['value']
                temp_dict['Sender'] = msg_from
            else:
                pass

        temp_dict['Snippet'] = message['snippet']  # fetching message snippet

        try:
            # Fetching message body
            part_body = payld['body']
            part_data = part_body['data']  # fetching data from the body
            clean_one = part_data.replace("-", "+")  # decoding from Base64 to UTF-8
            clean_one = clean_one.replace("_", "/")  # decoding from Base64 to UTF-8
            clean_two = base64.b64decode(bytes(clean_one, 'UTF-8'))  # decoding from Base64 to UTF-8
            soup = BeautifulSoup(clean_two, "lxml")
            mssg_body = soup.body()
            # mssg_body is a readible form of message body
            # depending on the end user's requirements, it can be further cleaned
            # using regex, beautiful soup, or any other method
            temp_dict['Message_body'] = mssg_body

        except Exception as e:
            # print(e, message)
            pass

        # print(temp_dict)

def main():
    service = get_service()

    results = service.users().labels().list(userId='me').execute()
    # is:unread works
    # message = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
    # message_list = message['messages']
    # get_message_content(message_list, service)
    message = service.users().messages().get(userId='me', id='17859b8510893fb5',
                                             format='full').execute()  # fetch the message using API
    print(message)
    # inbox = service.users().messages().get(userId='me', id='17781186b361b22c', format='raw').execute()
    # label = create_message_label(remove_label=['UNREAD'])
    # add_label_to_email(service, 'me', '17769bf529ecff26', label)
    inbox = service.users().threads().get(userId='me', id='17859b8510893fb5', format='full').execute()
    print(inbox)
    # get_attachments(service, 'me', '17762287ad70ee03', 'C:/Users/karma/Downloads/APPLICATION')
    # create_message('karmanminocha@gmail.com', 'karman.singh@indiamart.com, garg.aman@indiamart.com',
    #                'testing attachment', '17762287ad70ee03', 'testing reply',
    #                service=service)
    # create_message2('karmanminocha@gmail.com', 'karman.singh@indiamart.com', None, None, 'testing attachment', 'testing reply_final', '17762287ad70ee03', service)
    #
    # print(len(message['messages']))
    # print(message_list, '\n', inbox)

    # labels = results.get('labels', [])

    # if not labels:
    #     print('No labels found.')
    # else:
    #     print('Labels:')
    #     for label in labels:
    #         print(label['name'])
    #
    # message64 = create_message('karmanminocha@gmail.com', 'garg.aman@indiamart.com', 'testing API',
    #                            'testing reply')
    # message64_attach = create_Message_with_attachment('me', 'karman.singh@indiamart.com', 'testing attachment', 'test',
    #                                                   r'Hi<br/>Html <b>hello</b>', r'C:\Users\karma\Downloads\IndiaMart\server-error.png')
    # send_message(service, 'me', message64_attach)


if __name__ == '__main__':
    main()
