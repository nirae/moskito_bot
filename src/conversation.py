from Bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
import os
import yaml
import logging
import random
import string

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

def birthday_error(update, context):
    update.message.reply_text("Hmmm la date n'est pas bonne... Recommence!")
    return BIRTHDAY

def place_of_birth(update, context):
    context.user_data['placeofbirth'] = update.message.text
    update.message.reply_text("Je sais même pas ou c'est\nCode postal de ton lieu de résidence?")
    return ZIPCODE

def zipcode(update, context):
    context.user_data['zipcode'] = int(update.message.text)
    update.message.reply_text("Ville de résidence?")
    return CITY

def zipcode_error(update, context):
    update.message.reply_text("Hmmm le code postal n'est pas bon... Recommence!")
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

    return ask_context(update, context)

def reason(update, context):
    message = update.callback_query.message
    logging.info("[%d] reason choosed" % update.callback_query.from_user.id)
    message.reply_text("Bien reçu!")

    try:
        with open(attestation_config_file.format(chat_id=update.callback_query.from_user.id)) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if not data:
                logging.error("[%d] empty config file" % update.callback_query.from_user.id)
                os.remove(attestation_config_file.format(chat_id=update.callback_query.from_user.id))
                message.reply_text("Ton fichier de configuration semble être corrompu, je le supprime. Fais en un nouveau avec /attestation")
                return ConversationHandler.END
    except:
        logging.error("[%d] open failed on config file in reason" % update.callback_query.from_user.id)
        os.remove(attestation_config_file.format(chat_id=update.callback_query.from_user.id))
        message.reply_text("Tu n'as pas de fichier de configuration ou il est corrompu. Fais en un nouveau avec /attestation")
        return ConversationHandler.END

    data['user']['user'] = 'user'
    data['user']['reason'] = update.callback_query.data
    data['user']['context'] = context.user_data['context']
    if 'message' in data['user']:
        del data['user']['message']

    letters = string.ascii_lowercase
    tmp_filename = ''.join(random.choice(letters) for i in range(30))
    tmp_filename = '/tmp/' + tmp_filename

    gen = Generator(directory=tmp_filename+'/')
    schema = ConfigSchema()
    config = schema.load(data['user'])
    if not config:
        logging.error("[%d] config validation failed" % update.callback_query.from_user.id)
        message.reply_text("Une erreur est survenue durant la génération de l'attestation, vérifie tes informations avec la commande /maconfig et essaye de recommencer")
        return ConversationHandler.END
    
    logging.info("[%d] attestation generation..." % update.callback_query.from_user.id)
    logging.debug(vars(config))
    message.reply_text("Je génère ton attestation ...")

    try:
        filename = gen.run(config, output=tmp_filename + str(update.callback_query.from_user.id) + '_attestation.pdf')
        if not filename:
            logging.error("[%d] attestation generation failed" % update.callback_query.from_user.id)
            message.reply_text("Une erreur est survenue durant la génération de l'attestation, vérifie tes informations avec la commande /maconfig et essaye de recommencer")
            return ConversationHandler.END
    except:
        logging.error("[%d] attestation generation failed" % update.callback_query.from_user.id)
        message.reply_text("Une erreur est survenue durant la génération de l'attestation, vérifie tes informations avec la commande /maconfig et essaye de recommencer")
        return ConversationHandler.END
    logging.info("[%d] done" % update.callback_query.from_user.id)
    with open(filename, 'rb') as f:
        message.reply_document(document=f, filename='attestation.pdf')
    logging.info("[%d] removing attestation file %s" % (update.callback_query.from_user.id, filename))
    os.remove(filename)
    gen.close()
    context.user_data.clear()
    return ConversationHandler.END

def context_conv(update, context):
    message = context.user_data['message']
    logging.info("[%d] context choosed" % message.from_user.id)
    context.user_data['context'] = update.callback_query.data
    return ask_reason(update, context)

def ask_context(update, context):
    context.user_data['message'] = update.message
    keyboard = [
        [
            InlineKeyboardButton("Couvre-Feu", callback_data='couvre-feu'),
            InlineKeyboardButton("Confinement", callback_data='confinement')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Contexte :", reply_markup=reply_markup)
    return CONTEXT

def ask_reason(update, context):
    context.user_data['message'] = update.message

    context_choice = context.user_data['context']
    
    if context_choice == 'couvre-feu':
        keyboard = [
            [
                InlineKeyboardButton("Transits", callback_data='transits'),
                InlineKeyboardButton("Animaux", callback_data='animaux')
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
            ]
        ]
    elif context_choice == 'confinement':
        keyboard = [
            [
                InlineKeyboardButton("Achats", callback_data='achats'),
                InlineKeyboardButton("Sortie", callback_data='sport'),
            ],
            [
                InlineKeyboardButton("Transits", callback_data='transits'),
                InlineKeyboardButton("Sante", callback_data='sante'),
                InlineKeyboardButton("Travail", callback_data='travail')
            ],
            [
                InlineKeyboardButton("Culte / Culturel", callback_data='culte-culturel'),
                InlineKeyboardButton("Enfants", callback_data='enfants'),
                InlineKeyboardButton("Déménagement", callback_data='demenagement'),
                InlineKeyboardButton("Démarches", callback_data='demarche')
            ],
            [
                InlineKeyboardButton("Famille", callback_data='famille'),
                InlineKeyboardButton("Handicap", callback_data='handicap'),
                InlineKeyboardButton("Convocation", callback_data='convocation'),
                InlineKeyboardButton("Mission", callback_data='missions')
            ]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("Choisis la raison", reply_markup=reply_markup)
    return REASON

CONTEXT, REASON, FIRST_NAME, LAST_NAME, BIRTHDAY, PLACEOFBIRTH, ZIPCODE, CITY, ADDRESS  = range(9)

states = {
    CONTEXT: [CallbackQueryHandler(context_conv)],
    REASON: [CallbackQueryHandler(reason)],
    FIRST_NAME: [MessageHandler(Filters.text & (~Filters.command), first_name)], 
    LAST_NAME: [MessageHandler(Filters.text & (~Filters.command), last_name)], 
    BIRTHDAY: [
        MessageHandler(Filters.regex('^([0-9]{2}/[0-9]{2}/[0-9]{4})$'), birthday),
        MessageHandler(Filters.regex('^.*$'), birthday_error)
    ], 
    PLACEOFBIRTH: [MessageHandler(Filters.text & (~Filters.command), place_of_birth)], 
    ZIPCODE: [
        MessageHandler(Filters.regex('^([1-9]{1}[0-9]{4})$'), zipcode),
        MessageHandler(Filters.regex('^.*$'), zipcode_error)
    ], 
    CITY: [MessageHandler(Filters.text & (~Filters.command), city)],
    ADDRESS: [MessageHandler(Filters.text & (~Filters.command), address)]
}
