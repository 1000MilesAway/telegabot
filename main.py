import telebot
from telebot import types
from settings import vars
import requests
from PIL import Image
import emoji
import pymongo


def insert_document(collection, data):
    """ Function to insert a document into a collection and
    return the document's id.
    """
    return collection.insert_one(data).inserted_id

def find_document(collection, elements, multiple=True):
    """ Function to retrieve single or multiple documents from a provided
    Collection using a dictionary containing a document's elements.
    """
    if multiple:
        results = collection.find(elements)
        return [r for r in results]
    else:
        return collection.find_one(elements)

bot = telebot.TeleBot(vars["TOKEN"])
client = pymongo.MongoClient(vars["DB"]["host"], vars["DB"]["port"])
db = client[vars["DB"]["db"]]



chat = {"user_id": None, "inline_message": None, "message_id": None, "mode":None}
pack = {"name": None, "title": None, "sticker_set_name": None, "emoji": None, "db": db['sticker_sets'],
             "in_image": "images/in.png", "nobg_image": "images/nobg.png", "out_image": "images/out.png"}

class Data:

    def __init__(self, user_id):
        self.user_id = user_id
        self.chat = {"user_id": None, "inline_message": None, "message_id": None}
        self.pack = {"name": None, "sticker_set_name": None, "emoji": None, "db": db['sticker_sets'],
                 "in_image": "images/in.png", "nobg_image": "images/nobg.png", "out_image": "images/out.png"}
    def reset(self):
        self.chat = {"user_id": None, "inline_message": None, "message_id": None}
        self.pack = {"name": None, "sticker_set_name": None, "emoji": None, "db": db['sticker_sets'],
                     "in_image": "images/in.png", "nobg_image": "images/nobg.png", "out_image": "images/out.png"}


def update_kb(buttons, text):
    keyboard = types.InlineKeyboardMarkup()
    for button_data in buttons:
        button = types.InlineKeyboardButton(text=button_data["text"], callback_data=button_data["call"])
        keyboard.add(button)
    msg = bot.edit_message_text(chat_id=chat["inline_message"].chat.id, message_id=chat["inline_message"].message_id,
                                text=text, reply_markup=keyboard)
    return msg

def remove_bg(filename):
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': open(filename, 'rb')},
        data={'size': 'auto'},
        headers={'X-Api-Key': vars["RMV_BG_API"]},
    )
    if response.status_code == requests.codes.ok:
        with open(pack["nobg_image"], 'wb') as out:
            out.write(response.content)
            out.close()
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
    img.save(pack["out_image"])


@bot.message_handler(commands=['start'])
def start(message):
    data = Data(message.from_user.id)
    keyboardmain = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(text="Создать стикерпак", callback_data="create")
    button2 = types.InlineKeyboardButton(text="Обновить стикерпак", callback_data="update")
    # button3 = types.InlineKeyboardButton(text="Обработать фото", callback_data="image")
    keyboardmain.add(button1, button2)
    # bot.delete_message(message.chat.id, message.message_id)
    chat["user_id"] = message.from_user.id
    chat["inline_message"] = bot.send_message(message.chat.id, "Выберите опцию", reply_markup=keyboardmain)

def select_pack(message):
    result = find_document(pack["db"], {"user_id": chat["user_id"]})
    user_packs = []
    for obj in result:
        user_packs.append({"text": obj["set_title"], "call": "_" + obj["set_name"]})
    update_kb(user_packs, "Выберите пак")
    print(result)

def set_name(message):
    name = message.text
    if not name[0].isascii():
        update_kb([{"text": "Назад", "call": "mainmenu"}], "Ошибка в названии")
        bot.register_next_step_handler(chat["inline_message"], set_name)
        return
    pack["name"] = name
    bot.delete_message(message.chat.id, message.message_id)
    update_kb([{"text": "Назад", "call": "mainmenu"}], "Имя корректно, пришлите первое изображение как файл")
    bot.register_next_step_handler(chat["inline_message"], set_image)


def set_image(message):
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)

    with open(pack["in_image"], 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.delete_message(message.chat.id, message.message_id)
    update_kb([{"text": "Назад", "call": "mainmenu"},
               {"text": "Да", "call": "y_nobg"},
               {"text": "Нет", "call": "n_nobg"}],
              "Изображение корректно, удалить фон?")


def set_emoji(message):
    text = message.text
    if len(text) != 1 and text[0] in emoji.UNICODE_EMOJI:
        update_kb([{"text": "Назад", "call": "mainmenu"}], "Ошибка в эмоджи. Введите еще раз")
        bot.register_next_step_handler(chat["inline_message"], set_emoji)
        return
    pack["emoji"] = text
    bot.delete_message(message.chat.id, message.message_id)

    if chat["mode"] == "create":
        create_set_finally()
    if chat["mode"] == "update":
        update_set_finally()

def create_set_finally():
    with open(pack["out_image"], 'rb') as img:
        print(chat["user_id"])
        bot.create_new_sticker_set(chat["user_id"], pack["name"] + '_by_' + vars["BOT_NAME"],
                                   pack["name"], img, pack["emoji"])
    set = bot.get_sticker_set(pack["name"] + '_by_' + vars["BOT_NAME"])
    mes = bot.send_sticker(chat["inline_message"].chat.id, set.stickers[len(set.stickers) - 1].file_id)
    chat["message_id"] = mes.message_id
    update_kb([{"text": "Назад", "call": "done"}], "Успешно создано")
    new_set = {
        "user_id": chat["user_id"],
        "set_name": pack["name"] + '_by_' + vars["BOT_NAME"],
        "set_title": pack["name"]
    }
    print(insert_document(pack["db"], new_set))

    result = find_document(pack["db"], {"user_id": chat["user_id"]})
    print(result)

    print(set)


def update_set_finally():
    with open(pack["out_image"], 'rb') as img:
        print(chat["user_id"])
        bot.add_sticker_to_set(chat["user_id"], pack["name"], img, pack["emoji"])
    set = bot.get_sticker_set(pack["name"])
    mes = bot.send_sticker(chat["inline_message"].chat.id, set.stickers[len(set.stickers) - 1].file_id)
    chat["message_id"] = mes.message_id
    update_kb([{"text": "Назад", "call": "done"}], "Успешно добавленно")


def get_image(message):
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)

    with open("images/in.png", 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.delete_message(message.chat.id, message.message_id)
    resize(remove_bg("in.png"))
    with open("images/resized_image.png", 'rb') as img:
        bot.send_photo(message.chat.id, img)

    create_set_finally(1, 1, 1)
    keyboard = types.InlineKeyboardMarkup()
    backbutton = types.InlineKeyboardButton(text="back", callback_data="mainmenu")
    keyboard.add(backbutton)
    bot.edit_message_text(chat_id=chat["inline_message"].chat.id, message_id=chat["inline_message"].message_id,
                          text="Устраивает фото?", reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print(call.message.text)
    if call.data == "done":
        bot.delete_message(call.message.chat.id, chat["message_id"])
        update_kb([{"text": "Создать стикерпак", "call": "create"},
                   {"text": "Обновить стикерпак", "call": "update"}], "Выберите опцию")
    if call.data == "mainmenu":
        update_kb([{"text": "Создать стикерпак", "call": "create"},
                   {"text": "Обновить стикерпак", "call": "update"}], "Выберите опцию")

    if call.data == "create":
        chat["mode"] = "create"
        update_kb([{"text": "Назад", "call": "mainmenu"}], "Введите название пака")
        bot.register_next_step_handler(chat["inline_message"], set_name)

    elif call.data == "update":
        chat["mode"] = "update"
        select_pack(chat["inline_message"])


    elif call.data[0] == "_":
        pack["name"] = call.data[1:]
        update_kb([{"text": "Назад", "call": "mainmenu"}],
                  "Выбран пак. Пришлите изображение")
        bot.register_next_step_handler(chat["inline_message"], set_image)

    elif call.data == "image":
        keyboard = types.InlineKeyboardMarkup()
        backbutton = types.InlineKeyboardButton(text="back", callback_data="mainmenu")
        keyboard.add(backbutton)
        msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Загрузите фото", reply_markup=keyboard)
        bot.register_next_step_handler(msg, get_image)
    elif call.data == "y_nobg":
        update_kb([{"text": "Назад", "call": "mainmenu"},
                   {"text": "Да", "call": "correct_nobg"},
                   {"text": "Нет", "call": "incorrect_nobg"}],
                  "Устраивает?")
        remove_bg(pack["in_image"])
        with open(pack["nobg_image"], 'rb') as img:
            mes = bot.send_photo(chat["inline_message"].chat.id, img)
            chat["message_id"] = mes.message_id

    elif call.data == "n_nobg":
        resize(pack["in_image"])
        update_kb([{"text": "Назад", "call": "mainmenu"}], "Пришлите эмоджи")
        bot.register_next_step_handler(chat["inline_message"], set_emoji)
    elif call.data == "correct_nobg":
        bot.delete_message(chat["inline_message"].chat.id, chat["message_id"])
        resize(pack["nobg_image"])
        update_kb([{"text": "Назад", "call": "mainmenu"}], "Пришлите эмоджи")
        bot.register_next_step_handler(chat["inline_message"], set_emoji)
    elif call.data == "incorrect_nobg":
        bot.delete_message(chat["inline_message"].chat.id, chat["message_id"])
        update_kb([{"text": "Назад", "call": "mainmenu"},
                   {"text": "Да", "call": "y_nobg"},
                   {"text": "Нет", "call": "n_nobg"}],
                  "Попробовать еще раз?")


if __name__ == "__main__":
    # resize(remove_bg("in.png"))
    bot.polling(none_stop=True)
