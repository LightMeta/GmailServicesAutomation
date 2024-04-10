from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle,os, base64, sqlite3

'''
There can be multiple scopes , that can be viewed in documentation,such as modify, readonly etc.I am moving forward with readonly since we need emails data
and don't want to change it. '''

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def bytes_to_kb(bytes):
    ''' Conversion of Email Size (byes--->kb ) for Good User Experience '''
    kb = bytes / 1024
    return kb


def authenticate_gmail():
    ''' Authentication part Using GCP ,
        Creation of Pickle file from JSON '''    
    
    creds = None
    #instead of text , i have used pickle file to load my credentials because of security'
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    ' refresh the creds and create again in case of corrupted file or old creds'
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
    return creds

def fetch_from_subject_and_date(headers):
        '''  Retreiving FROM ,EMAIL SUBJECT and Date from 
                GCP gmail API response headers        '''
        for header in headers:
            try:
                if header['name'] == 'From':
                    from_address = header['value']
                elif header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'Date':
                    received_datetime = header['value']
            except:
                from_address,subject,received_datetime = None,None,None

        return from_address,subject,received_datetime    

def fetch_decoded_body(message_body):
    ''' Retrival of Encoded UTF-8 body , converting to text.'''

    if 'data' in message_body:
        message_data = message_body['data']
        message_text = base64.urlsafe_b64decode(
            message_data).decode('utf-8')
        return message_text

def fetch_emails_information():
    ''' 
        Retrival of Emails in a batch of 50 emails at a time 
    '''
    # try:
        # authentication part
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # giving lebel as Inbox only as of now
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print('As of now 0 emails  in Inbox')
        return []
    
    # Saving data in readale format from respanse payload. List of tuples , where each tuple is organized email row.
    emails_info = []

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = msg.get('payload', {}).get('headers', [])

        for header in headers:
            from_address,subject,received_datetime = fetch_from_subject_and_date(headers)
        
        payload = msg.get('payload')
        
        try:
            payload = payload['parts'][0]
        except:
            pass
        
        if payload:
            message_text = fetch_decoded_body(payload.get('body', {}))

        email_info_dic = {
            'id': message['id'],
            'from': from_address,
            'subject': subject,
            'message': message_text,
            'received_datetime': received_datetime,
            'sizeinkbs':bytes_to_kb(msg['sizeEstimate'])
        }
        
        emails_info.append(email_info_dic)

    return emails_info
    # except:
    #     print(f'An error occurred while fetching emails')
    #     return []

def create_table(curr):
    '''
    Creation of Table in case if it's not existing
    '''
    curr.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            from_address TEXT,
            subject TEXT,
            message TEXT,
            received_datetime TEXT,
            emailsize   INTEGER
        )
    ''')

def create_connection_db():
    '''Create connection to db'''
    conn = sqlite3.connect('email_database.db')
    cursor = conn.cursor()
    return conn,cursor

def store(data,conn,curr):
        ''' Running sql query on sqlite and dsaving the data.'''
        for email_info in data:
            curr.execute('''
                INSERT OR REPLACE INTO emails (id, from_address, subject, message, received_datetime,emailsize)
                VALUES (?, ?, ?, ?, ?,?)
            ''', (email_info['id'], email_info['from'], email_info['subject'], email_info['message'], email_info['received_datetime'],email_info['sizeinkbs']))
        conn.commit()
        conn.close()
        print('Emails stored in the database.')

def main_insert():
    '''Creating table'''
    conn,curr = create_connection_db()
    create_table(curr)

    ''' Email data'''
    email_data = fetch_emails_information()
    if email_data:
            store(email_data,conn,curr)

    return "SUCCESSFULLY INSERTED DATA"




