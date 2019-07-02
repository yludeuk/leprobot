# -*- coding: utf-8 -*-
import os
from datetime import datetime

import telebot
import random
from flask import Flask, request
from pymongo import MongoClient

token = os.environ['TOKEN']
bot = telebot.TeleBot(token)

server = Flask(__name__)


client = MongoClient(os.environ['MONGO_URL'], 63367)
db = client[os.environ['MONGODB']]
db.authenticate(os.environ['MONGO_USER'], os.environ['MONGO_PASSWORD'])
lepers_collection = db['lepers']

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    result = "Привет! Я Лепрорандомбот!\r\nЯ поддерживаю следующие команды:"
    result += "\r\n/start - запустить бота"
    result += "\r\n/setlepers <список игроков> - установить актуальный список игроков для жеребьевки (ввод через пробел)"
    result += "\r\n/getlepers - посмотреть актуальный список"
    result += "\r\n/randomize <количество игроков> - выбрать случайным образом заданное количество игроков из актуального списка"
    result += "\r\n/help - посмотреть справку"
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['randomize'])
def handle_randomize(message):
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user.username else ''
    bound_to = message.chat.title if message.chat.type == 'group' else username
    lepers_by_group = {lepers_group['chat_id']: lepers_group for lepers_group in lepers_collection.find({})}
    if chat_id not in lepers_by_group:
        new_element = {'chat_id': message.chat.id,
                       'bound_to': bound_to,
                       'last_edit_date': datetime.fromtimestamp(message.date),
                       'last_edited_by': username,
                       'members': [],
                       'number': 0}
        lepers_by_group[chat_id] = new_element
        lepers_collection.insert_one(new_element)

    msg = message.text[len('/randomize'):]
    if msg.startswith('@'):
        if msg.startswith('@LeproRandomBot ') or msg == '@LeproRandomBot':
            msg = msg[len('@LeproRandomBot '):]
        else:
            msg = '0'
    members = lepers_by_group[message.chat.id]['members']
    if len(members) == 0:
        bot.send_message(message.chat.id, 'Актуальный список пуст. Я не смогу ничего нарандомить.')
        return
    if not msg:
        number = lepers_by_group[message.chat.id]['number']
        if not number:
            bot.send_message(message.chat.id, 'Нужно задать количество участников.')
            return
    else:
        try:
            number = int(msg)
        except:
            bot.send_message(message.chat.id, 'Что это за число? Не пойму.')
            return
        if not number:
            bot.send_message(message.chat.id, 'Ну нет, так нельзя.')
            return
    new_values = {
        'last_edit_date': datetime.fromtimestamp(message.date),
        'last_edited_by': username,
        'number': number
    }
    lepers_collection.update_one({'chat_id': chat_id}, {'$set': new_values}, upsert=False)
    members = [member for member in members if member]
    if len(members) < number:
        bot.send_message(message.chat.id, 'Позвольте, но я не могу выбрать %s из %s.' % (number, len(members)))
        return
    players = random.sample(members, number)
    losers = set(members).difference(players)
    players = [player for player in members if player in players]
    players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(players)]
    result = 'Рандом выбрал следующих игроков:\r\n%s' % '\r\n'.join(players_enumerated)
    result += '\r\nПоздравим счастливчиков!🌟'
    if len(losers) > 0:
        losers = [player for player in members if player in losers]
        players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(losers)]
        result += '\r\n\r\nЖдут следующего шанса:\r\n%s' % '\r\n'.join(players_enumerated)
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['setlepers'])
def handle_set_lepers(message):
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user.username else ''
    bound_to = message.chat.title if message.chat.type == 'group' else username
    lepers_by_group = {lepers_group['chat_id']: lepers_group for lepers_group in lepers_collection.find({})}
    if chat_id not in lepers_by_group:
        new_element = {'chat_id': message.chat.id,
                       'bound_to': bound_to,
                       'last_edit_date': datetime.fromtimestamp(message.date),
                       'last_edited_by': username,
                       'members': [],
                       'number': 0}
        lepers_collection.insert_one(new_element)

    msg = message.text[len('/setlepers'):]
    if msg.startswith('@'):
        if msg.startswith('@LeproRandomBot ') or msg == '@LeproRandomBot':
            msg = msg[len('@LeproRandomBot '):]
        else:
            bot.send_message(message.chat.id, 'Непонятно. Давайте еще раз.')
            return
    else:
        msg = msg[1:]
    if not msg:
        bot.send_message(message.chat.id, 'Укажите, пожалуйста, хотя бы одного человека.')
        return
    lepers = msg.split(' ')
    lepers_copy = lepers
    lepers = []
    for leper in lepers_copy:
        if leper not in lepers:
            lepers.append(leper)
    if len(lepers) > 100:
        bot.send_message(message.chat.id, 'Вас слишком много! Дайте мне поменьше людей, пожалуйста.')
        return
    if max([len(leper) for leper in lepers]) > 32:
        bot.send_message(message.chat.id, 'Кажется, у кого-то слишком длинное имя. Попробуйте еще раз...')
        return
    new_values = {
        'last_edit_date': datetime.fromtimestamp(message.date),
        'last_edited_by': username,
        'members': lepers
    }
    lepers_collection.update_one({'chat_id': chat_id}, {'$set': new_values}, upsert=False)
    bot.send_message(message.chat.id, 'Готово! Актуальный список обновлён.')


@bot.message_handler(commands=['getlepers'])
def handle_get_lepers(message):
    lepers_by_group = {lepers_group['chat_id']: lepers_group for lepers_group in lepers_collection.find({})}
    if message.chat.id not in lepers_by_group:
        username = message.from_user.username if message.from_user.username else ''
        bound_to = message.chat.title if message.chat.type == 'group' else username
        new_element = {'chat_id': message.chat.id,
                       'bound_to': bound_to,
                       'last_edit_date': datetime.fromtimestamp(message.date),
                       'last_edited_by': username,
                       'members': [],
                       'number': 0}
        lepers_by_group[message.chat.id] = new_element
        lepers_collection.insert_one(new_element)
    lepers = lepers_by_group[message.chat.id]['members']
    if len(lepers) == 0:
        result = 'В актуальном списке никого нет'
    else:
        players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(lepers)]
        result = 'Актуальный список:\r\n%s' % '\r\n'.join(players_enumerated)
    bot.send_message(message.chat.id, result)


@server.route('/%s' % token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=os.environ['URL'] + token)
    return "!", 200

port = int(os.environ.get('PORT', 5000))
server.run(host="0.0.0.0", port=port)