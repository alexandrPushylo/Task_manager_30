from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet, ConstructionSite
from dashboard.models import ApplicationToday, ApplicationTechnic
from dashboard.models import Technic
# from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import User

#   ------------------------------------------------------------------------------------------------------------------


from datetime import date, timedelta, datetime

import dashboard.assets as ASSETS

#   ------------------------------------------------------------------------------------------------------------------

TODAY = date.today()


def get_weekday(_date):
    return ASSETS.WEEKDAY[_date.weekday()]


def add_user(data: dict):
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    post = data.get('post') if data.get('post') is not None else 'employee'
    supervisor_id = data.get('supervisor_id')
    telephone = data.get('telephone')

    if all([username, password, first_name, last_name]):
        new_user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
            is_superuser=False
        )
        if post == 'master' and supervisor_id is None:
            post = 'employee'
        user_post = get_post_instance(post).objects.create(
            user=new_user,
            telephone=telephone
        )
        if user_post.title == 'master':
            user_post.foreman = Foreman.objects.get(pk=supervisor_id)
        user_post.save()

        return new_user
    return None


def get_users_post_instance(id_user):
    try:
        user = User.objects.get(pk=id_user)
        if isAdministrator(user):
            _instance = Administrator.objects.get(user=user)
            return _instance, _instance.title
        elif isForeman(user):
            _instance = Foreman.objects.get(user=user)
            return _instance, _instance.title
        elif isMaster(user):
            _instance = Master.objects.get(user=user)
            return _instance, _instance.title
        elif isDriver(user):
            _instance = Driver.objects.get(user=user)
            return _instance, _instance.title
        elif isMechanic(user):
            _instance = Mechanic.objects.get(user=user)
            return _instance, _instance.title
        elif isSupply(user):
            _instance = Supply.objects.get(user=user)
            return _instance, _instance.title
        elif isEmployee(user):
            _instance = Employee.objects.get(user=user)
            return _instance, _instance.title
    except User.DoesNotExist:
        return None, None


def get_post_instance(post: str):
    if post == 'administrator':
        return Administrator
    elif post == 'foreman':
        return Foreman
    elif post == 'master':
        return Master
    elif post == 'driver':
        return Driver
    elif post == 'mechanic':
        return Mechanic
    elif post == 'supply':
        return Supply
    elif post == 'employee':
        return Employee
    else:
        return None
def is_administrator(user: User) -> bool:
    return True if user.post == ASSETS.ADMINISTRATOR else False


def is_foreman(user: User) -> bool:
    return True if user.post == ASSETS.FOREMAN else False


def is_master(user: User) -> bool:
    return True if user.post == ASSETS.MASTER else False


def is_driver(user: User) -> bool:
    return True if user.post == ASSETS.DRIVER else False


def is_mechanic(user: User) -> bool:
    return True if user.post == ASSETS.MECHANIC else False


def is_supply(user: User) -> bool:
    return True if user.post == ASSETS.SUPPLY else False


def is_employee(user: User) -> bool:
    return True if user.post == ASSETS.EMPLOYEE else False


def convert_str_to_date(str_date: str) -> date:
    """конвертация str в datetime.date"""
    try:
        if isinstance(str_date, str):
            _day = datetime.strptime(str_date, '%Y-%m-%d').date()
            return _day
        elif isinstance(str_date, date):
            return str_date
    except:
        print('Error date')


def prepare_workday(_date):
    if WorkDaySheet.objects.filter(date__gte=_date).count() < 14:
        for n in range(14):
            _day = TODAY + timedelta(days=n)
            if _day.weekday() in (5, 6):
                status = False
            else:
                status = True
            WorkDaySheet.objects.update_or_create(date=_day, defaults={'status': status})
    else:
        return False
