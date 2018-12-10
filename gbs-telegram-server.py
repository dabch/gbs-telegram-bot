#!/usr/bin/python3

from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import configparser
import os
import pickle
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

print('loading config from config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
BOT_TOKEN = config['DEFAULT']['TOKEN']

print('loading info from subscribers.p')
subscribers = {}
if os.path.isfile('subscribers.p'):
    subscribers = pickle.load(open('subscribers.p', 'rb'))
else:
    subscribers = {}
print("subscribers: " + str(subscribers))

updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello")

def register_group(bot, update):
    msg = update.message.text.split(' ')
    id = update.message.chat_id
    try:
        groupnum = int(msg[1])
        if groupnum in subscribers:
            subscribers[groupnum].append(id)
        else:
            subscribers[groupnum] = [id]
        bot.send_message(chat_id=update.message.chat_id, text="Registered successfully for Group {}".format(groupnum))
        pickle.dump(subscribers, open('subscribers.p', 'wb+'))
    except:
        if len(msg) > 1:
            msg = msg[1] + " is not a valid group number."
        else:
            msg = "No group number provided."
        bot.send_message(chat_id=id, text= msg+"\nPlease try again: send `/register [GROUPNUM]` and replace [GROUPNUM] with the number of your GBS Homework group", parse_mode="Markdown")
        return

def unregister_group(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Unregister")

start_handler = CommandHandler('start', start)
register_handler = CommandHandler('register', register_group)
unregister_handler = CommandHandler('unregister', unregister_group)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(register_handler)
dispatcher.add_handler(unregister_handler)


updater.start_polling()