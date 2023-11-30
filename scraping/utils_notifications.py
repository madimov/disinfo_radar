#Imports
import requests
import os
import json

#import telegram_send
#telegram_send.send(messages=["xxx"])

def send_notification(message):
    '''
    Sends notification via Telegram bot when a script has sucessfully run.

    TO DO:
        The big plan was to record also if error was encountered, and send message with error code. Not hard, but time consuming.
        Most of the work for this would be in the actual excution files.
        Would look something like:
        def error_message():
            try:
                stuff - basically all the called functions in here
            except Exception as e:
                logging.error('collection failed with following exception:')
                logging.error(e)
                return
    '''

    """
    SET_UP:
    1) Get a Telegram account (free) using your phone number

    Web: https://web.telegram.org Also download the Telegram Andriod. Of course, you want the notifications on your phone
    2) Go into settings (web or app) and set a username

    This is needed to obtain an id which your bot will use to send messages to
    3) Send a message to RawDataBot to get your id

    Just search for RawDataBot and send any message (hi will do). Take a note of your id.
    4) Create your bot (which you'll command with HTTP requests)

    Now search for BotFather and send the message /start. Help is displayed. Send the message /newbot and follow the instructions. Take a note of your token to access the HTTP API
    5) Send the API request using Python

    You could install and use telegram-send, but if you are like me and you prefer the generic library requests which will give you the experience to handle any HTTP API, this is how to do it:

    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)

    with open('./credentials/bot_token.json') as json_file:
        token_source = json.load(json_file)

    token = token_source['token']

    url = f"https://api.telegram.org/bot{token}"

    params = {"chat_id": "895750691", "text": message} ## IIRC the chat_id will need to be updated based on your bot

    r = requests.get(url + "/sendMessage", params=params)

# Test
#send_notification("Basic test successful")
