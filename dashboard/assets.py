from .types import Enum, TitleDescriptionType, UserPostType, ApplicationTodayType

#   const---------------------------------------------------------------------------------------------------------------
# ADMINISTRATOR = 'administrator'
# FOREMAN = 'foreman'
# MASTER = 'master'
# DRIVER = 'driver'
# MECHANIC = 'mechanic'
# SUPPLY = 'supply'
# EMPLOYEE = 'employee'

# VAR_APPS_SEND = 'var_apps_send'
# VAR_DEFAULT_PASSWORD = '1234'

UserPosts = UserPostType(
    TitleDescriptionType('administrator', 'Администратор'),
    TitleDescriptionType('foreman', 'Прораб'),
    TitleDescriptionType('master', 'Мастер'),
    TitleDescriptionType('driver', 'Водитель'),
    TitleDescriptionType('mechanic', 'Механик'),
    TitleDescriptionType('supply', 'Снабжение'),
    TitleDescriptionType('employee', 'Работник')
)

ApplicationTodayStatus = ApplicationTodayType(
    TitleDescriptionType('absent', 'Отсутствует'),
    TitleDescriptionType('saved', 'Сохранена'),
    TitleDescriptionType('submitted', 'Подана'),
    TitleDescriptionType('approved', 'Одобрена'),
    TitleDescriptionType('send', 'Отправлена')
)

# USER_POSTS_set = (ADMINISTRATOR, FOREMAN, MASTER, DRIVER, MECHANIC, SUPPLY, EMPLOYEE)
# USER_POSTS_dict = {
#     ADMINISTRATOR: 'Администратор',
#     FOREMAN: 'Прораб',
#     MASTER: 'Мастер',
#     DRIVER: 'Водитель',
#     MECHANIC: 'Механик',
#     SUPPLY: 'Снабжение',
#     EMPLOYEE: 'Работник'
# }

# ABSENT = 'absent'
# SAVED = 'saved'
# SUBMITTED = 'submitted'
# APPROVED = 'approved'
# SEND = 'send'

# APPLICATION_STATUS_set = (ABSENT, SAVED, SUBMITTED, APPROVED, SEND)
# APPLICATION_STATUS_dict = {
#     ABSENT: 'Отсутствует',
#     SAVED: 'Сохранена',
#     SUBMITTED: 'Подана',
#     APPROVED: 'Одобрена',
#     SEND: 'Отправлена'}

SORT_BY = {'driver': 'Водителю', 'technic': 'Технике'}

WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
MONTHS = (
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')


class ErrorMessages(Enum):
    invalid_signin = 'Неверный логин или пароль'
    invalid_register = 'Введены не все данные'


class MessagesAssets(Enum):
    reject = 'ОТКЛОНЕНА\n'
    CS_SUPPLY_TITLE = 'Снабжение'
    CS_SPEC_TITLE = 'Спец. задание'
    CS_SPEC_DEFAULT_DESC = 'Дробить бетон и асфальт'


class ViewMode(Enum):
    FUTURE = 'view_mode_future'
    CURRENT = 'view_mode_current'
    ARCHIVE = 'view_mode_archive'


COLORS = (
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
)
