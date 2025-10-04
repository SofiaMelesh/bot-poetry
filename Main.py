import requests
import time
import json
import random
import mysql.connector
import re

TOKEN = ''
URL = f''

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="poetry"
)

cursor = db.cursor(buffered=True)
user_states = {}


def reply_keyboard(chat_id, text, menu_type="main"):
    if menu_type == "main":
        reply_markup = {
            "keyboard": [
                [{"text": "О боте"}],
                [{"text": "Просмотреть все стихотворения"}],
                [{"text": "Где я нахожусь", "request_location": True}],
                [{"text": "Отправить другую геопозицию (геопозицией или текстом)"}],
                [{"text": "Карта стихов"}],
                [{"text": "Маршрут по следам Ахматовой"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    elif menu_type == "poem_map":
        reply_markup = {
            "keyboard": [
                [{"text": "Показать Санкт-Петербург ближе"}],
                [{"text": "Вернуться назад"}]  # Убрал кнопку Ахматовой отсюда
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

    data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    requests.post(f'{URL}sendMessage', data=data)


def send_photo(chat_id, photo_url, caption):
    try:
        print(f"Пытаюсь отправить фото по URL: {photo_url}")  # Логируем URL

        data = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        response = requests.post(f'{URL}sendPhoto', data=data)

        print(f"Ответ от Telegram API: {response.status_code}, {response.text}")  # Логируем ответ

        if response.status_code != 200:
            send_message(chat_id, f"⚠️ Ошибка отправки фото. Код: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке фото: {str(e)}")
        send_message(chat_id, "⚠️ Произошла ошибка при отправке изображения")


def show_poem_map(chat_id):
    # Здесь должны быть реальные URL ваших изображений
    map_image = "https://ibb.co/VchGK9mb"
    caption = """
🗺️ <b>Карта поэтического Петербурга и Ленинградской области</b>

На карте приблизительно отмечены:
- Улицы, которым посвящены стихи
- Районы, связанные с поэтическими произведениями
- Знаковые места, вдохновлявшие поэтов

ℹ️ <i>Даже если ваше местоположение не отмечено на карте - попробуйте! 
В нашей базе есть стихи со всего региона, и мы обязательно что-нибудь подберем.</i>

"""
    send_photo(chat_id, map_image, caption)
    reply_keyboard(chat_id, "Выберите действие:", "poem_map")

def show_spb_closer(chat_id):
    image_url = "https://ibb.co/VnJGPJj"
    caption = """
🏙️ <b>Сердце поэтического Петербурга</b>

Здесь, в историческом центре города, вы найдёте <b>самую высокую концентрацию</b> стихов и поэтических мест:

📍 <b>Ключевые точки на карте:</b>
- Дворцовая площадь и Эрмитаж
- Летний сад и набережные Невы
- Петропавловская крепость
- Невский проспект и канал Грибоедова

📜 <b>Этим местам посвящали стихи:</b>
• Пушкин • Ахматова • Блок • Бродский • Мандельштам

✨ <b>Обязательно посетите эти места с нашим ботом!</b> 
Отправьте геолокацию, когда будете там, и получите соответствующие стихотворения.

<i>Каждый камень здесь дышит поэзией, и мы поможем вам её услышать!</i>
"""
    send_photo(chat_id, image_url, caption)
    # Возвращаем стандартные кнопки после просмотра
    reply_keyboard(chat_id, "Выберите действие:")

def show_akhmatova_route(chat_id):
    image_url = "https://imgur.com/a/KefWO9L"
    caption = """
👣 <b>Маршрут по следам Анны Ахматовой</b>

📍 <b>Точки маршрута:</b>
1. Старт: <i>Воскресенская набережная, 14</i> (Дом, где жила Ахматова)
2. Финиш: <i>Биржевая площадь, 4</i> (Рядом с легендарной "Бродячей собакой")

🚶‍♀️ <b>Маршрут проходит по улицам:</b>
- Набережная реки Фонтанки
- Дворцовая набережная
- Университетская набережная
- Биржевой переулок

📜 <b>Этим местам Ахматова посвятила стихи:</b>
"Летний сад", "Смятение", "Эпические мотивы", "Петербург в 1913 году"

ℹ️ Протяженность маршрута достаточно большая. Это отличная поэтическая прогулка на 3-5 часов!

Хорошего путешествия по следам великой поэтессы! ✨
"""
    send_photo(chat_id, image_url, caption)
    # Возвращаем стандартные кнопки после просмотра
    reply_keyboard(chat_id, "Выберите действие:")


def send_message(chat_id, text, reply_markup=None):
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    requests.post(f'{URL}sendMessage', data=data)


def send_inline_keyboard(chat_id, text, options):
    keyboard = []
    for option in options:
        keyboard.append([{"text": option["text"], "callback_data": option["callback_data"]}])

    reply_markup = {
        "inline_keyboard": keyboard
    }

    send_message(chat_id, text, reply_markup)


def escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_poems(results):
    formatted = []
    for name, author, text in results:
        poem_message = (
            "📜 <b>Стихотворение:</b> <i>{}</i>\n"
            "✍️ <b>Автор:</b> <i>{}</i>\n\n"
            "📝 <pre>{}</pre>"
        ).format(escape_html(name), escape_html(author), escape_html(text))
        formatted.append(poem_message)
    return "\n\n".join(formatted)


def get_all_poems_list():
    cursor.execute("""
        SELECT p.poem_name, p.poem_author, p.poem_text, 
               COALESCE(d.title, s.street_title, 'Санкт-Петербург') as location
        FROM poems p
        LEFT JOIN district d ON p.district_id = d.district_id
        LEFT JOIN street s ON p.street_id = s.street_id
        ORDER BY p.poem_author, p.poem_name
    """)
    return cursor.fetchall()


def get_poem_by_name_and_author(poem_name, poem_author):
    cursor.execute("""
        SELECT p.poem_name, p.poem_author, p.poem_text, 
               COALESCE(d.title, s.street_title, 'Санкт-Петербург') as location
        FROM poems p
        LEFT JOIN district d ON p.district_id = d.district_id
        LEFT JOIN street s ON p.street_id = s.street_id
        WHERE p.poem_name = %s AND p.poem_author = %s
    """, (poem_name, poem_author))
    return cursor.fetchone()


def send_poems_list(chat_id):
    poems = get_all_poems_list()
    if not poems:
        send_message(chat_id, "В базе данных нет стихотворений.")
        return

    poems_list = []
    for idx, (name, author, _, location) in enumerate(poems, 1):
        poems_list.append(
            f"{idx}. <b>{escape_html(author)}</b> - {escape_html(name)}\n"
            f"   📍 {escape_html(location)}"
        )

    message = (
            "📚 <b>Список всех стихотворений:</b>\n\n" +
            "\n\n".join(poems_list) +
            "\n\nВведите номер стихотворения для просмотра:"
    )

    user_states[chat_id] = {
        'state': 'awaiting_poem_selection',
        'poems': poems
    }

    send_message(chat_id, message)


def send_selected_poem(chat_id, poem_number):
    state = user_states.get(chat_id, {})
    if state.get('state') != 'awaiting_poem_selection':
        send_message(chat_id, "Пожалуйста, сначала запросите список стихотворений.")
        return

    poems = state.get('poems', [])
    if not poems:  # Дополнительная проверка
        send_message(chat_id, "Список стихов пуст. Запросите список заново.")
        return
    try:
        poem_number = int(poem_number)
        if 1 <= poem_number <= len(poems):
            poem_name, poem_author, _, location = poems[poem_number - 1]
            poem_info = get_poem_by_name_and_author(poem_name, poem_author)
            if poem_info:
                name, author, text, location = poem_info
                message = (
                    "📜 <b>Стихотворение:</b> <i>{}</i>\n"
                    "✍️ <b>Автор:</b> <i>{}</i>\n"
                    "📍 <b>Место:</b> <i>{}</i>\n\n"
                    "📝 <pre>{}</pre>"
                ).format(
                    escape_html(name),
                    escape_html(author),
                    escape_html(location),
                    escape_html(text)
                )
                send_message(chat_id, message)

                # Ask the user if they want to select another poem
                send_message(chat_id, "Хотите выбрать другое стихотворение? Введите номер.")
            else:
                send_message(chat_id, "Стихотворение не найдено.")
        else:
            send_message(chat_id, f"Пожалуйста, введите число от 1 до {len(poems)}")
    except ValueError:
        send_message(chat_id, "Пожалуйста, введите номер стихотворения цифрами.")


def normalize(text):
    return re.sub(r'[^а-яёa-z0-9 ]', '', text.lower()).strip()


def check_message(chat_id, message):
    global user_states

    if message.lower() == '/start':
        user_states.pop(chat_id, None)
        send_message(chat_id, "Привет! Я бот, который поможет тебе узнать о поэтах Петербурга.")
        reply_keyboard(chat_id, "Выберите действие")

    elif message.lower() == 'карта стихов':
        show_poem_map(chat_id)
        user_states[chat_id] = None

    elif message.lower() == 'маршрут по следам ахматовой':  # Обновил проверку
        show_akhmatova_route(chat_id)
        user_states[chat_id] = None

    elif message.lower() == 'показать санкт-петербург ближе':
        show_spb_closer(chat_id)
        user_states[chat_id] = None

    elif message.lower() == 'вернуться назад':
        reply_keyboard(chat_id, "Выберите действие")
        user_states[chat_id] = None

    elif message.lower() == 'о боте':
        bot_info = """
        <b>📚 Петербургские строки</b>

        Я собираю стихи как пазл города - из каждой улицы, каждого двора. 

        Просто отправь мне:
        📍 Свою геопозицию 
        🏛 Название места
        📖 Или выбери стихотворение из полной коллекции

        Я покажу тебе Петербург глазами поэтов - от Пушкина до Бродского.

        Найди поэзию вокруг себя!
        """
        send_message(chat_id, bot_info)
        reply_keyboard(chat_id, "Выберите действие")
        user_states[chat_id] = None

    elif message.lower() == 'отправить другую геопозицию (геопозицией или текстом)':
        send_message(chat_id, 'Отправьте геометку или введите место текстом.')
        user_states[chat_id] = 'awaiting_address'

    elif message.lower() == 'просмотреть все стихотворения':
        poems = get_all_poems_list()  # Получаем список стихов
        if not poems:
            send_message(chat_id, "В базе данных нет стихотворений.")
            return

        # Сохраняем И состояние, И список стихов
        user_states[chat_id] = {
            'state': 'awaiting_poem_selection',
            'poems': poems  # Важно: сохраняем список!
        }

        # Формируем и отправляем список пользователю
        poems_list = []
        for idx, (name, author, _, location) in enumerate(poems, 1):
            poems_list.append(
                f"{idx}. <b>{escape_html(author)}</b> - {escape_html(name)}\n"
                f"   📍 {escape_html(location)}"
            )

        message = "📚 <b>Список всех стихотворений:</b>\n\n" + "\n\n".join(poems_list)
        send_message(chat_id, message + "\n\nВведите номер стихотворения для просмотра:")

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
                # Отправляем inline-клавиатуру с кнопками Да/Нет
                options = [
                    {"text": "Да", "callback_data": "address_confirm_yes"},
                    {"text": "Нет", "callback_data": "address_confirm_no"}
                ]
                send_inline_keyboard(chat_id, f"{address}\n\nЭто тот адрес?", options)
            else:
                send_message(chat_id, "Не удалось найти адрес, попробуйте еще раз.")

        elif isinstance(state, dict) and state.get('state') == 'awaiting_poem_selection':
            send_selected_poem(chat_id, message)
            # Keep the user in the same state to allow repeated poem selection
            user_states[chat_id]['state'] = 'awaiting_poem_selection'
        else:
            reply_keyboard(chat_id, 'Используйте кнопки для взаимодействия.')
            user_states[chat_id] = None
    else:
        reply_keyboard(chat_id, 'Используйте кнопки для взаимодействия.')


def handle_callback_query(callback_query):
    chat_id = callback_query['message']['chat']['id']
    callback_data = callback_query['data']
    message_id = callback_query['message']['message_id']

    if callback_data == 'address_confirm_yes':
        state = user_states.get(chat_id, {})
        if isinstance(state, dict) and state.get('state') == 'awaiting_confirmation':
            address = state['address_info']
            poem = get_poem_by_location(address)
            # Удаляем сообщение с кнопками
            requests.post(f'{URL}deleteMessage', json={
                'chat_id': chat_id,
                'message_id': message_id
            })
            send_message(chat_id, poem)
            user_states[chat_id] = 'default'
            reply_keyboard(chat_id, "Выберите действие:")

    elif callback_data == 'address_confirm_no':
        # Удаляем сообщение с кнопками
        requests.post(f'{URL}deleteMessage', json={
            'chat_id': chat_id,
            'message_id': message_id
        })
        send_message(chat_id, "Хорошо, введите адрес снова (уточните):")
        user_states[chat_id] = 'awaiting_address'


def get_updates(offset=0):
    result = requests.get(f'{URL}getUpdates?offset={offset}').json()
    print(f"Ответ от getUpdates: {json.dumps(result, indent=2)}")
    return result.get('result', [])


def geocode_address(address):
    token = 'pk.c198157a80eda06853578215b58c41d1'
    headers = {"Accept-Language": "ru"}
    response = requests.get(
        f'https://eu1.locationiq.com/v1/search.php?key={token}&q={address}&format=json',
        headers=headers
    ).json()
    print(f"Ответ от геокодирования: {json.dumps(response, indent=2)}")
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
    print(f"Ответ от реверс-геокодирования: {json.dumps(address, indent=2)}")
    return address.get("display_name")


def get_poem_by_location(address):
    debug_output = []
    debug_output.append(f"📍 Полученный адрес: {address}")
    if address is None:
        return "Не удалось получить адрес."
    # Проверка на принадлежность к Санкт-Петербургу или Ленинградской области
    if 'санкт-петербург' not in address.lower() and 'петербург' not in address.lower():
        if 'ленинградская область' not in address.lower():
            return (
                "🌍 Кажется, вы находитесь не в Ленинградской области.\n\n"
                "📝 Этот бот предназначен для знакомства со стихами, посвящёнными Санкт-Петербургу "
                "и его районам, включая Ленинградскую область.\n\n"
                "📍 Пожалуйста, отправьте геолокацию или адрес, относящийся к этому региону."
            )

    normalized_address = normalize(address)
    found_poems = []

    # Поиск по улицам с более строгим совпадением
    cursor.execute("SELECT street_id, street_title, district_id FROM street")
    streets = cursor.fetchall()

    matched_streets = []
    for street_id, street_title, district_id in streets:
        street_words = normalize(street_title).split()
        address_words = normalized_address.split()

        common_words = set(street_words) & set(address_words)
        if common_words:
            matched_streets.append((street_id, street_title, district_id, len(common_words)))

    matched_streets.sort(key=lambda x: x[3], reverse=True)

    if matched_streets:
        street_id, street_title, district_id, _ = matched_streets[0]
        debug_output.append(f"🏙 Найдена улица: {street_title} (ID: {street_id})")

        cursor.execute("""
            SELECT poem_name, poem_author, poem_text 
            FROM poems 
            WHERE street_id = %s
            ORDER BY RAND() 
            LIMIT 3
        """, (street_id,))
        street_poems = cursor.fetchall()

        if street_poems:
            debug_output.append(f"📖 Найдено {len(street_poems)} стихов по улице {street_title}")
            found_poems.extend(street_poems)
        else:
            debug_output.append(f"ℹ️ Для улицы {street_title} не найдено стихов")

    # Поиск по району, если стихов по улице нет
    if not found_poems:
        cursor.execute("""
            SELECT poem_name, poem_author, poem_text
            FROM poems 
            WHERE district_id = %s
            ORDER BY RAND() 
            LIMIT 3
        """, (district_id,))
        district_poems = cursor.fetchall()

        if district_poems:
            debug_output.append(f"📚 Найдено {len(district_poems)} стихов по району с ID {district_id}")
            found_poems.extend(district_poems)
        else:
            debug_output.append(f"ℹ️ Для района с ID {district_id} не найдено стихов")

    # Если ничего не найдено, показываем случайные стихотворения из района 25
    if not found_poems:
        debug_output.append("🔍 Не удалось найти стихи по точному адресу. Показываю случайные:")

        cursor.execute("""
            SELECT poem_name, poem_author, poem_text 
            FROM poems 
            WHERE district_id = 25 
            ORDER BY RAND() 
            LIMIT 3
        """)
        random_poems = cursor.fetchall()

        if random_poems:
            found_poems.extend(random_poems)
            debug_output.append(f"🎲 Выбрано {len(random_poems)} случайных стихотворений")
        else:
            debug_output.append("❌ В базе данных нет стихотворений")

    # Формируем итоговый ответ
    if found_poems:
        return "\n".join(debug_output) + "\n\n" + format_poems(found_poems)
    else:
        debug_output.append("❌ Не удалось найти подходящих стихотворений")
        return "\n".join(debug_output)



def run():
    update_id = None
    while True:
        time.sleep(3)
        messages = get_updates(update_id)

        if not messages:
            continue

        for message in messages:
            if 'update_id' not in message:
                continue

            update_id = message['update_id'] + 1

            # Обработка обычных сообщений
            if 'message' in message:
                chat_id = message['message'].get('chat', {}).get('id', None)
                if chat_id is None:
                    continue

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
                    user_states[chat_id] = None
                    reply_keyboard(chat_id, "Выберите действие:")


            # Обработка callback-запросов от inline-кнопок
            elif 'callback_query' in message:
                handle_callback_query(message['callback_query'])


if __name__ == '__main__':
    run()
