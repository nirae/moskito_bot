from Bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
import os
import yaml
import logging

from generateur_attestation_sortie.app import Generator, ConfigSchema

attestation_config_file = os.getcwd() + "/config_files/{chat_id}_config.yml"

def first_name(update, context):
    context.user_data['first_name'] = update.message.text
    update.message.reply_text('Joli !\nNom de famille?')
    return LAST_NAME

def last_name(update, context):
    context.user_data['last_name'] = update.message.text
    update.message.reply_text("On choisit pas...\nDate de naissance? format: JJ/MM/AAAA")
    return BIRTHDAY

def birthday(update, context):
    context.user_data['birthday'] = update.message.text
    update.message.reply_text("Lieu de naissance?")
    return PLACEOFBIRTH

def place_of_birth(update, context):
    context.user_data['placeofbirth'] = update.message.text
    update.message.reply_text("Je sais même pas ou c'est\nCode postal de ton lieu de résidence?")
    return ZIPCODE

def zipcode(update, context):
    context.user_data['zipcode'] = int(update.message.text)
    update.message.reply_text("Ville de résidence?")
    return CITY

def city(update, context):
    context.user_data['city'] = update.message.text
    update.message.reply_text("Dernier!\nAdresse?")
    return ADDRESS

def address(update, context):
    update.message.reply_text("Et voilà ! Tes infos sont stockées dans un fichier de configuration, je ne te les demanderai plus. Tu peux les voir avec /maconfig, ou les supprimer avec /oublier")
    context.user_data['address'] = update.message.text
    with open('exemple_config.yml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, val in context.user_data.items():
        data['user'][key] = val
    with open(attestation_config_file.format(chat_id=update.message.from_user.id), 'w') as f:
        yaml.dump(data, f)
    context.user_data.clear()
    logging.info("[%d] %s created!" % (update.message.from_user.id, attestation_config_file.format(chat_id=update.message.from_user.id)))
    return ask_reason(update, context)

def reason(update, context):
    message = context.user_data['message']
    logging.info("[%d] reason choosed" % message.from_user.id)

    with open(attestation_config_file.format(chat_id=message.from_user.id)) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    data['user']['user'] = 'user'
    data['user']['reason'] = update.callback_query.data

    gen = Generator()
    schema = ConfigSchema()
    config = schema.load(data['user'])
    if not config:
        logging.error("[%d] config validation failed" % message.from_user.id)
        message.reply_text("Une erreur est survenue durant la génération de l'attestation, vérifie tes informations avec la commande /maconfig et essaye de recommencer")
        return ConversationHandler.END
    
    logging.info("[%d] attestation generation..." % message.from_user.id)
    logging.debug(vars(config))
    filename = gen.run(config, output=str(message.from_user.id) + '_attestation.pdf')
    if not filename:
        logging.error("[%d] attestation generation failed" % message.from_user.id)
        message.reply_text("Une erreur est survenue durant la génération de l'attestation, vérifie tes informations avec la commande /maconfig et essaye de recommencer")
        return ConversationHandler.END
    logging.info("[%d] done" % message.from_user.id)
    with open(filename, 'rb') as f:
        message.reply_document(document=f)
    logging.info("[%d] removing attestation file %s" % (message.from_user.id, filename))
    os.remove(filename)
    gen.close()
    context.user_data.clear()
    return ConversationHandler.END

def ask_reason(update, context):
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
    return REASON

REASON, FIRST_NAME, LAST_NAME, BIRTHDAY, PLACEOFBIRTH, ZIPCODE, CITY, ADDRESS  = range(8)

states = {
    REASON: [CallbackQueryHandler(reason)],
    FIRST_NAME: [MessageHandler(Filters.text & (~Filters.command), first_name, message_updates=True)], 
    LAST_NAME: [MessageHandler(Filters.text & (~Filters.command), last_name, message_updates=True)], 
    BIRTHDAY: [MessageHandler(Filters.regex('^([0-9]{2}/[0-9]{2}/[0-9]{4})$'), birthday, message_updates=True)], 
    PLACEOFBIRTH: [MessageHandler(Filters.text & (~Filters.command), place_of_birth, message_updates=True)], 
    ZIPCODE: [MessageHandler(Filters.regex('^([1-9]{1}[0-9]{4})$'), zipcode, message_updates=True)], 
    CITY: [MessageHandler(Filters.text & (~Filters.command), city, message_updates=True)],
    ADDRESS: [MessageHandler(Filters.text & (~Filters.command), address, message_updates=True)]
}
