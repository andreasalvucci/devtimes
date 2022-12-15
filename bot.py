TOKEN = "5771315363:AAEPZk_zKMJBZ4AmCMxNxVoPjuXF-wPCeaA"
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import telegram
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

url = 'https://www.digitaltruth.com/devchart.php'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
film_options = soup.find_all('option', attrs={'value': True})
film_names = [option.text for option in film_options]


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

bot = telegram.Bot(token=TOKEN)
ERROR, ASKING_FOR_FILM, ASKING_FOR_DEVELOPER, ASKING_FOR_DILUTION = range(4)

def start(update, context):
    update.message.reply_text('Hello! I am a development time calculator. Please tell me the name of the film you want to use.')
    return ASKING_FOR_FILM

def film_name(update, context):
    context.user_data['film'] = update.message.text
    update.message.reply_text('Thank you. Now please tell me the name of the developer you want to use.')
    return ASKING_FOR_DEVELOPER

def developer_name(update, context):
    context.user_data['developer'] = update.message.text
    update.message.reply_text('Thank you. Now please tell me the dilution you want to use.')
    return ASKING_FOR_DILUTION

def dilution(update, context):
    context.user_data['dilution'] = update.message.text
    film = context.user_data['film']
    developer = context.user_data['developer']
    dilution = context.user_data['dilution']
    list_of_times = get_development_times(film, developer)
    times = filter_by_dilution(list_of_times,dilution,"time_35")
    update.message.reply_text("Trovato il tempo per il 35mm")
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text('Cancelling the conversation.')
    return ConversationHandler.END

def error(update, context):
    update.message.reply_text('Errore, riprova')
    return ASKING_FOR_FILM

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ERROR: [MessageHandler(Filters.text,error)],
        ASKING_FOR_FILM: [MessageHandler(Filters.text, film_name)],
        ASKING_FOR_DEVELOPER: [MessageHandler(Filters.text, developer_name)],
        ASKING_FOR_DILUTION: [MessageHandler(Filters.text, dilution)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()
