import requests  # Импортируем библиотеку для выполнения HTTP-запросов
import time  # Импортируем библиотеку для работы со временем (задержки)
import json  # Импортируем библиотеку для работы с JSON-данными

# Токен Telegram-бота (уникальный идентификатор для работы с API)
TOKEN = '7680395003:AAFDsDd1KzrREdG-529OUIiRw2xqz2afwx0'
# Базовый URL API Telegram для выполнения запросов
URL = f'https://api.telegram.org/bot{TOKEN}/'

# Словарь для хранения состояния пользователей (например, ожидает ли бот ввода текста)
user_states = {}

def reply_keyboard(chat_id, text):
    """
    Функция для отправки сообщения с встроенной клавиатурой.
    :param chat_id: ID чата, куда отправить сообщение
    :param text: Текст сообщения
    """
    reply_markup = {
        "keyboard": [
            [{"text": "О боте"}],  # Кнопка для отображения информации о боте
            [{"text": "Где я нахожусь", "request_location": True}],  # Кнопка для отправки геолокации
            [{"text": "Отправить другую геопозицию (геопозицией или текстом)"}]  # Кнопка для ввода нового адреса
        ],
        "resize_keyboard": True,  # Клавиатура будет подстраиваться по размеру экрана
        "one_time_keyboard": False,  # Клавиатура не скрывается после нажатия
        "input_field_placeholder": "Используйте кнопки"  # Подсказка в поле ввода
    }
    data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    requests.post(f'{URL}sendMessage', data=data)  # Отправляем сообщение с клавиатурой

def get_updates(offset=0):
    """
    Функция для получения новых сообщений от Telegram API.
    :param offset: ID последнего обработанного сообщения (чтобы не получать дубликаты)
    :return: Список новых сообщений
    """
    result = requests.get(f'{URL}getUpdates?offset={offset}').json()
    return result.get('result', [])  # Если нет новых сообщений, вернёт пустой список

def send_message(chat_id, text):
    """
    Функция для отправки текстового сообщения пользователю.
    :param chat_id: ID чата
    :param text: Текст сообщения
    """
    requests.get(f'{URL}sendMessage?chat_id={chat_id}&text={text}')

def check_message(chat_id, message):
    """
    Функция для обработки текстовых сообщений пользователя.
    :param chat_id: ID чата пользователя
    :param message: Текст сообщения пользователя
    """
    global user_states  # Используем глобальный словарь состояний пользователей

    if message.lower() == '/start':  # Если пользователь запустил бота
        user_states.pop(chat_id, None)  # Сбрасываем состояние пользователя
        send_message(chat_id, "Привет! Я бот, который поможет тебе узнать о поэтах Петербурга.")
        reply_keyboard(chat_id, "Выберите действие")  # Отправляем клавиатуру

    elif message.lower() == 'о боте':  # Информация о боте
        send_message(chat_id, 'Этот бот поможет тебе подробнее ознакомиться с творчеством поэтов о Санкт-Петербурге.')
        reply_keyboard(chat_id, "Выберите действие")  # Показываем клавиатуру снова

    elif message.lower() == 'отправить другую геопозицию (геопозицией или текстом)':
        send_message(chat_id, 'Отправьте геометку или введите место текстом.')
        user_states[chat_id] = 'awaiting_address'  # Устанавливаем состояние ожидания ввода адреса

    elif chat_id in user_states and user_states[chat_id] == 'awaiting_address':
        # Если пользователь отправил текстовый адрес
        location_info = geocode_address(message)
        if location_info:
            send_message(chat_id, location_info)  # Отправляем информацию о местоположении
            user_states[chat_id] = 'default'  # Сбрасываем состояние
        else:
            send_message(chat_id, "Не удалось найти адрес, попробуйте еще раз.")  # Ошибка поиска

    else:
        reply_keyboard(chat_id, 'Используйте кнопки для взаимодействия.')  # Если сообщение не распознано

def geocode_address(address):
    """
    Функция для поиска координат по текстовому адресу через API LocationIQ.
    :param address: Адрес в виде строки
    :return: Найденный адрес и его координаты (или None, если не найдено)
    """
    token = 'pk.c198157a80eda06853578215b58c41d1'
    headers = {"Accept-Language": "ru"}
    response = requests.get(
        f'https://eu1.locationiq.com/v1/search.php?key={token}&q={address}&format=json',
        headers=headers
    ).json()
    if response and isinstance(response, list):
        place = response[0]
        return f'Адрес найден: {place.get("display_name")}. Координаты: {place.get("lat")}, {place.get("lon")}.'
    return None

def geocoder(latitude, longitude):
    """
    Функция для поиска адреса по координатам через API LocationIQ.
    :param latitude: Широта
    :param longitude: Долгота
    :return: Полный адрес местоположения
    """
    token = 'pk.c198157a80eda06853578215b58c41d1'
    headers = {"Accept-Language": "ru"}
    address = requests.get(
        f'https://eu1.locationiq.com/v1/reverse.php?key={token}&lat={latitude}&lon={longitude}&format=json',
        headers=headers
    ).json()
    return f'Твое местоположение: {address.get("display_name")}'  # Возвращаем полный адрес

def run():
    """
    Основная функция работы бота. Циклически проверяет новые сообщения и обрабатывает их.
    """
    update_id = 0  # Переменная для хранения последнего обработанного сообщения
    while True:
        time.sleep(2)  # Задержка между запросами к Telegram API (чтобы не перегружать сервер)
        messages = get_updates(update_id)  # Получаем новые сообщения
        for message in messages:
            if update_id < message['update_id']:  # Проверяем, обработано ли сообщение
                update_id = message['update_id']  # Обновляем ID последнего обработанного сообщения
                chat_id = message['message']['chat']['id']  # ID чата пользователя
                user_message = message['message'].get('text')  # Получаем текст сообщения

                if user_message:  # Если сообщение текстовое
                    check_message(chat_id, user_message)  # Обрабатываем текст

                user_location = message['message'].get('location')  # Получаем геолокацию (если есть)
                if user_location:  # Если пользователь отправил геопозицию
                    latitude = user_location['latitude']
                    longitude = user_location['longitude']
                    send_message(chat_id, geocoder(latitude, longitude))  # Отправляем адрес

# Запуск бота при запуске файла
if __name__ == '__main__':
    run()
