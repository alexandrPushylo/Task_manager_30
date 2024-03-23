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


def add_user(data: dict, user_id=None):
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    post = data.get('post') if data.get('post') is not None else ASSETS.EMPLOYEE
    supervisor_id = int(data.get('supervisor_id')) if data.get('supervisor_id') is not None else None
    telephone = data.get('telephone')

    if user_id:
        if all([username, password, first_name, last_name]):
            _user = User.objects.get(pk=user_id)
            _user.username = username
            _user.first_name = first_name
            _user.last_name = last_name
            _user.telephone = telephone
            _user.password = _user.set_password(password) if _user.password != password else _user.password
            _user.post = post
            _user.supervisor_user_id = supervisor_id
            _user.save()
            return _user
    else:
        if all([username, password, first_name, last_name]):
            new_user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                telephone=telephone,
                post=post,
                supervisor_user_id=supervisor_id,
                is_staff=False,
                is_superuser=False
            )
            return new_user
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


def prepare_driver_sheet(workday: WorkDaySheet):
    driver_list = User.objects.filter(isArchive=False, post=ASSETS.DRIVER)
    count_driver = len(driver_list)

    driver_sheet_list = DriverSheet.objects.filter(isArchive=False, date=workday)
    count_driver_sheet = len(driver_sheet_list)

    last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
    last_driver_sheet = DriverSheet.objects.filter(isArchive=False, date=last_workday)

    if count_driver > count_driver_sheet:
        if last_driver_sheet.exists():
            print('Copy')
            for driver in last_driver_sheet:
                DriverSheet.objects.get_or_create(date=workday,
                                                  driver=driver.driver,
                                                  status=driver.status)
        else:
            print('create')
            for driver in driver_list:
                DriverSheet.objects.get_or_create(date=workday, driver=driver)
        print('+')
    elif count_driver < count_driver_sheet:
        print('-')
    else:
        print('=')
