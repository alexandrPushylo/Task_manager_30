from dashboard.models import User
import dashboard.assets as ASSETS

from logger import getLogger
log = getLogger(__name__)


def edit_user(user_id, data: dict) -> User | None:
    try:
        user = User.objects.get(pk=user_id)
        user.username = data['username']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.telephone = data['telephone']
        if data['password'] != user.password:
            user.set_password(data['password'])
        user.post = data['post']
        user.supervisor_user_id = data['supervisor_user_id']
        user.save()
        log.info('Пользователь %s %s был изменен', user.last_name, user.first_name)
        return user
    except User.DoesNotExist:
        log.exception(User.DoesNotExist)
        return None


def create_new_user(data: dict) -> User | None:
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
    log.info('Пользователь %s %s был создан', user.last_name, user.first_name)
    return user


def check_user_data(user_data: dict) -> dict | None:
    log.info('Проверка user_data')
    username = user_data.get('username')
    first_name = user_data.get('first_name')
    last_name = user_data.get('last_name')
    telephone = user_data.get('telephone')
    password = user_data.get('password')
    post = user_data.get('post') if user_data.get('post') is not None else ASSETS.EMPLOYEE
    supervisor_user_id = int(user_data.get('supervisor_id')) if user_data.get('supervisor_id') is not None else None

    if all((username, first_name, last_name, password)):
        log.info(f'Данные: (username, first_name, last_name, password) в порядке')
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


def add_or_edit_user(data, user_id=None):
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


def delete_user(user_id):
    try:
        user = User.objects.get(pk=user_id)
        user.isArchive = True
        user.save(update_fields=['isArchive'])
        log.info(f'Пользователь {user.last_name} {user.first_name} был помещен в архив')
        return user
    except User.DoesNotExist:
        log.exception(User.DoesNotExist)
        return None
