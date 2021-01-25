import telebot

TOKEN = '1590672424:AAGqOnBKzRRQD0KksL4zrBV5pQQzyCLAP4M'
bot = telebot.TeleBot(TOKEN)
bot.polling(none_stop=True)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Я бот. Приятно познакомиться, {}'.format(message.from_user.first_name))

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.from_user.id, 'Привет!')
    else:
        bot.send_message(message.from_user.id, 'Не понимаю, что это значит.')