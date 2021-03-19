#! /usr/bin/env python3

from Bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
import requests
from datetime import datetime
import os
import yaml
import logging

from conversation import states, FIRST_NAME, ask_context

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)

attestation_config_file = os.getcwd() + "/config_files/{chat_id}_config.yml"

token = os.environ['TELEGRAM_TOKEN']
chat_id = os.environ['TELEGRAM_GROUP_ID']

bot = Bot(token, chat_id)

@bot.add_command(name='hello')
def hello(update, context):
    logging.info("[%d] /hello called" % update.message.from_user.id)
    update.message.reply_text('Bzz Bzz ... Hello %s!' % update.message.from_user.first_name)

@bot.add_command(name='heure')
def hour(update, context):
    logging.info("[%d] /heure called" % update.message.from_user.id)
    paris = requests.get('http://worldtimeapi.org/api/timezone/Europe/Paris').json()
    montreal = requests.get('http://worldtimeapi.org/api/timezone/America/Montreal').json()
    paris = datetime.fromisoformat(paris['datetime'])
    montreal = datetime.fromisoformat(montreal['datetime'])
    update.message.reply_text('Il est %dh%d chez Emma\nIl est %dh%d chez les autres' % (montreal.hour, montreal.minute, paris.hour, paris.minute))


@bot.conversation(name='attestation', states=states, cancel_text="Goodbye!")
def attestation(update, context):
    logging.info("[%d] /attestation called" % update.message.from_user.id)
    file = attestation_config_file.format(chat_id=update.message.from_user.id)
    if not os.path.isfile(file):
        logging.info("[%d] config file not found. starting questions" % update.message.from_user.id)
        update.message.reply_text("""Ah ! Je n'ai pas encore les informations te concernant.
Réponds à mes quelques questions et tu n'auras plus jamais à le faire !

Je stockerai tes informations dans un fichier de configuration. Tu peux quitter la conversation à tout moment en envoyant /stop. Tu peux aussi supprimer ton fichier de configuration avec la commande /oublier.

Les attestations sont supprimées directement après l'envoi.

Commençons, quel est ton prénom ?""")
        return FIRST_NAME
    logging.info("[%d] config file %s found" % (update.message.from_user.id, file))
    return ask_context(update, context)

@bot.add_command(name='oublier')
def oublier(update, context):
    logging.info("[%d] /oublier called" % update.message.from_user.id)
    filename = attestation_config_file.format(chat_id=update.message.from_user.id)
    if not os.path.isfile(filename):
        update.message.reply_text("Tu n'as pas de fichier de configuration.")
    else:
        os.remove(filename)
        logging.info("removing %s" % filename)
        update.message.reply_text("J'ai bien supprimé ton fichier de configuration.")

@bot.add_command(name='maconfig')
def maconfig(update, context):
    logging.info("[%d] /maconfig called" % update.message.from_user.id)
    filename = attestation_config_file.format(chat_id=update.message.from_user.id)
    if not os.path.isfile(filename):
        update.message.reply_text("Tu n'as pas de fichier de configuration.")
    else:
        with open(filename) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        update.message.reply_text("""
Attention les yeux, voici les informations de ton fichier de configuration :

{data}

Si tu souhaites les mettre à jour, supprime le fichier avec la commande /oublier et relance /attestation
        """.format(data=yaml.dump(data)))
        logging.info("sending configuration informations %s" % filename)

# @bot.add_command(name='jobs')
# def jobs(update, context):
#     print(bot.jobs.jobs())

# @bot.daily(time='22:51:00')
# def bzz(context):
#     print("send!")
#     bot.send_message("BzzZZZZZ", chat_id)

# @bot.repeat(interval=10)
# def bzz_minutes(context):
#     print("send!")
#     bot.send_message("Bzz", chat_id)

if __name__ == "__main__":
    bot.start()
