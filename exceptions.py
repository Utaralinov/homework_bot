class SendMessageError(Exception):
    def __init__(self, error):
        super().__init__(('Ошибка отправки сообщения в телеграм: '
                          f'{error}'))


class EndpointError(Exception):
    def __init__(self, error):
        super().__init__(f'Сбой при запросе к эндпойнту: {error}')


class JSONError(Exception):
    def __init__(self, response, error):
        super().__init__((f'Ответ {response} получен не в виде JSON: '
                         f'{error}'))
