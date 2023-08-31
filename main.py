from __future__ import print_function

import os.path
import base64
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from googlesearch import search

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/calendar.readonly', 'https://mail.google.com/']

email_send = True
email_delete = True

def quickstart():
    creds = None
    token_json = '<ADD TOKEN JSON FILE PATH>'
    cred_json = '<ADD CREDENTIALS JSON PATH>'
    
    # The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_json):
        creds = Credentials.from_authorized_user_file(token_json, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_json SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_json, 'w') as token:
            token.write(creds.to_json())
    return creds


def emailDataGather():
    rows_to_add = []
    
    #get creds
    creds = quickstart()
    
    #get to gmailAPI
    service = build('gmail', 'v1', credentials=creds)

    # Retrieve a list of messages in the inbox
    results = service.users().messages().list(userId='me', q='in:inbox').execute()
    messages = results.get('messages', [])
    
    #keywords that, if present in sender, will allow the email to get looked at
    #ex: keywords = ["LinkedIn","Monster","Handshake","Glassdoor","Indeed"]
    keywords = ['<ADD KEYWORDS HERE>']

    # Print each message subject and sender
    
    if not messages:
        print('No messages found in the inbox.')
    else:
        
        #for all messages in email...
        for i, message in enumerate(messages):
            
            #get the first message
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            if 'payload' in msg and 'headers' in msg['payload']:
                
                #get important information
                headers = msg['payload']['headers']
                subject = '(no subject)'
                sender = '(no sender)'
                body = '(no body)'
                date = '(no date)'
                date_obj = datetime.now()
                for header in headers:
                    
                    #set each value (that is present)
                    if header['name'] == 'Subject':
                        subject = header['value']
                        if subject == None:
                            subject = '(no subject)'
                    elif header['name'] == 'From':
                        sender = header['value']
                    elif header['name'] == 'Body':
                        body = header['value']
                    elif header['name'] == 'Date':
                        #for some reason, many different options for how dates can show up. This was my attempt to standarize them
                        date_string = header['value'].replace("  "," ")
                                                date_options = ['%a, %d %b %Y %H:%M:%S', '%a, %d %b %Y %H:%M:%S %z', '%d %b %Y %H:%M:%S', '%d %b %Y %H:%M:%S %z']
                        for date_strf in date_options:
                            try:
                                date_obj = datetime.strptime(" ".join(date_string.split(" ")[0:5]), date_strf)
                                break
                            except:
                                continue
                date = date_obj.strftime("%m/%d/%y")
                
                #if the keywords are in the sender, meaning these are the emails from the job companies
                if any(keyword in sender for keyword in keywords):
                    
                    #shows that this email exists on the terminal
                    print("! " + sender[0:10] +" " + subject[0:10], end = "")
                    
                    #there appears to be two ways a message can be loaded, not sure why
                    if 'parts' in msg['payload']:
                        # Retrieve the message body from the first part
                        data1 = msg['payload']['parts'][0]['body']['data']
                        body = base64.urlsafe_b64decode(data1).decode('utf-8')
                    else:
                        # Retrieve the message body from the whole message
                        data1 = msg['payload']['body']['data']
                        body = base64.urlsafe_b64decode(data1).decode('utf-8')
                    
                    # Parse the HTML body using BeautifulSoup
                    soup = BeautifulSoup(body, 'html.parser')
                    
                    # Print the message details and the parsed body
                    data = soup.get_text()
                    
                    #One type of LinkedIn Email --> LinkedIn Job Alerts
                    if "LinkedIn Job Alerts" in sender:
                        #list of things that were left in my parsing that I did not want, some of which could be turned on and in future versions
                        #(i.e visible_alum_connection = True/False
                            #visible_connections = True/False)

                        #how it works: 
                            #1) parses information
                            #2) left with JUST the 4 data points DATE, JOB, COMPANY, LOCATION, (LINK?)
                        linkedIn_blacklist = ['View job:\r', 'alumni\r', 'alum\r', 'This company is actively hiring\r', '          \r', 'connections\r', 'connection\r', 'Apply with resume & profile\r']
                        try:
                            #attempt at parsing, please HELP!!!
                            for job in data.split('---------------------------------------------------------')[:-1]:
                                job = job.split("\n")[3:-2]
                                final_job_list = [date]
                                for job_param in job:
                                    inIt = False
                                    for word in linkedIn_blacklist:
                                        if word in job_param:  #this is here becuase number company alumni causes number change
                                            inIt = True
                                    if job_param not in linkedIn_blacklist and not inIt:
                                        final_job_list.append(job_param.replace('\r','').strip())
                                
                                #pre-defined rows_to_add holds ALL job information
                                rows_to_add.append(final_job_list)
                            
                            #if works, will remove from inbox
                            if email_delete: 
                               service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['INBOX']}).execute()
                        
                        except Exception as e:
                            print('LinkedIn Error', e)
                            #if fail, email_send is true, will reply to email with 'add to list'
                            if email_send: 
                                reply_to_message(message['id'], 'add to list')


                    if "Handshake" in sender:
                        #parsing attempt for Hanshake Email
                        try:
                            data = data.split('\r\n')
                            new_list = []
                            #things that were hard to remove in other ways
                            handshake_blacklist = ["", "•", "\xa0", " ", "Search all jobs"]
                            for ele in handshake_blacklist:
                                while ele in data:
                                    data.remove(ele)
                            for i in range(0, len(data), 3):
                                new_list.append(data[i:i+3])
                            
                            #left with just elements needed for job Stuff. no link so ADD is there
                            for element in new_list:
                                rows_to_add.append([date] + element + ['ADD'])
                            
                            #if works, will remove from inbox
                            if email_delete: 
                                service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['INBOX']}).execute()
                        except Exception as e:
                            print('Handshake Error', e)
                            #will send email if error and email_send is true
                            if email_send: 
                               reply_to_message(message['id'], 'add to list')

                #glassDoor changed their HTML so it is not updated
'''
                    if "Glassdoor" in sender:
                        print("!", end = "")
                        try:
                            import re
                            job_tables = soup.find('table', class_=lambda x: x and 'css-hprvaa'in x).find_all('td', class_=lambda x: x and "hqhui1" in x)
                            print(len(job_tables))
                            for i in job_tables:
                                try:
                                    job_element1 = i.find("span",class_=lambda x: x and "css-1obn1y" in x)
                                    print(job_element1)
                                    job_element = job_element1.find("a",class_=lambda x: x and "css-ytumd6" in x)
                                    print(job_element)
                                    span_element = i.find("span",class_=lambda x: x and "css-y6uhzt" in x)
                                    loca_element = i.find("span",class_=lambda x: x and "css-1paj1yl" in x)
                                except Exception as e:
                                    print(job_element[:2] if job_element else None, span_element[:2] if span_element else None, loca_element.text.strip()[:2] if loca_element else None)
                                link_element = next(search(f'{job_element} {span_element} {loca_element}', tld="com", num=1, stop=1, pause=1))
                                if job_element == None or span_element == None or loca_element == None or link_element == None:
                                    print("there is a None element")
                                    continue
                                job = job_element.text.strip()
                                company = span_element.text.strip().replace(' -', '')
                                location = loca_element.text.strip()
                                link = link_element
                                print("AAAAA", job, "BBBBB", company, "CCCCC", location)
                                rows_to_add.append([date, job, company, location,link])
                                if email_send: 
                                    service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['INBOX']}).execute()
                        except Exception as e:
                            print('Glassdoor Error', e)
                            if email_send: 
                                reply_to_message(message['id'], 'add to list')
'''
                    
                    if "Indeed Job Feed" in sender:
                        #parsing attempt
                        try:
                            data = data.split("\n\n")[1]
                            data_new = data.split("\n    \n")
                            for data_val in data_new:
                                try:
                                    
                                    datum = data_val.split("\n")
                                    #this is the data (much more clean, would like others to look more like this)
                                    name = datum[0].strip()
                                    comp = datum[1].split(" - ")[0].strip()
                                    loca = datum[1].split(" - ")[1].strip()
                                    for i in range(len(datum)):
                                        if "http" in datum[i]:
                                            link = datum[i].strip()
                                        else:
                                            #I get the link here by searching on google
                                            link = link_element = next(search(f'{name} {comp} {loca}', tld="com", num=1, stop=1, pause=1))
                                    rows_to_add.append([date, name, comp, loca, link])
                                    #if works, remove from inbox
                                    if email_delete: 
                                        service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['INBOX']}).execute()

                                except:
                                    _=0

                        except Exception as e:
                            print('Indeed Job Feed error', e)
                            #if failed, send email to add to list
                            if email_send: 
                                reply_to_message(message['id'], 'add to list')



                    elif "Indeed" in sender:
                        #attempt to parse indeed
                        try:
                            indeed_blacklist = ['Responsive employer',  'Just posted', 'Easily apply', '']
                            data = data.split('\n\n')
                            for i in data:
                                j = i.split('\n')
                                for word in indeed_blacklist:
                                    while word.strip() in j:
                                        j.remove(word)
                                if len(j) == 5:
                                    job = j[0].strip()
                                    comp = j[1].split(" - ")[0].strip()
                                    loca = j[1].split(" - ")[1].strip()
                                    link = j[4].strip()
                                    rows_to_add.append([date, job, comp, loca, link])
                            if email_send: 
                               service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['INBOX']}).execute()
                        except Exception as e:
                            print('Indeed error', e)
                            if email_send: 
                                reply_to_message(message['id'], 'add to list')
    return rows_to_add

#attempt to format list based on blacklist and duplicates (it failed)
#would like for it to not include duplicates that are already in the spreadsheet
def formatList(OGlist):
    new_list = []
    add = True
    job_words_blacklist = ["<add strings here>"]
    location_blacklist = ["<add strings here>"]
    for job in OGlist:
        date = job[0]
        name = job[1]
        comp = job[2]
        loca = job[3]
        link = job[4]

        for word in name_words_blacklist:
            if word in name:
                add = False
        for word in location_blacklist:
            if ", " + word in loca:
                add = False
        if " -" in job[2]:
            job[2].replace(" -", "")
        if job in new_list:
            add = False
        if add:
            new_list.append(job)

    return new_list



#adds values to list
def sheetAccess(new_values):
    #formats list with function above
    formatList(new_values)
    #if list empty/NA, dont add to spreadsheet
    if new_values == [] or new_values == None:
        return None
    print("adding values", end = "\r")
    
    #needed to place the data
    SPREADSHEET_ID = '<ADD SPREADSHEET ID>'
    SHEET_NAME = '<ADD SHEET NAME>'
    range_name = f'{SHEET_NAME}!A:E'

    #creds again
    creds = quickstart()
    #access sheetsAPI
    service = build('sheets', 'v4', credentials=creds)
    
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=range_name).execute()
    #find the FIRST empty row
    values = result.get('values', [])
    highest_empty_row = len(values) + 1
    for i, row in enumerate(values, 1):
        if not row:
            highest_empty_row = i
            break
    add_values = []
    add = True
    # I believe this is supposed to stop duplicates
    for job in new_values:
        for i, row in enumerate(values, 1):
            if job[1:3] == row[1:3]:
                add = False
        if add:
            add_values.append(job)
    # Add the value to the highest empty row or add a new row at the end
    print("just about to add values", end = "\r")
    if highest_empty_row > len(values):
        range_name = f'{SHEET_NAME}!A{highest_empty_row}'
        body = {'values': add_values}
        result = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=range_name, valueInputOption='RAW', body=body).execute()
        print(f'Added values to row {highest_empty_row}')
    else:
        range_name = f'{SHEET_NAME}!A{highest_empty_row}'
        body = {'values': add_values}
        result = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=range_name, valueInputOption='RAW', body=body).execute()
        print(f'Added values to row {highest_empty_row}, add to INTERNSHIP')



def reply_to_message(message_id, words_to_say):
    # Authenticate and build the Gmail API client
    creds = Credentials.from_authorized_user_file('tokenJaredcoh.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    # Get the original message
    message = service.users().messages().get(userId='me', id=message_id).execute()

    # Email to send to
    sender = '<ADD YOUR EMAIL HERE>'
    # Construct the message to send
    message_body = f"To: {sender}\nSubject: Re: {message['payload']['headers'][3]['value']}\n\n{words_to_say}"
    encoded_body = base64.urlsafe_b64encode(message_body.encode('utf-8')).decode('utf-8')
    reply_message = service.users().messages().send(
        userId='me',
        body={'raw': encoded_body, 'threadId': message_id},
    ).execute()
    print(message_id, "--> replied with", words_to_say)
