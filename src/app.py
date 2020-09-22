#! /usr/bin/env python3

from Bot import Bot
import requests
from datetime import datetime
import os

token = os.environ['TELEGRAM_TOKEN']
chat_id = os.environ['TELEGRAM_GROUP_ID']

bot = Bot(token, chat_id)

@bot.add_command(name='hello')
def hello(update, context):
    update.message.reply_text('Bzz Bzz ... Hello %s!' % update.message.from_user.first_name)

@bot.add_command(name='heure')
def hour(update, context):
    paris = requests.get('http://worldtimeapi.org/api/timezone/Europe/Paris').json()
    montreal = requests.get('http://worldtimeapi.org/api/timezone/America/Montreal').json()
    paris = datetime.fromisoformat(paris['datetime'])
    montreal = datetime.fromisoformat(montreal['datetime'])
    update.message.reply_text('Il est %dh%d chez Emma\nIl est %dh%d chez les autres' % (montreal.hour, montreal.minute, paris.hour, paris.minute))

# @bot.add_command(name='jobs')
# def jobs(update, context):
#     print(bot.jobs.jobs())

# @bot.daily(time='22:51:00')
# def bzz(context):
#     print("send!")
#     bot.send_message("BzzZZZZZ", chat_id)

# @bot.repeat(interval=60)
# def bzz_minutes(context):
#     print("send!")
#     bot.send_message("Bzz", chat_id)

if __name__ == "__main__":
    bot.start()
