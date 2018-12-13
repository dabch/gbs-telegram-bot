#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import telegram
import pickle
import os
import sys
import re
import configparser
from telegram.ext import messagequeue as mq
from telegram.ext import MessageHandler, Filters
from telegram.utils.request import Request
from telegram import TelegramError
import time

print('loading config from config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
CHAT_ID = int(config['DEFAULT']['CHATID'])
GROUP_NUM = int(config['DEFAULT']['GROUPNUM'])
BOT_TOKEN = config['DEFAULT']['TOKEN']

bot = telegram.Bot(BOT_TOKEN)

url = 'http://gbs.cm.in.tum.de/gbs_result.html'
page = urlopen(url)

soup = BeautifulSoup(page, 'lxml')

table = soup.table

points = {}
test_out = {}
points_old = {}
subscribers = {}

#extract all <br> because they seem to break BeautifulSoup
for e in soup.findAll('<br>'):
    e.extract()

if os.path.isfile('points.p'):
    print('loading points from pickle')
    points_old = pickle.load(open('points.p', 'rb'))

if os.path.isfile('subscribers.p'):
    print('Loading subscribers from pickle')
    subscribers = pickle.load(open('subscribers.p', 'rb'))

print(subscribers)


def send_msg(msg, group, mode='Markdown'):
    """
    Telegram flood limits:
    - no more than 30 messages per second total (i.e. wait at least 1/30 of a second between sending messages)
    - no more than 20 messages per minute per group (shouldn't bother us)
    """
    for sub in subscribers[group]:
        try:
            bot.send_message(sub, str(msg), parse_mode=mode)
            time.sleep(0.05) # sleep to avoid hitting the flood limit
        except TelegramError as e:
            print("Failed to send message: " + str(e))
            print(msg)
            time.sleep(2)

        

    

def craft_testoutput(group):
    testouts = []
    print(points)
    print(points_old)
    for t in points[group]:
        # print(points_old)
        # print(points_old[group])
        # print(points_old[group][t])
        if (not group in points_old) or (not t in points_old[group]) or (points_old[group][t] != points[group][t]):
            out = 'Test output for new task #' + str(t) + ':\n```' + test_out[group][t].replace(" - ", "\n") + '```'
            if len(out) > 4096:
                testouts.append('Test output for new task #%d is too long. Please refer to [http://gbs.cm.in.tum.de/gbs_result.html](http://gbs.cm.in.tum.de/gbs_result.html).' % t)
            else:
                testouts.append(out)
    return testouts

def craft_summary(group):
    msg = '❗New points for group {}❗\n'.format(group)
    total = 0
    for t, p in points[group].items():
        total += p
        msg += '#' + str(t) + ' = ' + str(p)
        if p >= 10:
            msg += ' ✅'
        elif p >= 8:
            msg += ' ⚠'
        else:
            msg += ' ❌'
        msg += '\n'
    msg += 'Total: *' + str(total) + '*\n'
    msg += 'Average: *%.2f*\n' % (total / len(points[group]))
    msg += 'Percentage: *%.2f%%*\n' % (total / (len(points[group]) * 10) * 100)
    return msg

rows = soup.find_all('tr')[1:] # cut off the heading row

subbed_groups = sorted(subscribers)
for row in rows:
    cols = row.find_all('td')
    # if len(cols) >= 4:
    #     print(cols[0].text)
    if len(cols) >= 4 and int(cols[0].text) in subbed_groups:
        group = int(cols[0].text)
        print('Found subbed group {}'.format(group))
        task = int(cols[1].text)
        point = float(cols[2].text)
        if group not in points:
            points[group] = {}
        if group not in test_out:
            test_out[group] = {}
        points[group][task] = point
        testout = cols[3].text
        # occurences = re.findall("Points received: \d\/\d", testout)
        # for x in occurences:
        #     testout.replace(x, x + "\n")
        test_out[group][task] = testout

print(points)

for group in points:
    if group in subbed_groups and (not group in points_old or points[group] != points_old[group]):
        print("Difference detected in group {}. Sending message".format(group))
        testout = craft_testoutput(group)
        for test in testout:
            send_msg(test, group, 'Markdown')
        summary = craft_summary(group)
        send_msg(summary, group)

pickle.dump(points, open('points.p', 'wb+'))
