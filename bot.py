
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

select_element = soup.find('select', {'id': 'Film'})
options = select_element.find_all('option')
film_list = [option.text for option in options]
film_list = film_list[2:]
film_list = film_list[:(len(film_list)-2)]

select_element_developer = soup.find('select', {'id': 'Developer'})
options = select_element_developer.find_all('option')
developers_list = [option.text for option in options]
developers_list = developers_list[2:]
developers_list = developers_list[:(len(developers_list)-2)]
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

FILM_FORMAT, FILM_NAME, DEVELOPER, DILUTION, ISO, END = range(6)
def get_all_possible_dilutions(dataframe):
    return np.unique(dataframe["dilution"])

def filter_by_dilution(dataframe, dilution,type_of_film):
    return dataframe[dataframe["dilution"]==dilution][type_of_film]

def start(update, context):
    film_name_keyboard = [
        [telegram.KeyboardButton('35'), telegram.KeyboardButton('120'),telegram.KeyboardButton('sheet')]
    ]
    film_name_markup = telegram.ReplyKeyboardMarkup(film_name_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="What type of film are you developing?", reply_markup=film_name_markup)
    return FILM_FORMAT

def film_type(update, context):
    user_film_type = update.message.text
    context.user_data['film_type']=user_film_type
    film_name_keyboard=[]

    for film in film_list:
        newList = []
        film_name = str(film)
        button_to_add = telegram.KeyboardButton(film_name)
        newList.append(button_to_add)
        film_name_keyboard.append(newList)

    film_name_markup = telegram.ReplyKeyboardMarkup(film_name_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Which film are you using?", reply_markup=film_name_markup)
    return FILM_NAME

def film_name(update,context):
    user_film_name = update.message.text
    context.user_data['film_name'] = user_film_name
    developer_name_keyboard=[]

    for developer in developers_list:
        newList = []
        developer_name = str(developer)
        button_to_add = telegram.KeyboardButton(developer_name)
        newList.append(button_to_add)
        developer_name_keyboard.append(newList)

    developer_name_markup = telegram.ReplyKeyboardMarkup(developer_name_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Which developer are you using?", reply_markup=developer_name_markup)
    return DEVELOPER
        

def developer_name(update, context):
    user_film_name = context.user_data.get('film_name')
    user_developer_name = update.message.text
    print("SVILUPPO DI {} IN {}".format(user_film_name,user_developer_name))
    context.user_data['developer_name'] = user_developer_name
    data = get_development_times(user_film_name,user_developer_name)
    print(data)
    context.user_data['dataframe'] = data
    all_dilutions = get_all_possible_dilutions(data)
    dilution_keyboard=[]
    for dilution in all_dilutions:
        newList=[]
        button_to_add = telegram.KeyboardButton(dilution)
        newList.append(button_to_add)
        dilution_keyboard.append(newList)
    dilution_markup = telegram.ReplyKeyboardMarkup(dilution_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="What is the dilution of your developer?", reply_markup=dilution_markup)
    return DILUTION

def dilution(update, context):
    user_dilution = update.message.text
    context.user_data['dilution'] = user_dilution
    data = context.user_data['dataframe']
    print("DATA")
    print(data)
    all_iso = np.unique(data["iso"])
    print(all_iso)
    iso_keyboard = []
    for iso_entry in all_iso:
        newList = []
        button_to_add = telegram.KeyboardButton(iso_entry)
        newList.append(button_to_add)
        iso_keyboard.append(newList)
    iso_markup = telegram.ReplyKeyboardMarkup(iso_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="For what ISO sensitivity do you want do develop?", reply_markup=iso_markup)
    return ISO

def iso(update, context):
    user_iso = update.message.text
    user_dilution = context.user_data.get('dilution')
    data = context.user_data['dataframe']
    data_for_user_iso = data[data["iso"]==user_iso]
    data_for_user_dilution = data_for_user_iso[data_for_user_iso["dilution"]==user_dilution]
    key_type = "time_"+context.user_data.get('film_type')
    minutes = data_for_user_dilution[key_type].iloc[0]
    context.user_data['minutes'] = minutes
    update.message.reply_text(f"The developing time is: {minutes} minutes.")
    return ConversationHandler.END


updater = Updater(token=TOKEN, use_context=True)

conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FILM_FORMAT: [MessageHandler(Filters.text, film_type)],
            FILM_NAME: [MessageHandler(Filters.text,film_name)],
            DEVELOPER: [MessageHandler(Filters.text, developer_name)],
            DILUTION: [MessageHandler(Filters.text, dilution)],
            ISO: [MessageHandler(Filters.text,iso)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()