from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import base64
import email
from os import sys
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

def main(recipient):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))

    try:
        df = pd.read_pickle('foo.pkl')
        query_date = int(df.index[-1][0].value / 1000000000)
    except FileNotFoundError:
        df = pd.DataFrame(index=pd.to_datetime([]))
        query_date = int(round(time.time()))

    # Call the Gmail API
    user_id = 'me'
    query = 'from:' + recipient + ' before:' + str(query_date)
    response = service.users().messages().list(userId=user_id,
                                            q=query).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query,
                                        pageToken=page_token).execute()
        messages.extend(response['messages'])

    count = 0
    for message in messages:
        msg_id = message['id']
        message_content = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
        msg_str2 = message_content['raw'].encode('ASCII')
        msg_str = base64.urlsafe_b64decode(message_content['raw'].encode('ASCII'))
        #print(message_content['payload'])
        soup = BeautifulSoup(msg_str, 'lxml')
        #soup = BeautifulSoup(msg_str2, 'lxml')
        table = soup.find_all('table')[1].find_all('table')[0].find_all('table')[7]

        skippedFirst = False
        ts = pd.to_datetime(message_content['internalDate'], unit='ms')
        print(ts)
        namesList = []
        valuesList = []
        for row in table.find_all('tr'):
            if skippedFirst == False:
                skippedFirst = True
                continue
            columns = row.find_all('td')
            img = columns[5].findChild('img')
            starString = ""
            if (img != None) :
                if img.has_attr('alt'):
                    starString = img.attrs['alt'][0]
            stock_name = columns[0].get_text().strip()
            namesList.append(stock_name)
            if len(starString) == 1:
                valuesList.append(int(starString))
            else:
                continue
            
        df2 = pd.DataFrame([valuesList], columns=namesList, index=[[ts]])
        if len(df) == 0:
            df = df2
        else:
            df = pd.concat([df, df2], axis=0, sort=True)
        
        if (count > 30):
            break # don't go overboard while testing
        count += 1
        df.to_pickle('foo.pkl')

    df.plot()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit(-1)
    main(sys.argv[1])
    