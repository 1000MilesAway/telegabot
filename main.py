import telebot
from telebot import types
from settings import vars
import requests
import os, sys
from PIL import Image


bot = telebot.TeleBot(vars["TOKEN"])
pack_name = None

user_dict = {"user_id": None, "inline_message": None, "sticker_set_name": None, "emoji": None}


def remove_bg(filename):
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': open(filename, 'rb')},
        data={'size': 'auto'},
        headers={'X-Api-Key': vars["RMV_BG_API"]},
    )
    if response.status_code == requests.codes.ok:
        filename = filename.split(".")[0]+'_no_bg.png'
        with open(filename, 'wb') as out:
            out.write(response.content)
            out.close()
            return filename
    else:
        print("Error:", response.status_code, response.text)


def resize(filename):
    img = Image.open(filename)
    img_w = 512 / float(img.size[0])
    img_h = 512 / float(img.size[1])
    if img.size[0] >= img.size[1]:
        img_h = int(float(img.size[1]) * float(img_w))
        img_w = 512
        img = img.resize((img_w, img_h), Image.ANTIALIAS)
    else:
        img_w = int(float(img.size[0]) * float(img_h))
        img_h = 512
        img = img.resize((img_w, img_h), Image.ANTIALIAS)
    img.save('resized_image.png')


@bot.message_handler(commands=['start'])
def start(message):
    keyboardmain = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(text="Создать стикерпак", callback_data="create")
    button2 = types.InlineKeyboardButton(text="Обновить стикерпак", callback_data="update")
    button3 = types.InlineKeyboardButton(text="Обработать фото", callback_data="image")
    keyboardmain.add(button1, button2, button3)
    # bot.delete_message(message.chat.id, message.message_id)
    user_dict["inline_message"] = bot.send_message(message.chat.id, "Выберите опцию", reply_markup=keyboardmain)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global pack_name
    print("create: " + message.text)
    pack_name = message.text
    # if is_creating:
    #     print("create: " + message.text)


def create_set(name, image, emoji):
    img = open("resized_image.png", 'rb')
    bot.create_new_sticker_set(252334485, 'Memtetrad' + '_by_' + 'Da_ya_ne_bot', 'AutoMemtetrad', img, "😧")
    set = bot.get_sticker_set('Memtetrad' + '_by_' + 'Da_ya_ne_bot')
    bot.send_sticker(user_dict["inline_message"].chat.id, set.stickers[len(set.stickers)-1].file_id)
    print(set)


# @bot.message_handler(content_types=['document'])
def get_image(message):
    print(user_dict)
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)
    print(file_name)
    with open("in.png", 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.delete_message(message.chat.id, message.message_id)
    resize(remove_bg("in.png"))
    img = open("resized_image.png", 'rb')
    bot.send_photo(message.chat.id, img)
    create_set(1,1,1)
    keyboard = types.InlineKeyboardMarkup()
    backbutton = types.InlineKeyboardButton(text="back", callback_data="mainmenu")
    keyboard.add(backbutton)
    bot.edit_message_text(chat_id=user_dict["inline_message"].chat.id, message_id=user_dict["inline_message"].message_id, text="Устраивает фото?",
                                reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print(call.message.text)
    if call.data == "mainmenu":
        keyboardmain = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton(text="Создать стикерпак", callback_data="create")
        button2 = types.InlineKeyboardButton(text="Обновить стикерпак", callback_data="update")
        button3 = types.InlineKeyboardButton(text="Обработать фото", callback_data="image")
        keyboardmain.add(button1, button2, button3)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите опцию", reply_markup=keyboardmain)

    if call.data == "create":
        # print(call.data)
        keyboard = types.InlineKeyboardMarkup()
        # rele1 = types.InlineKeyboardButton(text="1t", callback_data="1")
        # rele2 = types.InlineKeyboardButton(text="2t", callback_data="2")
        # rele3 = types.InlineKeyboardButton(text="3t", callback_data="3")
        add_button = types.InlineKeyboardButton(text="Добавить", callback_data="create_name")
        back_button = types.InlineKeyboardButton(text="Назад", callback_data="mainmenu")
        keyboard.add(add_button, back_button)
        # is_creating = True
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="WIP", reply_markup=keyboard)
    elif call.data == "create_name":
        print(pack_name)
        # bot.create_new_sticker_set(252334485, 'Memtetrad'+'_by_'+'Da_ya_ne_bot', 'AutoMemtetrad')
        print(bot.get_sticker_set('Memtetrad'+'_by_'+'Da_ya_ne_bot'))

    elif call.data == "update":

        keyboard = types.InlineKeyboardMarkup()
        rele1 = types.InlineKeyboardButton(text="another layer", callback_data="gg")
        backbutton = types.InlineKeyboardButton(text="back", callback_data="mainmenu")
        keyboard.add(rele1, backbutton)
        bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id, text="replaced text", reply_markup=keyboard)

    elif call.data == "image":
        keyboard = types.InlineKeyboardMarkup()
        backbutton = types.InlineKeyboardButton(text="back", callback_data="mainmenu")
        keyboard.add(backbutton)
        msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Загрузите фото", reply_markup=keyboard)
        bot.register_next_step_handler(msg, get_image)

    elif call.data == "1" or call.data == "2" or call.data == "3":
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="alert")
        keyboard3 = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="lastlayer", callback_data="ll")
        keyboard3.add(button)
        bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id, text="last layer",reply_markup=keyboard3)


if __name__ == "__main__":
    # resize(remove_bg("in.png"))
    bot.polling(none_stop=True)
