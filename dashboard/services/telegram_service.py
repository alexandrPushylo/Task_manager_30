import random

import dashboard.assets as ASSETS
import dashboard.telegram_bot as telegram
from config.creds import USE_TELEGRAM
from dashboard.models import WorkDaySheet
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.services.user import UserService
from logger import getLogger

log = getLogger(__name__)

class TelegramService:
    USE_TELEGRAM = USE_TELEGRAM
    BOT = telegram.BOT

    @classmethod
    def send_messages(cls, chat_id, messages):
        """
        Отправка messages пользователю с chat_id через Telegram
        :param chat_id:
        :param messages:
        :return:
        """
        if USE_TELEGRAM:
            try:
                cls.BOT.send_message(chat_id=chat_id, text=messages, parse_mode='html')
            except telegram.ApiTelegramException as e:
                log.error('send_messages_by_telegram(): ApiTelegramException [%s]' % chat_id)

    @classmethod
    def get_user_key(cls, user_id):
        """
        Получить уникальный ключ для привязки Telegram
        :param user_id:
        :return:
        """
        _user = UserService.get_object(pk=user_id)
        if _user:
            _key = random.randint(100, 999)
            return f'{_key}{_user.id}'
        return None

    @classmethod
    def send_application_by_telegram_for_driver(cls, workday_data: WorkDaySchema, messages=None, application_today_id=None):
        all_already_send = workday_data.is_all_application_send
        template_date = f'{ASSETS.WEEKDAY[workday_data.date.weekday()]}, {workday_data.date.day} {ASSETS.MONTHS_T[workday_data.date.month - 1]}'
        driver_list = TechnicSheetService.get_queryset(
            date_id=workday_data.id,
            status=True,
            driver_sheet__status=True,
            isArchive=False
        )
        if application_today_id:
            application_today = ApplicationTodayService.get_queryset(id=application_today_id)
        else:
            application_today = ApplicationTodayService.get_queryset(
                isArchive=False,
                date_id=workday_data.id,
                status=ASSETS.ApplicationTodayStatus.SEND.title)

        application_technic_list = ApplicationTechnicService.get_queryset(
            isArchive=False,
            is_cancelled=False,
            isChecked=False,
            application_today__in=application_today
        ).select_related('technic_sheet', 'application_today__construction_site__foreman')

        driver_sheet_list = driver_list.filter(
            id__in=application_technic_list.values_list('technic_sheet_id', flat=True)).values(
            'id',
            'driver_sheet__driver__telegram_id_chat',
            'driver_sheet__driver__last_name',
            'driver_sheet__driver__first_name',
        )

        for driver_sheet_item in driver_sheet_list:
            driver_sheet_item['applications'] = application_technic_list.filter(
                technic_sheet_id=driver_sheet_item['id']).values(
                'priority',
                'application_today__construction_site__address',
                'application_today__construction_site__foreman__last_name',
                'application_today__is_application_send',
                'description'
            ).order_by('priority')

        if all_already_send:
            msg = f'Обновленная заявка на:\n{template_date}\n\n'
        else:
            msg = f'Заявка на:\n{template_date}\n\n'

        for item in driver_sheet_list:
            msg = ''
            msg = f"{item['driver_sheet__driver__last_name']} {item['driver_sheet__driver__first_name']}\n{msg}"
            for app in item['applications']:
                if app['application_today__construction_site__foreman__last_name']:
                    msg += f"{app['priority']}) {app['application_today__construction_site__address']} ({app['application_today__construction_site__foreman__last_name']})\n"
                else:
                    msg += f"{app['priority']}) {app['application_today__construction_site__address']}\n"
                if app['description']:
                    msg += f"{app['description']}\n\n"
                else:
                    msg += f"\n"
            if item['driver_sheet__driver__telegram_id_chat']:
                cls.send_messages(chat_id=item['driver_sheet__driver__telegram_id_chat'], messages=msg)

    @classmethod
    def send_application_by_telegram_for_foreman(cls, workday_data: WorkDaySchema, messages=None, application_today_id=None):
        all_already_send = workday_data.is_all_application_send
        template_date = f'{ASSETS.WEEKDAY[workday_data.date.weekday()]}, {workday_data.date.day} {ASSETS.MONTHS_T[workday_data.date.month - 1]}'
        foreman_list = UserService.get_queryset(
            isArchive=False,
            post__in=(ASSETS.UserPosts.FOREMAN.title, ASSETS.UserPosts.MASTER.title, ASSETS.UserPosts.SUPPLY.title)
        ).values(
            'id',
            'last_name',
            'first_name',
            'post',
            'supervisor_user_id',
            'telegram_id_chat'
        )

        if application_today_id:
            application_today = ApplicationTodayService.get_queryset(
                pk=application_today_id
            ).select_related('construction_site__foreman')
        else:
            application_today = ApplicationTodayService.get_queryset(
                isArchive=False,
                date_id=workday_data.id,
                status=ASSETS.ApplicationTodayStatus.SEND.title
            ).select_related('construction_site__foreman')

        for item in foreman_list:
            if item['post'] == ASSETS.UserPosts.FOREMAN.title:
                foreman_id = item['id']
            else:
                foreman_id = item['supervisor_user_id']
            if foreman_id:
                app_today = application_today.filter(
                    construction_site__foreman_id=foreman_id
                )
            else:
                app_today = application_today.filter(
                    construction_site__address=ASSETS.MessagesAssets.CS_SUPPLY_TITLE.value
                )
            item['applications'] = app_today.values(
                'construction_site__address',
                'is_application_send'
            )

        for item in foreman_list:
            if all_already_send:
                msg = f"Повторное уведомление:\n{template_date}\n"
            else:
                msg = f"{template_date}\n"
            if item['applications']:
                for app in item['applications']:
                    if app['is_application_send']:
                        msg = f"Повторное уведомление:\n{template_date}\n"
                    else:
                        msg = msg
                    msg += f"Заявка на {app['construction_site__address']} одобрена\n"
                if item['telegram_id_chat']:
                    cls.send_messages(chat_id=item['telegram_id_chat'], messages=msg)

    @classmethod
    def send_application_by_telegram_for_admin(cls, workday_data: WorkDaySchema, messages=None, application_today_id=None):
        template_date = f'{ASSETS.WEEKDAY[workday_data.date.weekday()]}, {workday_data.date.day} {ASSETS.MONTHS_T[workday_data.date.month - 1]}'
        administrators_list = UserService.get_queryset(
            isArchive=False,
            post=ASSETS.UserPosts.ADMINISTRATOR.title
        )

        if workday_data.is_all_application_send:
            msg = f"Заявки на:\n{template_date} отправлены повторно"
        else:
            msg = f"Заявки на:\n{template_date} отправлены"

        if application_today_id:
            app_today = ApplicationTodayService.get_object(id=application_today_id)
            if app_today:
                if app_today.construction_site.foreman:
                    msg_constr_site = f'{app_today.construction_site.address} ({app_today.construction_site.foreman})'
                else:
                    msg_constr_site = f'{app_today.construction_site.address}'

                if app_today.is_application_send:
                    msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена повторно"
                else:
                    msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена"

        messages = messages if messages else msg

        [cls.send_messages(admin.telegram_id_chat, messages)
         for admin in administrators_list if admin.telegram_id_chat]

    @classmethod
    def send_application_by_telegram_for_all(cls, workday_data: WorkDaySchema, messages, application_today_id):
        """
        Отправка заявок всем пользователям через Telegram
        :param workday_data:
        :param messages:
        :param application_today_id:
        :return:
        """
        cls.send_application_by_telegram_for_driver(workday_data, messages, application_today_id)
        cls.send_application_by_telegram_for_foreman(workday_data, messages, application_today_id)
        cls.send_application_by_telegram_for_admin(workday_data, messages, application_today_id)
