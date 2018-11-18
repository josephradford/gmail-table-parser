from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import base64
import email
from os import sys
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

class DateAndRating:
    def __init__(self, date, rating):
        self.rating_date = date
        self.rating = rating

class Stock:
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.ratings = []

    def append(self, date, rating):
        self.ratings.append(DateAndRating(date, rating))

class Stocks:
    def __init__(self):
        self.stocks = []

    def append(self, stock_name, stock_rating, date):
        foundStock = False
        for stock in self.stocks:
            if stock.stock_name == stock_name:
                stock.append(date, stock_rating)
                foundStock = True
        if foundStock == False:
            stock = Stock(stock_name)
            stock.append(date, stock_rating)
            self.stocks.append(stock)

        

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

    # Call the Gmail API
    user_id = 'me'
    query = 'from:' + recipient
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

    stocks = Stocks()
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
        for row in table.find_all('tr'):
            if skippedFirst == False:
                skippedFirst = True
                continue
            columns = row.find_all('td')
            img = columns[5].findChild('img')
            starString = ""
            if (img != None) :
                if img.has_attr('alt'):
                    starString = img.attrs['alt']
            stocks.append(columns[0].get_text().strip(), starString, message_content['internalDate'])

    print(len(messages) + ' messages')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit(-1)
    main(sys.argv[1])
    