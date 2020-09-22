# pip3 install python-telegram-bot
import telegram
from telegram.ext import Updater, CommandHandler, JobQueue
import datetime

class Bot(object):

    def __init__(self, token, group_id):
        self.token = token
        self.bot = telegram.Bot(token=token)
        self.chat_id = group_id
        self.updater = Updater(token, use_context=True)
        self.jobs = self.updater.job_queue
        
    def add_command(self, name,
                    pass_args=False,
                    pass_job_queue=False,
                    pass_chat_data=False):
        def decorator(func):
            handler = CommandHandler(name, func, pass_args, pass_job_queue, pass_chat_data)
            self.updater.dispatcher.add_handler(handler)
            return func
        return decorator

    def monthly(self, time, day):
        def decorator(func):
            to = datetime.time()
            t = to.fromisoformat(time).replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
            self.jobs.run_monthly(func, t, day, context=self.chat_id)
            return func
        return decorator

    def daily(self, time, days=(0, 1, 2, 3, 4, 5, 6)):
        def decorator(func):
            to = datetime.time()
            t = to.fromisoformat(time).replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
            self.jobs.run_daily(func, t, days, context=self.chat_id)
            return func
        return decorator

    def repeat(self, interval=60):
        def decorator(func):
            self.jobs.run_repeating(func, interval, first=0)
            return func
        return decorator

    def send_message(self, message, chat_id):
        self.bot.send_message(chat_id=chat_id, text=message)

    def start(self):
        # start the bot
        self.updater.start_polling()
        # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
        # SIGABRT. This should be used most of the time, since start_polling() is
        # non-blocking and will stop the bot gracefully.
        self.updater.idle()
