import datetime

from .types import Enum, TitleDescriptionType, UserPostType, ApplicationTodayType

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
    TitleDescriptionType('deleted', 'Удалена'),
    TitleDescriptionType('absent', 'Отсутствует'),
    TitleDescriptionType('saved', 'Сохранена'),
    TitleDescriptionType('submitted', 'Подана'),
    TitleDescriptionType('approved', 'Одобрена'),
    TitleDescriptionType('send', 'Отправлена')
)
SHOW_APPLICATIONS_WITH_STATUSES = (ApplicationTodayStatus.APPROVED.title, ApplicationTodayStatus.SEND.title)
SHOW_APPLICATIONS_FOR_SUPPLY_WITH_STATUSES = (
    ApplicationTodayStatus.SUBMITTED.title,
    ApplicationTodayStatus.APPROVED.title,
    ApplicationTodayStatus.SEND.title)
SHOW_APPLICATIONS_FOR_MECHANIC_WITH_STATUSES = SHOW_APPLICATIONS_FOR_SUPPLY_WITH_STATUSES

SORT_BY = {'driver': 'Водителю', 'technic': 'Технике'}

WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
MONTHS = (
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')
MONTHS_T = (
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября','декабря')

TIME_REDIRECT_DASHBOARD_FOR_FOREMAN = datetime.time(hour=10, minute=0)
TIME_REDIRECT_DASHBOARD_FOR_MECHANIC = datetime.time(hour=10, minute=0)
TIME_REDIRECT_DASHBOARD_FOR_DRIVER = datetime.time(hour=19, minute=0)
TIME_REDIRECT_DASHBOARD_FOR_EMPLOYEE = datetime.time(hour=17, minute=0)


class ErrorMessages(Enum):
    invalid_signin = 'Неверный логин или пароль'
    invalid_register = 'Введены не все данные'
    user_already_exists = 'Данный пользователь уже существует'


class MessagesAssets(Enum):
    reject = 'ОТКЛОНЕНА\n'
    CS_SUPPLY_TITLE = 'Снабжение'
    CS_SPEC_TITLE = 'Спец. задание'
    CS_SPEC_DEFAULT_DESC = 'Дробить бетон и асфальт'


class ViewMode(Enum):
    FUTURE = 'view_mode_future'
    CURRENT = 'view_mode_current'
    ARCHIVE = 'view_mode_archive'


class AcceptMode(Enum):
    AUTO = 'auto'
    MANUAL = 'manual'
    OFF = 'off'


class TaskDescriptionMode(Enum):
    AUTO = 'auto'
    DEFAULT = 'default'
    MANUAL = 'manual'


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


class UserEditResult(Enum):
    OK = 'ok'
    EXISTS = 'exists'
    ERROR = 'error'

