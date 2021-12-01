from __future__ import print_function
from random import random
import re
import vk_api
import requests
from bs4 import BeautifulSoup as bs
from vk_api.exceptions import AuthError
from vk_api.utils import get_random_id
import configuration as conf
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll, VkBotEvent
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
vk_session = vk_api.VkApi(token=conf.vk_private_token)
longpool = VkBotLongPoll(vk_session, conf.vk_group_id)

def main():
    print('-------------------------START-------------------------')
    for event in longpool.listen():
        print("There are new message to group", event.obj)
        sender = event.message
        user_id = sender.get('from_id')
        message = sender.get('text')
        if event.type == VkBotEventType.MESSAGE_NEW:
            if message == "Погода":
                get_weather(user_id=user_id)
            else:
                get_message_and_make_response(user_id=user_id, message_text= message)
        elif event.type == VkBotEventType.MESSAGE_REPLY:
            if message == "Погода":
                get_weather(user_id=user_id)
            else:
                get_message_and_make_response(user_id=user_id, message_text= message)        


def get_message_and_make_response(user_id, message_text):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    
    result_requests = service.spreadsheets().values().get(spreadsheetId=conf.google_spreadsheet_id, range="A2:A100").execute()
    rows_requests = result_requests.get('values', [])
    
    response_request = service.spreadsheets().values().get(spreadsheetId=conf.google_spreadsheet_id, range="B2:B100").execute()
    rows_reponse = response_request.get('values', [])
    print(rows_reponse)
    
    if not rows_requests:
        vk_session.method('messages.send', {'user_id': user_id, 'random_id': get_random_id(), 'message': "Вы знаете у меня нету настроения разговаривать с Вами 🤷‍♀️"})
    i = 0
    for value in rows_requests:
        if value[0] == message_text:
            message_response = rows_reponse[i]
            print(message_response)
            print(i)
            vk_session.method('messages.send', {'user_id': user_id, 'random_id': get_random_id(), 'message': message_response[0]})
            return
        else:
            vk_session.method('messages.send', {'user_id': user_id, 'random_id': get_random_id(), 'message': 'Ой я такого не знаю 😒'})
            return
        i = i + 1

def get_weather(user_id):
    country = 'russia'
    city = 'syktyvkar'
    request_for_weather = 'https://www.timeanddate.com/weather/{}/{}'.format(country, city)
    response = requests.get(request_for_weather)
    print(response.content)
    soup = bs(response.content, 'html')
    first_item = soup.select_one("#qlook p:nth-of-type(2)")
    strings = [string for string in first_item.stripped_strings]
    feels_like = strings[0]
    x = feels_like.replace("Feels Like:", "ощущается как ")
    vk_reponse_message = 'Знаешь Вселенная создала меня в Сыктывкаре, к сожалению, метеорологам я не доверяю, а погода сейчас ' + x
    vk_session.method('messages.send', {'user_id': user_id, 'random_id': get_random_id(), 'message': vk_reponse_message})   
                
if __name__ == '__main__':
    main()
    
