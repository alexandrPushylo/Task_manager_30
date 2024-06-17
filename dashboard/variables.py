# template = {'title': '', 'name': ''}
from datetime import datetime

VAR_APPLICATION_SEND = {
    'title': 'Отметка отправки приложений',
    'name': 'apps_status_send'
}
VAR_DEFAULT_PASSWORD = {
    'title': 'Пароль по умолчанию',
    'name': 'default_password',
    'value': '1234',
}
VAR_TIME_RECEPTION_OF_APPS = {
    'title': 'Время приема заявок',
    'name': 'time_reception_of_applications',
    'time': datetime.now().time().replace(hour=16, minute=0, second=0, microsecond=0),
    'flag': True,
}

# Для prepare_variables() - automatic creation of variables
VARIABLES_LIST = (
    # VAR_APPLICATION_SEND,
    VAR_DEFAULT_PASSWORD,
    VAR_TIME_RECEPTION_OF_APPS,
)
