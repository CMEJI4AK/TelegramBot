import json
import requests
import time
from datetime import datetime, timedelta

import telebot
from telebot import types
import traceback

import locale

locale.setlocale(
    locale.LC_ALL,
    ("ru_RU", "UTF-8"),
)  # Для русских названий месяцев в модулей datetime

currencies = {"rub": "руб."}

categories = {
    "main": "Все",
    "cinema": "Кино",
    "concert": "Концерт",
    "theatre": "Театр",
    "art": "Выставки",
    "standup": "Стендап",
    "show": "Шоу",
    "quest": "Квесты",
}

YANDEX_AFISHA_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ru,en;q=0.9",
    "x-force-cors-preflight": "1",
}


def getEventsInCityWithPeriod(
    city: str,
    date: datetime,
    *,
    category: str = "main",
    period: int = 1,
    limit: int = 10,
    offset: int = 0,
):
    params = {
        "limit": limit,
        "offset": offset,
        "rubric": category,
        "recommended": False,
        "date": date.strftime("%Y-%m-%d"),
        "period": period,
        "hasMixed": "0",
        "city": city.lower(),
        "_": str(round(time.time() * 1000)),
    }

    response = requests.get(
        f"https://afisha.yandex.ru/api/events/rubric/{category}",
        params=params,
        headers=YANDEX_AFISHA_HEADERS,
    )
    events = []
    data = response.json()
    for event in data["data"]:
        events.append(
            {
                "url": f"https://afisha.yandex.ru{event['event']['url']}",  # example: /prem/concert/name_event
                "name": event["event"]["title"],
                "contentRating": event["event"]["contentRating"],
                "tickets": event["event"]["tickets"],
                "dates": [
                    datetime.strptime(date, "%Y-%m-%d")
                    for date in event["scheduleInfo"]["dates"]
                ],
                "times": [t for t in event["scheduleInfo"]["regularity"]["daily"]],
                "oneOfPlaces": {
                    "url": f"https://afisha.yandex.ru{event["scheduleInfo"]["oneOfPlaces"]['url']}",
                    "title": event["scheduleInfo"]["oneOfPlaces"]["title"],
                },
                "type": {
                    "code": event["event"]["type"]["code"],
                    "name": event["event"]["type"]["name"],
                },
                "previewText": event["scheduleInfo"]["preview"]["text"],
            }
        )
    return events


bot = telebot.TeleBot("7121373991:AAG_t5_GsD9UAzghR9hQJPv1Elx31jwlC70")
last_messages: dict[int, list[int]] = {}


@bot.message_handler(
    content_types=[
        "photo",
        "video",
        "audio",
        "document",
        "sticker",
        "animation",
        "voice",
        "video_note",
        "story",
    ]
)
def get_content(message: types.Message):
    msg = bot.reply_to(
        message,
        "Мне бы очень хотелось узнать, что там, но я не умею распознавать такого рода сообщения😔.",
    )
    last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(commands=["start"])
def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton("Меню")
    btn2 = types.KeyboardButton("Помощь")
    btn3 = types.KeyboardButton("Перезапустить бота")
    btn4 = types.KeyboardButton("Справка")
    markup.row(btn1, btn4)
    markup.row(btn2, btn3)
    # markup2 = types.InlineKeyboardMarkup()
    msg = bot.send_message(
        message.chat.id, f"Привет, {message.from_user.first_name}", reply_markup=markup
    )
    last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(commands=["support"])
def support(message: types.Message):
    support_text = """
    Наша поддержка, с помощью которой вы можете связаться с нами напрямую:
    - Telegram: @savasakii или @egorichlyadov
    - E-mail: saveliybk30@gmail.com или lyadovegorka@yandex.ru
    """
    msg = bot.send_message(message.chat.id, support_text)
    last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(func=lambda message: message.text.lower() == "меню")
@bot.message_handler(commands=["menu"])
def menu(message: types.Message):
    file = open("./mainphoto.jpg", "rb")
    markup = types.InlineKeyboardMarkup()
    for key, name in categories.items():
        markup.add(
            types.InlineKeyboardButton(
                text=name, callback_data=json.dumps(["GEC", key])
            )
        )
    msg = bot.send_photo(
        message.chat.id,
        file,
        caption="Я помогу найти интересные занятия в Перми, пожалуйста выберите категорию:",
        reply_markup=markup,
    )
    last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(func=lambda message: message.text.lower() == "перезапустить бота")
@bot.message_handler(commands=["restart"])
def restart(message: types.Message):
    if message.chat.id in last_messages:
        for msg_id in last_messages[message.chat.id]:
            try:
                bot.delete_message(message.chat.id, msg_id)
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")
                traceback.print_exc()  # Для более подробного логирования ошибок
        last_messages[message.chat.id] = []  # Очищаем список ID сообщений

    msg = bot.send_message(
        message.chat.id,
        "Сессия перезапущена. Все предыдущие сообщения игнорируются. Пропишите '/start' для запуска бота",
    )
    last_messages[message.chat.id] = [msg.message_id]
    bot.register_next_step_handler(message, start)


@bot.message_handler(func=lambda message: message.text.lower() == "справка")
def help_message(message: types.Message):
    help_text = """
    Вот справочная информация по боту:
    - Команда '/start' - начать работу с ботом.
    - Команда '/menu' - показать главное меню.
    - Команда '/support' - поддержка, где вы можете связаться с нами насчёт ваших проблем.
    - Команда '/restart' - перезапустить сессию с ботом.
    - пропишите 'Меню' - показать главное меню.
    - пропишите 'Справка' - показать справочную информацию.
    - пропишите 'Помощь' - получить руководство пользователя.
    - пропишите 'Перезапустить бота' - перезапустить сессию, чтобы предыдущие сообщения игнорировались. После этого пропишите '/start' чтобы запустить бота.
    """
    msg = bot.reply_to(message, help_text)
    last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(func=lambda message: message.text.lower() == "помощь")
def help_document(message: types.Message):
    with open("Руководство пользователя.pdf", "rb") as help_file:
        msg = bot.send_message(
            message.chat.id,
            "В этом файле находится руководство пользователя, с помощью него вы сможете решите свою проблему",
        )
        bot.send_document(message.chat.id, help_file)
        last_messages[message.chat.id] = [msg.message_id]


@bot.message_handler(func=lambda message: True)
def echo_all(message: types.Message):
    msg = bot.reply_to(message, "Что то вы не то нажали, пропишите '/start'")

    if message.chat.id not in last_messages:
        last_messages[message.chat.id] = []
    last_messages[message.chat.id].extend([message.message_id, msg.message_id])


def make_pagination_markup(method, limit, offset, date, period, mid, category):
    markup = types.InlineKeyboardMarkup()
    btns = []
    if offset > 0 and offset >= limit:
        btns.append(
            types.InlineKeyboardButton(
                "Пред. стр.",
                callback_data=json.dumps(
                    [method, limit, offset - limit, date, period, mid, category]
                ),
            )
        )
    btns.append(
        types.InlineKeyboardButton(
            "След. стр.",
            callback_data=json.dumps(
                [method, limit, offset + limit, date, period, mid, category]
            ),
        )
    )
    markup.add(*btns)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    """
    data[0] - method; GE - get events; GEC - get events by category;
    data[1] - limit
    data[2] - offset
    data[3] - date
    data[4] - period
    data[5] - message id to edit (default: -1)
    data[6] - category
    """
    data = json.loads(call.data)
    method = data[0]

    if method == "GE":  # получение событий которые проходят сегодня
        limit, offset, date, period, message_id, category = data[1:]
        events = getEventsInCityWithPeriod(
            "perm",
            datetime.strptime(date, "%Y-%m-%d"),
            limit=limit,
            offset=offset,
            period=period,
            category=category,
        )
        isToday = date == datetime.today().strftime("%Y-%m-%d")
        message = f"<b>События {'сегодня' if isToday else datetime.strptime(date, "%Y-%m-%d").strftime("%d %B %Y")}:</b>\n"
        for event in events:
            message += (
                f"Название: <a href=\"{event['url']}\">\"{event['name']}\"</a>\n"
                + f"Дата: {event["dates"][0].strftime("%d %B %Y") if period > 1 else ('сегодня' if isToday else datetime.strptime(date, "%Y-%m-%d").strftime("%d %B %Y"))}\n"
                + (
                    f"Время: с {event['times'][0]} до {event['times'][-1]}\n"
                    if len(event["times"]) > 1
                    else ""
                )
                + f"Место: <a href=\"{event['oneOfPlaces']['url']}\">{event['oneOfPlaces']['title']}</a>\n"
                + f"Категория: {event['type']['name']}\n"
                + (
                    f"Цена: от {event['tickets'][0]['price']['min']//100} до {event['tickets'][0]['price']['max']//100} {currencies[event['tickets'][0]['price']['currency']]}"
                    if len(event["tickets"]) > 0
                    else ""
                )
                + "\n\n"
            )
        if len(events) == 0:
            message += "    Событий нет или они закончились :("
        if message_id == -1:
            markup = make_pagination_markup(
                method, limit, offset, date, period, message_id, category
            )
            m = bot.send_message(
                call.message.chat.id,
                message,
                parse_mode="HTML",
                reply_markup=markup,
                link_preview_options=types.LinkPreviewOptions(is_disabled=True),
            )
            message_id = m.message_id
        markup = make_pagination_markup(
            method, limit, offset, date, period, message_id, category
        )
        m = bot.edit_message_text(
            message,
            call.message.chat.id,
            message_id,
            parse_mode="HTML",
            reply_markup=markup,
            link_preview_options=types.LinkPreviewOptions(is_disabled=True),
        )
    elif method == "GEC":  # получение категорий
        category = data[1]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "На сегодня",
                callback_data=json.dumps(
                    [
                        "GE",
                        10,
                        0,
                        datetime.today().strftime("%Y-%m-%d"),
                        1,
                        -1,
                        category,
                    ]
                ),
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "На завтра",
                callback_data=json.dumps(
                    [
                        "GE",
                        10,
                        0,
                        (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
                        1,
                        -1,
                        category,
                    ]
                ),
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "На 7 дней",
                callback_data=json.dumps(
                    [
                        "GE",
                        10,
                        0,
                        datetime.today().strftime("%Y-%m-%d"),
                        7,
                        -1,
                        category,
                    ]
                ),
            )
        )
        msg = bot.send_message(
            call.message.chat.id,
            f'Выберите на какой день или какие дни вы хотите узнать события в категории "{categories[category]}": ',
            reply_markup=markup,
        )


bot.polling(none_stop=True)
