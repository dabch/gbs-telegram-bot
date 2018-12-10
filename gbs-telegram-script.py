#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import telegram
import pickle
import os
import sys
import re
import configparser

print('loading config from config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
CHAT_ID = int(config['DEFAULT']['CHATID'])
GROUP_NUM = int(config['DEFAULT']['GROUPNUM'])
BOT_TOKEN = config['DEFAULT']['TOKEN']

bot = telegram.Bot(BOT_TOKEN)

print("working with group {} and chatid {}".format(GROUP_NUM, CHAT_ID))

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
    subscribers = pickle.load(open('subscribers', 'rb'))

def send_msg(msg, chatid):
    bot.send_message(chatid, str(msg), parse_mode='Markdown')

def craft_testoutput(points, group):
    msg = ''
    for t, p in points.items():
        if t not in points_old.keys():
            msg += 'Test output for new task #' + str(t) + ':\n' + test_out[t].replace(" - ", "\n"))

def craft_summary():
    msg = '❗A new submission was corrected❗\n'
    total = 0
    for t, p in points.items():
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
    msg += 'Average: *' + str(total / len(points)) + '*\n'
    msg += 'Percentage: *' + str(total / (len(points) * 10) * 100) + '%*\n'
    return msg

rows = soup.find_all('tr')[1:]

subbed_groups = sorted(subscribers)
lastgroup = 1
for row in rows:
    cols = row.find_all('td')
    group = int(cols[4].text)
    # print(cols[0].text, int(cols[0].text) == GROUP_NUM, GROUP_NUM)
    if(len(cols) >= 4 and group in subscribers)):
        if  # TODO save if the group number has changed
        group = int(cols[4].text)
        task = int(cols[1].text)
        point = float(cols[2].text)
        points[group][task] = point
        testout = cols[3].text
        occurences = re.findall("Points received: \d\/\d", testout)
        for x in occurences:
            testout.replace(x, x + "\n")
        test_out[task] = testout

print(points)

if points[group] != points_old[group]:
    print("Difference detected. Sending message")
    msg = craft_summary()
    send_msg(msg)

sys.setrecursionlimit(10000)
pickle.dump(points, open('points.p', 'wb+'))
