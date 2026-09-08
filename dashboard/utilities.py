import enum
from datetime import date, datetime, time
import random
from typing import Literal

from django.core.cache import cache
from django.db import models

from dashboard.assets import AcceptMode
from dashboard.models import WorkDaySheet
from django.db.models.query import QuerySet
from dashboard.schemas.user_schema import UserSchema
from logger import getLogger

#   ------------------------------------------------------------------------------------------------------------------
import dashboard.assets as assets
from config.settings import USE_CACHE
#   ------------------------------------------------------------------------------------------------------------------
log = getLogger(__name__)


class Utilities:
    # NOW = lambda: datetime.now().time()
    USE_CACHE = USE_CACHE
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        TODAY = "today"

    @classmethod
    def get_now(cls) -> time:
        return datetime.now().time()

    @classmethod
    def get_today(cls) -> date:
        cache_key = f"{cls.CacheKeys.TODAY.value}"
        cache_ttl = 60 * 60

        today_from_cache = cache.get(cache_key) if cls.USE_CACHE else None
        if today_from_cache is None:
            today: date = date.today()
            if cls.USE_CACHE:
                cache.set(cache_key, today, cache_ttl)
            return today
        return today_from_cache

    @classmethod
    def get_ru_weekday(cls, _date: date) -> str | None:
        """
        Получить день недели на русском языке
        :param _date:
        :return:
        """
        if isinstance(_date, str):
            weekday = datetime.strptime(_date, '%Y-%m-%d').weekday()
        elif isinstance(_date, WorkDaySheet):
            weekday = _date.date
        elif isinstance(_date, date):
            weekday = _date.weekday()
        else:
            return None
        if weekday in range(0, 7):
            return assets.WEEKDAY[weekday]
        else:
            return None

    @classmethod
    def get_ids_list_from_model(cls, model: models.Model | QuerySet[models.Model]) -> list[int]:
        if isinstance(model, models.Model):
            return [model.pk]
        elif isinstance(model, QuerySet):
            return list(model.values_list('id', flat=True))
        else:
            return []

    @classmethod
    def set_color_for_list(cls, some_list: list) -> dict:
        """
        Привязка цвета для каждого элемента из списка some_list
        :param some_list:
        :return:
        """
        colors = assets.COLORS[:]
        random.shuffle(colors)
        out = {
            int(id_): color
            for id_, color in zip(some_list, colors)
        }
        return out

    @classmethod
    def sort_applications_by_status(cls, item):
        """
        Сортировка application_today по статусу
        :param item:
        :return:
        """
        if item is None or item['application_today'] is None:
            return 10

        status = item['application_today']['status']

        if status == assets.ApplicationTodayStatus.SAVED.title:
            return 1
        if status == assets.ApplicationTodayStatus.SUBMITTED.title:
            return 5
        if status == assets.ApplicationTodayStatus.APPROVED.title:
            return 5
        if status == assets.ApplicationTodayStatus.SEND.title:
            return 5
        if status == assets.ApplicationTodayStatus.DELETED.title:
            return 7
        if status == assets.ApplicationTodayStatus.ABSENT.title:
            return 9
        return 9

    @classmethod
    def get_view_mode(cls, date_: date) -> str:
        """
        Получить режим отображения
        :param date_:
        :return:
        """
        if date_ == cls.get_today():
            return assets.ViewMode.CURRENT.value
        elif date_ < cls.get_today():
            return assets.ViewMode.ARCHIVE.value
        elif date_ > cls.get_today():
            return assets.ViewMode.FUTURE.value
        else:
            return 'None'

    @classmethod
    def get_accept_mode(cls, accept_mode: str) -> Literal[AcceptMode.AUTO, AcceptMode.CLOSE, AcceptMode.OPEN]:
        """ Получить режим accept mode"""
        if accept_mode == assets.AcceptMode.AUTO.value:
            return assets.AcceptMode.AUTO
        elif accept_mode == assets.AcceptMode.CLOSE.value:
            return assets.AcceptMode.CLOSE
        elif accept_mode == assets.AcceptMode.OPEN.value:
            return assets.AcceptMode.OPEN
        else:
            return assets.AcceptMode.AUTO

    @classmethod
    def is_valid_str(cls, value: str | None) -> bool:
        """
        Проверка : value is not None and value != ''
        :param value:
        :return:
        """
        if value is not None and value != '':
            return True
        else:
            return False

    @classmethod
    def validate_cache_name(cls, raw_name: str) -> str:
        return raw_name.strip().replace(" ",'')

    @classmethod
    def is_admin(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.ADMINISTRATOR.title == current_user.post

    @classmethod
    def is_foreman(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.FOREMAN.title == current_user.post

    @classmethod
    def is_master(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.MASTER.title == current_user.post

    @classmethod
    def is_driver(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.DRIVER.title == current_user.post

    @classmethod
    def is_mechanic(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.MECHANIC.title == current_user.post

    @classmethod
    def is_supply(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.SUPPLY.title == current_user.post

    @classmethod
    def is_employee(cls, current_user: UserSchema) -> bool:
        return assets.UserPosts.EMPLOYEE.title == current_user.post

    @classmethod
    def is_supply_driver(
            cls,
            current_technic_sheet_id_list: list,
            supply_technic_list_id_list: list
    ) -> bool:
        if current_technic_sheet_id_list and set(current_technic_sheet_id_list).issubset(supply_technic_list_id_list):
            return True
        else:
            return False
