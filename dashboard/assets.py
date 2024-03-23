#   const---------------------------------------------------------------------------------------------------------------
ADMINISTRATOR = 'administrator'
FOREMAN = 'foreman'
MASTER = 'master'
DRIVER = 'driver'
MECHANIC = 'mechanic'
SUPPLY = 'supply'
EMPLOYEE = 'employee'

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


WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")


ERROR_MESSAGES = {
    'login': 'Неверный логин или пароль',
    'register': 'Введены не все данные',
}
