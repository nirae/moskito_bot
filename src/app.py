#! /usr/bin/env python3

from Bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
import requests
from datetime import datetime
import os
import glob
import yaml
import traceback

from generator import Generator, ConfigSchema

token = os.environ['TELEGRAM_TOKEN']
chat_id = os.environ['TELEGRAM_GROUP_ID']

bot = Bot(token, chat_id)

@bot.add_command(name='hello')
def hello(update, context):
    update.message.reply_text('Bzz Bzz ... Hello %s!' % update.message.from_user.first_name)

@bot.add_command(name='heure')
def hour(update, context):
    print("heure")
    paris = requests.get('http://worldtimeapi.org/api/timezone/Europe/Paris').json()
    montreal = requests.get('http://worldtimeapi.org/api/timezone/America/Montreal').json()
    paris = datetime.fromisoformat(paris['datetime'])
    montreal = datetime.fromisoformat(montreal['datetime'])
    update.message.reply_text('Il est %dh%d chez Emma\nIl est %dh%d chez les autres' % (montreal.hour, montreal.minute, paris.hour, paris.minute))

################################################################################
################################################################################
#                           ATTESTATION                                        #
################################################################################
################################################################################

REASON, FIRST_NAME, LAST_NAME, BIRTHDAY, PLACEOFBIRTH, ZIPCODE, CITY, ADDRESS  = range(8)

def first_name(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['first_name'] = update.message.text
    update.message.reply_text('Joli !\nNom de famille?')
    return LAST_NAME

def last_name(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['last_name'] = update.message.text
    update.message.reply_text("On choisit pas...\nDate de naissance? format: JJ/MM/AAAA")
    return BIRTHDAY

def birthday(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['birthday'] = update.message.text
    update.message.reply_text("Lieu de naissance?")
    return PLACEOFBIRTH

def place_of_birth(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['placeofbirth'] = update.message.text
    update.message.reply_text("Je sais même pas ou c'est\nCode postal de ton lieu de résidence?")
    return ZIPCODE

def zipcode(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['zipcode'] = int(update.message.text)
    update.message.reply_text("Ville de résidence?")
    return CITY

def city(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END
    context.user_data['city'] = update.message.text
    update.message.reply_text("Dernier!\nAdresse?")
    return ADDRESS

def address(update, context):
    if update.message.text == "stop":
        update.message.reply_text("Tant pis...")
        return ConversationHandler.END

    update.message.reply_text("""
Et voilà ! Tes infos sont stockées dans un fichier de configuration, je ne te les demanderai plus.
Tu peux relancer la commande /attestation pour recevoir ton attestation
""")
    context.user_data['address'] = update.message.text

    with open('config.yml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    for key, val in context.user_data.items():
        data['user'][key] = val
    with open(str(update.message.from_user.id) + '_config.yml', 'w') as f:
        yaml.dump(data, f)
        f.close()
    context.user_data.clear()
    return ConversationHandler.END

def reason(update, context):
    message = context.user_data['message']
    try:
        with open(str(message.from_user.id) + '_config.yml') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

        data['user']['user'] = 'user'
        data['user']['reason'] = update.callback_query.data
        gen = Generator()
        schema = ConfigSchema()
        config = schema.load(data['user'])
        print("vars", vars(config))
        filename = gen.run(config, output=str(message.from_user.id) + '_attestation.pdf')
        if not filename:
            return ConversationHandler.END
        with open(filename, 'rb') as f:
            message.reply_document(document=f)
            f.close()
        os.remove(filename)
        gen.close()
    except:
        traceback.print_exc()
    context.user_data.clear()
    return ConversationHandler.END

states = {
    REASON: [CallbackQueryHandler(reason)],
    FIRST_NAME: [MessageHandler(Filters.text, first_name)], 
    LAST_NAME: [MessageHandler(Filters.text, last_name)], 
    BIRTHDAY: [MessageHandler(Filters.regex('^([0-9]{2}/[0-9]{2}/[0-9]{4})$'), birthday)], 
    PLACEOFBIRTH: [MessageHandler(Filters.text, place_of_birth)], 
    ZIPCODE: [MessageHandler(Filters.regex('^([1-9]{1}[0-9]{4})$'), zipcode)], 
    CITY: [MessageHandler(Filters.text, city)],
    ADDRESS: [MessageHandler(Filters.text, address)]
}

@bot.conversation(name='attestation', states=states, cancel_text="Goodbye!")
def attestation(update, context):
    file = glob.glob(str(update.message.from_user.id) + '_config.yml')
    if not file:
        update.message.reply_text("""Ah ! Je n'ai pas encore les informations te concernant.
Réponds à mes quelques questions et tu n'auras plus jamais à le faire !

Je stockerai tes informations dans un fichier de configuration. Tu peux quitter la conversation à tout moment en envoyant "stop". Tu peux aussi supprimer ton fichier de configuration avec la commande /oublier.

Les attestations sont supprimées directement après l'envoi.

Commençons, quel est ton prénom ?""")
        return FIRST_NAME
    try:
        context.user_data['message'] = update.message
        keyboard = [
            [
                InlineKeyboardButton("Achats", callback_data='achats'),
                InlineKeyboardButton("Sortie 1h", callback_data='sports_animaux')
            ],
            [
                InlineKeyboardButton("Sante", callback_data='sante'),
                InlineKeyboardButton("Travail", callback_data='travail')
            ],
            [
                InlineKeyboardButton("Famille", callback_data='famille'),
                InlineKeyboardButton("Handicap", callback_data='handicap'),
                InlineKeyboardButton("Convocation", callback_data='convocation'),
                InlineKeyboardButton("Mission", callback_data='missions'),
                InlineKeyboardButton("Enfants", callback_data='enfants')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Choisis la raison", reply_markup=reply_markup)
    except:
        traceback.print_exc()
    return REASON

@bot.add_command(name='oublier')
def oublier(update, context):
    filename = str(update.message.from_user.id) + '_config.yml'
    file = glob.glob(filename)
    if not file:
        update.message.reply_text("Tu n'as pas de fichier de configuration.")
    else:
        os.remove(filename)
        update.message.reply_text("J'ai bien supprimé ton fichier de configuration.")

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
