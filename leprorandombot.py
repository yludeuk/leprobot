# -*- coding: utf-8 -*-
import os
import sys
import telebot
import shelve
import random
from flask import Flask, request

token = os.environ['TOKEN']
bot = telebot.TeleBot(token)

server = Flask(__name__)


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
    msg = message.text[len('/randomize'):]
    if msg.startswith('@'):
        if msg.startswith('@LeproRandomBot ') or msg == '@LeproRandomBot':
            msg = msg[len('@LeproRandomBot '):]
        else:
            msg = '0'
    total = set(get_lepers(message.chat.id))
    if len(total) == 0:
        bot.send_message(message.chat.id, 'Актуальный список пуст. Я не смогу ничего нарандомить.')
        return
    if not msg:
        with shelve.open('lepers.db') as storage:
            try:
                number = int(storage['number'])
            except KeyError:
                number = len(total)
    else:
        try:
            number = int(msg)
        except:
            bot.send_message(message.chat.id, 'Что это за число? Не пойму.')
            return
        if not number:
            bot.send_message(message.chat.id, 'Ну нет, так нельзя.')
            return
        with shelve.open('lepers.db') as storage:
            storage['number'] = number
    if len(total) < number:
        bot.send_message(message.chat.id, 'Позвольте, но я не могу выбрать %s из %s.' % (number, len(total)))
        return
    players = random.sample(total, number)
    losers = total.difference(players)
    players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(players)]
    result = '*Рандом выбрал следующих игроков:*\r\n%s' % '\r\n'.join(players_enumerated)
    result += '\r\n*Поздравим счастливчиков!*🌟'
    if len(losers) > 0:
        players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(losers)]
        result += '\r\n\r\n*Ждут следующего шанса:*\r\n%s' % '\r\n'.join(players_enumerated)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')


@bot.message_handler(commands=['setlepers'])
def handle_set_lepers(message):
    msg = message.text[len('/setlepers '):]
    if not msg:
        bot.send_message(message.chat.id, 'Укажите, пожалуйста, хотя бы одного человека.')
        return
    lepers = msg.split(' ')
    if len(lepers) > 100:
        bot.send_message(message.chat.id, 'Вас слишком много! Дайте мне поменьше людей, пожалуйста.')
        return
    if max([len(leper) for leper in lepers]) > 32:
        bot.send_message(message.chat.id, 'Кажется, у кого-то слишком длинное имя. Попробуйте еще раз...')
        return
    set_lepers(message.chat.id, lepers)
    bot.send_message(message.chat.id, 'Готово! Актуальный список обновлён.')


@bot.message_handler(commands=['getlepers'])
def handle_get_lepers(message):
    lepers = get_lepers(message.chat.id)
    if len(lepers) == 0:
        result = 'В актуальном списке никого нет'
    else:
        players_enumerated = ['%s. %s' % (i + 1, player) for i, player in enumerate(lepers)]
        result = '*Актуальный список:*\r\n%s' % '\r\n'.join(players_enumerated)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')


def set_lepers(chat_id, lepers):
    with shelve.open('lepers.db') as storage:
        storage[str(chat_id)] = set(lepers)


def get_lepers(chat_id):
    with shelve.open('lepers.db') as storage:
        try:
            lepers = storage[str(chat_id)]
            return lepers
        except KeyError:
            return []

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