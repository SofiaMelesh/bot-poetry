import requests
import time
import json
import random
import mysql.connector

TOKEN = '7680395003:AAFDsDd1KzrREdG-529OUIiRw2xqz2afwx0'
URL = f'https://api.telegram.org/bot{TOKEN}/'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Bim2005201725-",
    database="poetry"
)

cursor = db.cursor()
user_states = {}


def reply_keyboard(chat_id, text):
    reply_markup = {
        "keyboard": [
            [{"text": "О боте"}],
            [{"text": "Где я нахожусь", "request_location": True}],
            [{"text": "Отправить другую геопозицию (геопозицией или текстом)"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Используйте кнопки"
    }
    data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    requests.post(f'{URL}sendMessage', data=data)


def send_message(chat_id, text):
    requests.get(f'{URL}sendMessage?chat_id={chat_id}&text={text}')


def get_updates(offset=0):
    result = requests.get(f'{URL}getUpdates?offset={offset}').json()
    return result.get('result', [])


def geocode_address(address):
    token = 'pk.c198157a80eda06853578215b58c41d1'
    headers = {"Accept-Language": "ru"}
    response = requests.get(
        f'https://eu1.locationiq.com/v1/search.php?key={token}&q={address}&format=json',
        headers=headers
    ).json()
    if response and isinstance(response, list):
        place = response[0]
        return place['lat'], place['lon'], place.get("display_name")
    return None


def geocoder(latitude, longitude):
    token = 'pk.c198157a80eda06853578215b58c41d1'
    headers = {"Accept-Language": "ru"}
    address = requests.get(
        f'https://eu1.locationiq.com/v1/reverse.php?key={token}&lat={latitude}&lon={longitude}&format=json',
        headers=headers
    ).json()
    return address.get("display_name")


import random  # не забудь импортировать в начале файла

def get_poem_by_location(address):
    if 'санкт-петербург' not in address.lower() and 'петербург' not in address.lower():
        return (
            "🌍 Кажется, вы находитесь не в Санкт-Петербурге.\n\n"
            "📝 Этот бот предназначен для знакомства со стихами, посвящёнными Санкт-Петербургу "
            "и его районам, включая Ленинградскую область.\n\n"
            "📍 Пожалуйста, отправьте геолокацию или адрес, относящийся к этому региону."
        )

    # 1. Поиск по улице
    cursor.execute("SELECT street_id, street_title, district_id FROM street")
    street_rows = cursor.fetchall()

    for street_id, street_title, district_id in street_rows:
        if street_title.lower() in address.lower():
            # Поиск стихов по street_id
            cursor.execute(
                "SELECT poem_name, poem_author, poem_text FROM poems WHERE street_id = %s",
                (street_id,)
            )
            results = cursor.fetchall()
            if results:
                return format_poems(results)

            # Если по улице ничего нет, ищем по district_id этой улицы
            cursor.execute(
                "SELECT poem_name, poem_author, poem_text FROM poems WHERE district_id = %s",
                (district_id,)
            )
            district_results = cursor.fetchall()
            if district_results:
                return format_poems(district_results)

            break  # Нашли улицу, но ничего — не продолжаем искать другие улицы

    # 2. Если улицу не нашли — ищем по district напрямую
    cursor.execute("SELECT district_id, title FROM district")
    district_rows = cursor.fetchall()
    for district_id, title in district_rows:
        if title.lower() in address.lower():
            cursor.execute(
                "SELECT poem_name, poem_author, poem_text FROM poems WHERE district_id = %s",
                (district_id,)
            )
            results = cursor.fetchall()
            if results:
                return format_poems(results)

    # 3. Ничего не нашли — выводим случайное из района с ID 25
    cursor.execute("SELECT poem_name, poem_author, poem_text FROM poems WHERE district_id = 25")
    fallback = cursor.fetchall()
    if fallback:
        return format_poems([random.choice(fallback)])
    else:
        return "Ничего не найдено."



def format_poems(results):
    return "\n\n".join([f"Стихотворение: {name}\nАвтор: {author}\nТекст:\n{text}" for name, author, text in results])


def check_message(chat_id, message):
    global user_states

    if message.lower() == '/start':
        user_states.pop(chat_id, None)
        send_message(chat_id, "Привет! Я бот, который поможет тебе узнать о поэтах Петербурга.")
        reply_keyboard(chat_id, "Выберите действие")

    elif message.lower() == 'о боте':
        send_message(chat_id, 'Этот бот поможет тебе подробнее ознакомиться с творчеством поэтов о Санкт-Петербурге.')
        reply_keyboard(chat_id, "Выберите действие")

    elif message.lower() == 'отправить другую геопозицию (геопозицией или текстом)':
        send_message(chat_id, 'Отправьте геометку или введите место текстом.')
        user_states[chat_id] = 'awaiting_address'

    elif chat_id in user_states:
        state = user_states[chat_id]

        if state == 'awaiting_address':
            location_info = geocode_address(message)
            if location_info:
                lat, lon, address = location_info
                user_states[chat_id] = {
                    'state': 'awaiting_confirmation',
                    'address_info': address,
                    'latitude': lat,
                    'longitude': lon
                }
                send_message(chat_id, f"{address}\n\nЭто тот адрес? (да/нет)")
            else:
                send_message(chat_id, "Не удалось найти адрес, попробуйте еще раз.")

        elif isinstance(state, dict) and state.get('state') == 'awaiting_confirmation':
            if message.strip().lower() in ['да', 'yes', 'ок']:
                address = state['address_info']
                poem = get_poem_by_location(address)
                send_message(chat_id, poem)
                user_states[chat_id] = 'default'
            elif message.strip().lower() in ['нет', 'no']:
                send_message(chat_id, "Хорошо, введите адрес снова (уточните):")
                user_states[chat_id] = 'awaiting_address'
            else:
                send_message(chat_id, "Пожалуйста, ответьте 'да' или 'нет'.")
    else:
        reply_keyboard(chat_id, 'Используйте кнопки для взаимодействия.')


def run():
    update_id = 0
    while True:
        time.sleep(2)
        messages = get_updates(update_id)
        for message in messages:
            if update_id < message['update_id']:
                update_id = message['update_id']
                chat_id = message['message']['chat']['id']
                user_message = message['message'].get('text')

                if user_message:
                    check_message(chat_id, user_message)

                user_location = message['message'].get('location')
                if user_location:
                    latitude = user_location['latitude']
                    longitude = user_location['longitude']
                    address = geocoder(latitude, longitude)
                    send_message(chat_id, address)
                    poem = get_poem_by_location(address)
                    send_message(chat_id, poem)


if __name__ == '__main__':
    run()
