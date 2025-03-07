from django.db.utils import IntegrityError

from dashboard.models import User
from django.core.handlers.wsgi import WSGIRequest

import dashboard.assets as ASSETS
import dashboard.utilities as U
from django.db.models import QuerySet  # type: ignore

from logger import getLogger

log = getLogger(__name__)


def is_administrator(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.ADMINISTRATOR.title else False


def is_foreman(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.FOREMAN.title else False


def is_master(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.MASTER.title else False


def is_driver(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.DRIVER.title else False


def is_mechanic(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.MECHANIC.title else False


def is_supply(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.SUPPLY.title else False


def is_employee(user: User) -> bool:
    return True if user.post == ASSETS.UserPosts.EMPLOYEE.title else False


def get_foreman(user: User) -> User | None:
    """
    Получить объект типа: foreman от user или None
    :param user: foreman or master
    :return: foreman: User | None
    """
    if is_foreman(user):
        return user
    elif is_master(user):
        foreman = get_user(pk=user.supervisor_user_id)
        return foreman
    else:
        return None


def get_user(**kwargs) -> User:
    try:
        user = User.objects.get(**kwargs)
        return user
    except User.DoesNotExist:
        log.warning("get_user(): User.DoesNotExist ")
        return User.objects.none()
    except ValueError:
        log.error("get_user(): ValueError")
        return User.objects.none()


def get_user_queryset(select_related: tuple = (),
                      order_by: tuple = (),
                      **kwargs) -> QuerySet[User]:

    user = User.objects.filter(**kwargs)
    if select_related:
        user = user.select_related(*select_related)
    if order_by:
        user = user.order_by(*order_by)
    return user


def edit_user(user_id, data: dict) -> User:
    user = get_user(pk=user_id)
    if user:
        user.username = data['username']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.telephone = data['telephone']
        if data['password'] != user.password:
            user.set_password(data['password'])
        user.post = data['post']
        user.supervisor_user_id = data['supervisor_user_id']
        user.save()
        log.info(f"Пользователь {data['last_name']} {data['first_name']} был изменен")
        return user
    else:
        return User.objects.none()


def create_new_user(data: dict) -> User | None:
    try:
        user = User.objects.create_user(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            telephone=data['telephone'],
            password=data['password'],
            post=data['post'],
            supervisor_user_id=data['supervisor_user_id'],
            is_staff=False,
            is_superuser=False
        )
        log.info('Пользователь %s был добавлен' % data['last_name'])
        return user
    except IntegrityError:
        log.error('create_new_user(): IntegrityError; | username= [%s]', data['username'])
        return None


def check_user_data(user_data: WSGIRequest.POST) -> dict | None:
    log.info('Проверка user_data')
    username = user_data.get('username')
    first_name = str(user_data.get('first_name')).strip().capitalize()
    last_name = str(user_data.get('last_name')).strip().capitalize()
    telephone = user_data.get('telephone')
    password = user_data.get('password')
    post = user_data.get('post') if user_data.get('post') is not None else ASSETS.UserPosts.EMPLOYEE.title
    supervisor_user_id = int(user_data.get('supervisor_id')) if user_data.get('supervisor_id') is not None else None

    telephone = U.validate_telephone(telephone)

    if all((username, first_name, last_name, password)):
        log.info('Данные: (username, first_name, last_name, password) в порядке')
        return {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'telephone': telephone,
            'password': password,
            'post': post,
            'supervisor_user_id': supervisor_user_id
        }
    else:
        log.error('Ошибка с данными: (username, first_name, last_name, password) при проверке')
        return None


def add_or_edit_user(data: WSGIRequest.POST, user_id=None):
    prepare_data = check_user_data(data)
    if user_id:
        if prepare_data:
            return edit_user(user_id, prepare_data)
        else:
            log.error('Ошибка с данными "user_data" при изменении пользователя')
    else:
        if prepare_data:
            return create_new_user(prepare_data)
        else:
            log.error('Ошибка с данными "user_data" при создании пользователя')


def delete_user(user_id) -> User:
    user = get_user(pk=user_id)
    if user:
        user.isArchive = True
        user.save(update_fields=['isArchive'])
        log.info(f'Пользователь: ({user.last_name} {user.first_name}) был помещен в архив')
        return user
    return User.objects.none()


def is_supply_driver(current_technic_sheet_id_list: list, supply_technic_list_id_list: list) -> bool:
    if current_technic_sheet_id_list and set(current_technic_sheet_id_list).issubset(supply_technic_list_id_list):
        # print(current_technic_sheet_id_list)
        # print(supply_technic_list_id_list)
        return True
    else:
        return False


def check_user_by_phone(telephone) -> User|None:
    """
    Проверка существования пользователя с телефоном "telephone"
    :param telephone:
    :return:
    """
    validate_telephone = U.validate_telephone(telephone, length=7, use_pref=False)
    if validate_telephone:
        user = get_user_queryset(
            isArchive=False,
            telephone__contains=validate_telephone
        )
    else:
        user = User.objects.none()
    if user.exists() and user.count()==1:
        return user.first()
    else:
        return None
