#   const---------------------------------------------------------------------------------------------------------------
ADMINISTRATOR = 'administrator'
FOREMAN = 'foreman'
MASTER = 'master'
DRIVER = 'driver'
MECHANIC = 'mechanic'
SUPPLY = 'supply'
EMPLOYEE = 'employee'

# VAR_APPS_SEND = 'var_apps_send'
# VAR_DEFAULT_PASSWORD = '1234'

USER_POSTS_set = (ADMINISTRATOR, FOREMAN, MASTER, DRIVER, MECHANIC, SUPPLY, EMPLOYEE)
USER_POSTS_dict = {
    ADMINISTRATOR: 'Администратор',
    FOREMAN: 'Прораб',
    MASTER: 'Мастер',
    DRIVER: 'Водитель',
    MECHANIC: 'Механик',
    SUPPLY: 'Снабжение',
    EMPLOYEE: 'Работник'
}

ABSENT = 'absent'
SAVED = 'saved'
SUBMITTED = 'submitted'
APPROVED = 'approved'
SEND = 'send'

APPLICATION_STATUS_set = (ABSENT, SAVED, SUBMITTED, APPROVED, SEND)
APPLICATION_STATUS_dict = {
    ABSENT: 'Отсутствует',
    SAVED: 'Сохранена',
    SUBMITTED: 'Подана',
    APPROVED: 'Одобрена',
    SEND: 'Отправлена'}

SORT_BY = {'driver': 'Водителю', 'technic': 'Технике'}

WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
MONTHS = (
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')

ERROR_MESSAGES = {
    'login': 'Неверный логин или пароль',
    'register': 'Введены не все данные',
}
MESSAGES = {
    'reject': 'ОТКЛОНЕНА\n'
}

CS_SUPPLY_TITLE = 'Снабжение'
CS_SPEC_TITLE = 'Спец. задание'
CS_SPEC_DEFAULT_DESC = 'Дробить бетон и асфальт'


COLORS = [
    '#15b03e',
    '#5a9e6c',
    '#85d633',
    '#2b5403',
    '#f0dc05',
    '#fa9600',
    '#fa4f00',
    '#fa0400',
    '#00fae1',
    '#008efa',
    '#001dfa',
    '#9600fa',
    '#fa00ed',
]

#   -------------------------------------------------------------
VIEW_MODE_FUTURE = 'view_mode_future'
VIEW_MODE_CURRENT = 'view_mode_current'
VIEW_MODE_ARCHIVE = 'view_mode_archive'
#   -------------------------------------------------------------
