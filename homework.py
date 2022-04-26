import logging
import os
import requests
import sys
import telegram
import time
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv('token_practicum')
TELEGRAM_TOKEN = os.getenv('token_telega')
TELEGRAM_CHAT_ID = os.getenv('id_telega')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отвечающая за отрпавку сообщений в телеграм."""
    chat_id = TELEGRAM_CHAT_ID
    bot.send_message(chat_id, message)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise requests.HTTPError(response)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) is not dict:
        raise TypeError('Ответ получен не в виде словаря')
    key = 'homeworks'
    if key not in response.keys():
        raise KeyError(f'В response нет ключа {key}')
    if type(response[key]) is not list:
        raise TypeError('Домашняя работа получена не в виде списка')
    return response[key]


def parse_status(homework):
    """Извлекает информацию о статусе домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES.keys():
        raise KeyError(('Недокументированный статус домашней '
                        f'работы: {homework_status}'))
    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if (PRACTICUM_TOKEN is None) or (TELEGRAM_TOKEN is None) or \
            (TELEGRAM_CHAT_ID is None):
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные окружения!')
        return

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('Нет обновлений в статусах работ')
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
                logger.info(('Сообщение отправленно в телеграм: '
                             f'{message}'))

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if last_error_message != message:
                try:
                    send_message(bot, message)
                    last_error_message = message
                except Exception:
                    pass
            time.sleep(RETRY_TIME)
        else:
            logger.error('Сбой в работе программы')


if __name__ == '__main__':
    main()
