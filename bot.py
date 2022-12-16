
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import telegram
from dotenv import load_dotenv
import logging
import os
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import  CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.environ.get("TOKEN_TELEGRAM_DEVTIMES")
print(TOKEN)

url = 'https://www.digitaltruth.com/devchart.php'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
film_options = soup.find_all('option', attrs={'value': True})
film_names = [option.text for option in film_options]
logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

logger = logging.getLogger(__name__)


def get_development_times(film, developer):
    column_names = ["film","developer","dilution","iso","time_35","time_120","time_sheet","temperature"]
    my_list = []
    film=film.replace(" ","+")
    developer=developer.replace(" ","+")
    url = 'https://www.digitaltruth.com/devchart.php?Film={}&Developer={}&mdc=Search&TempUnits=C&TimeUnits=D'.format(film, developer)
    print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {"class":"mdctable sortable"})
    if(table==None):
        return pd.DataFrame()
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 0:
            continue
        film = cells[0].text
        developer = cells[1].text
        dilution = cells[2].text
        asa = cells[3].text
        time_35 = cells[4].text
        time_120 = cells[5].text
        time_sheet = cells[6].text
        temperature = cells[7].text
        new_row = [film,developer,dilution,asa,time_35,time_120,time_sheet,temperature]
        my_list.append(new_row)
    
    result = pd.DataFrame(my_list, columns=column_names)
    return result

def get_all_possible_dilutions(dataframe):
    return np.unique(dataframe["dilution"])

def filter_by_dilution(dataframe, dilution,type_of_film):
    return dataframe[dataframe["dilution"]==dilution][type_of_film]

def start(update, context):
    film_name_keyboard = [
        [telegram.KeyboardButton('35mm'), telegram.KeyboardButton('120')]
    ]
    film_name_markup = telegram.ReplyKeyboardMarkup(film_name_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="What type of film are you developing?", reply_markup=film_name_markup)

def film_type(update, context):
    film_type = update.message.text
    developer_name_keyboard = [
        [telegram.KeyboardButton('Ilford ID-11'), telegram.KeyboardButton('Kodak D-76')],
        [telegram.KeyboardButton('Rodinal'), telegram.KeyboardButton('Tetenal Colortec C-41')]
    ]
    developer_name_markup = telegram.ReplyKeyboardMarkup(developer_name_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Which developer are you using?", reply_markup=developer_name_markup)

def developer_name(update, context):
    developer_name = update.message.text
    dilution_keyboard = [
        [telegram.InlineKeyboardButton('1+1', callback_data='1+1'), telegram.InlineKeyboardButton('1+2', callback_data='1+2')],
        [telegram.InlineKeyboardButton('1+3', callback_data='1+3'), telegram.InlineKeyboardButton('1+4', callback_data='1+4')]
    ]
    dilution_markup = telegram.InlineKeyboardMarkup(dilution_keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="What is the dilution of your developer?", reply_markup=dilution_markup)

def dilution(update, context):
    query = update.callback_query
    dilution = query.data
    context.bot.send_message(chat_id=query.message.chat_id, text="Thank you for the information. Based on your inputs, the developing time for your film is X minutes.")

updater = Updater(token=TOKEN, use_context=True)

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, film_type))
updater.dispatcher.add_handler(MessageHandler(Filters.text, developer_name))
updater.start_polling()