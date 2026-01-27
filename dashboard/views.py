import json
from typing import Any

from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth import login, logout, authenticate
from dashboard.models import ApplicationTechnic

import dashboard.assets as ASSETS
import config.endpoints as ENDPOINTS
from dashboard.schemas.construction_site_schema import EditConstructionSiteSchema
from dashboard.schemas.technic_schema import EditTechnicSchema
from dashboard.schemas.user_schema import EditUserSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.utilities import Utilities
import dashboard.variables as VAR
import dashboard.telegram_bot  as telegram

#   SERVICE--------------------------------------------------
from dashboard.schemas.application_today_schema import CreateApplicationTodaySchema
from dashboard.schemas.parameter_schema import SetParameterSchema

from dashboard.services.application_material import ApplicationMaterialService
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.construction_site import ConstructionSiteService
from dashboard.services.technic import TechnicService, TemplateDescService
from dashboard.services.work_day_sheet import WorkDayService
from dashboard.services.driver_sheet import DriverSheetService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.services.user import UserService
from dashboard.services.parameter import ParameterService
from dashboard.services.telegram_service import TelegramService
from dashboard.services.add_edit_application import EditApplicationService
from dashboard.services.dashboard import DashboardService
#   SERVICE--------------------------------------------------

from logger import getLogger

log = getLogger(__name__)


# Create your views here.


def routing(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        next_work_day = WorkDayService.get_next_workday()
        next_app_today = ApplicationTodayService.get_queryset(
            isArchive=False,
            date=next_work_day.id
        )
        if Utilities.is_admin(current_user):
            if next_app_today.exists():
                return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")

        elif Utilities.is_foreman(current_user) or Utilities.is_master(current_user):
            if Utilities.NOW() > ASSETS.TIME_REDIRECT_DASHBOARD_FOR_FOREMAN:
                return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")

        elif Utilities.is_supply(current_user):
            return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")
        elif Utilities.is_mechanic(current_user):
            return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")
        elif Utilities.is_driver(current_user):
            if Utilities.NOW() > ASSETS.TIME_REDIRECT_DASHBOARD_FOR_DRIVER:
                return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")
        elif Utilities.is_employee(current_user):
            if Utilities.NOW() > ASSETS.TIME_REDIRECT_DASHBOARD_FOR_EMPLOYEE:
                return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={next_work_day.date}")
        else:
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def dashboard_view(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)
    current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
    current_user = UserService.get_current_user(request.user.pk)

    context = {
        'title': request.user,
    }
    context = Utilities.get_prepared_data(context, current_day)
    context = Utilities.prepare_data_for_filter(context)

    if not current_day.status:
        if (request.GET.get('current_day') is None or request.GET.get('current_day') == '' or
                Utilities.is_driver(current_user) or
                Utilities.is_employee(current_user)):
            next_workday = WorkDayService.get_next_workday(current_day.date)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD + f'?current_day={next_workday.date}')
        return render(request, 'content/spec/weekend.html', context)

    #   POST    ===================================================================================================
    if request.method == 'POST':
        operation = request.POST.get('operation')

        if operation == 'change_props_for_view':
            io_name = request.POST.get('io_name')
            io_status = request.POST.get('io_isChecked')
            io_value = request.POST.get('io_value')
            status = Utilities.change_view_props(io_name, io_status, io_value, current_user.id)
            if status:
                return HttpResponse(b'ok')
            else:
                return HttpResponse(b'error')

        if operation == 'copy':
            target_day = request.POST.get('target_day')
            application_today_id = request.POST.get('application_id')
            if Utilities.is_valid_str(target_day) and Utilities.is_valid_str(application_today_id):
                target_workday_data = WorkDayService.get_current_date_data(target_day)
                default_app_status = Utilities.get_default_status_for_apps_today(current_user)
                Utilities.copy_application_to_target_day(int(application_today_id), target_workday_data, default_app_status)

        if Utilities.is_valid_str(operation) and operation == 'set_props_for_filter':
            Utilities.set_data_for_filter(request)

    #   POST    ===================================================================================================


    dashboard, template = DashboardService.get_dashboard(current_user)
    if Utilities.is_valid_str(request.GET.get('driver_id')):
        context = DashboardService.get_dashboard_for_driver(request, current_day, context)
        template = DashboardService.TemplateDashboardFor.INFO_ABOUT_DRIVER.value
    else:
        context = dashboard(request, current_day, context)
    return render(request, template, context)


def clear_or_restore_application_today(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        if any((
                Utilities.is_admin(current_user),
                Utilities.is_foreman(current_user),
                Utilities.is_master(current_user),
                Utilities.is_supply(current_user)
        )):
            if Utilities.is_foreman(current_user):
                foreman = current_user
            else:
                foreman_list = UserService.get_foreman_list()
                foreman = UserService.filter_user_by_id_from_data(current_user.supervisor_user_id, foreman_list)

            app_today_id = request.GET.get('app_today_id')
            action = request.GET.get('action', 'delete')
            if app_today_id:
                application_today = ApplicationTodayService.get_object(id=app_today_id)
                if not application_today:
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

                if (not Utilities.is_admin(current_user) and
                        foreman.id != application_today.construction_site.foreman.id):
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

                elif Utilities.is_supply(current_user):
                    supply_technic_ids_list = [t.id for t in TechnicService.get_supply_technic_list()]
                    if action == 'restore':
                        app_technic_list = ApplicationTechnicService.get_queryset(
                            application_today__date=application_today.date,
                            isArchive=False,
                            technic_sheet__technic_id__in=supply_technic_ids_list,
                            id_orig_app__gte=0
                        ).exclude(application_today=application_today)
                        app_technic_list.update(isChecked=True)
                    else:
                        app_technic_list = ApplicationTechnicService.get_queryset(
                            application_today__date=application_today.date,
                            isArchive=False,
                            technic_sheet__technic_id__in=supply_technic_ids_list
                        ).exclude(application_today=application_today)
                        app_technic_list.update(isChecked=False)

                if action == 'restore':
                    default_status = Utilities.get_default_status_for_apps_today(current_user)
                    Utilities.restore_application_today(application_today_id=application_today.id, status=default_status)
                else:
                    Utilities.delete_application_today(application_today.id)

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def validate_application_today_view(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.id)
        app_today_id = request.GET.get('app_today_id')
        current_day = request.GET.get('current_day')
        construction_site_id = request.GET.get('constr_site_id')
        default_status = Utilities.get_default_status_for_apps_today(current_user)

        if Utilities.is_valid_str(app_today_id):
            application_today = ApplicationTodayService.get_object(id=app_today_id)
        else:
            date = Utilities.get_current_day_data(current_day)
            application_today = ApplicationTodayService.get_object(
                construction_site_id=construction_site_id,
                date_id=date.id
            )
        if application_today:
            Utilities.validate_application_today(
                application_today=application_today,
                default_status=default_status)
        return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day}')
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_application_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Создать заявку'}
        # current_day = WORK_DAY_SERVICE.get_current_day(request)
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        current_user = UserService.get_current_user(request.user.id)
        context['weekday'] = ASSETS.WEEKDAY[current_day.date.weekday()]

        context = Utilities.get_prepared_data(context, current_day)

        constr_site_id = request.GET.get('constr_site_id')
        if Utilities.is_valid_str(constr_site_id):
            construction_site = ConstructionSiteService.get_object(id=constr_site_id)
        else:
            construction_site = None
        if construction_site:
            context['construction_site'] = construction_site
        else:
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        def _create_app_today():
            _default_status = Utilities.get_default_status_for_apps_today(current_user)
            create_data = CreateApplicationTodaySchema(
                construction_site_id=construction_site.pk,
                date_id=current_day.id
            )
            _application_today = ApplicationTodayService.get_or_create_by_data(create_data)
            return _application_today

        def _prepare_app_today(app_today_id, construction_site_id: int, date_id: int):
            if all((app_today_id, construction_site_id, date_id)):
                _application_today = ApplicationTodayService.get_object(
                    pk=app_today_id,
                    construction_site_id=construction_site_id,
                    date_id=date_id
                )
                if _application_today:
                    return _application_today
                else:
                    return _create_app_today()
            else:
                return _create_app_today()

        # context['is_changeable_material'] = U.get_accept_to_change_materials_app(current_workday=current_day)
        context['is_changeable_material'] = Utilities.get_accept_to_change_materials_app(current_workday=current_day)

        if not current_day.status:
            return render(request, 'content/spec/weekend.html', context)

        technic_sheets = TechnicSheetService.get_queryset(
            isArchive=False,
            driver_sheet__isnull=False,
            date_id=current_day.id
        ).select_related('technic', 'driver_sheet__driver')

        if not technic_sheets.exists():
            Utilities.prepare_sheets(current_day)

        technic_sheets_data = TechnicSheetService.get_tech_sheet_for_date(current_day)
        driver_sheet_data = DriverSheetService.get_driver_sheet_for_date(current_day)

        # if Utilities.is_admin(current_user):
        #     driver_sheet_ids = [ ds.id for ds in driver_sheet_data]
        #     technic_sheets_data = [ts for ts in technic_sheets_data if ts.driver_sheet and ts.status]
        # else:
        driver_sheet_ids = [ ds.id for ds in driver_sheet_data]
        technic_sheets_data = [ts for ts in technic_sheets_data if ts.driver_sheet in driver_sheet_ids]
        driver_sheet_ids_for_add = [ ds.id for ds in driver_sheet_data if ds.status]
        technic_sheets_data_for_add = [
            ts for ts in technic_sheets_data
            if ts.driver_sheet in driver_sheet_ids_for_add
               and ts.status
        ]

        technic_titles_dict = TechnicService.get_dict_short_technic_names(
            technic_sheets_data=technic_sheets_data
            # technic_sheets=technic_sheets
        )
        context['technic_titles_dict'] = technic_titles_dict

        context['technic_titles_dict_for_add'] = TechnicService.get_dict_short_technic_names(
            technic_sheets_data=technic_sheets_data_for_add
        )
        context['technic_driver_list_for_add'] = EditApplicationService.get_technic_driver_list(
            technic_titles=technic_titles_dict,
            technic_sheets_instance=technic_sheets.filter(
                driver_sheet__status=True,
                status=True,
            )
        )
        if Utilities.is_admin(current_user):
            context['technic_driver_list'] = EditApplicationService.get_technic_driver_list(
                technic_titles=technic_titles_dict,
                technic_sheets_instance=technic_sheets
            )
            technic_driver_list_json = EditApplicationService.get_technic_driver_list_for_json(
                technic_titles=technic_titles_dict,
                technic_sheets_instance=technic_sheets
            )
        else:
            context['technic_driver_list'] = context['technic_driver_list_for_add']
            technic_driver_list_json = EditApplicationService.get_technic_driver_list_for_json(
                technic_titles=technic_titles_dict,
                technic_sheets_instance=technic_sheets.filter(
                    driver_sheet__status=True,
                    status=True,
                )
            )

        if request.method == 'POST':
            operation = request.POST.get('operation')  # операция
            post_application_today_id = request.POST.get('app_today_id')
            post_technic_title_shrt = request.POST.get('technic_title_shrt')
            post_technic_sheet_id = request.POST.get('technic_sheet_id')
            post_application_technic_description = request.POST.get('app_tech_desc', '')
            post_application_technic_id = request.POST.get('application_technic_id')
            post_application_today_description = request.POST.get('application_today_description', '')
            post_application_material_description = request.POST.get('material_description', '')

            post_application_technic_description: str = post_application_technic_description.strip()
            post_application_today_description: str = post_application_today_description.strip()
            post_application_material_description: str = post_application_material_description.strip()

            match operation:
                case 'add_technic_to_application':
                    log.debug('add_technic_to_application')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )
                    data = EditApplicationService.add_technic_to_application(
                        post_technic_title_shrt=post_technic_title_shrt,
                        post_technic_sheet_id=post_technic_sheet_id,
                        post_application_technic_description=post_application_technic_description,
                        technic_titles_dict=technic_titles_dict,
                        current_user=current_user,
                        current_day=current_day,
                        app_today_inst=app_today,
                        technic_driver_list_json=technic_driver_list_json
                    )
                    return HttpResponse(json.dumps(data))

                case 'reject_application_technic':
                    log.debug('reject_application_technic')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )
                    status = EditApplicationService.reject_application_technic(
                        post_application_technic_id=post_application_technic_id,
                        current_day=current_day,
                        current_user=current_user,
                        app_today_inst=app_today,
                    )
                    return HttpResponse(status)

                case 'delete_application_technic':
                    log.debug('delete_application_technic')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )

                    status = EditApplicationService.delete_application_technic(
                        post_application_technic_id=post_application_technic_id,
                        app_today_inst=app_today,
                        current_user=current_user,
                    )
                    return HttpResponse(status)

                case 'apply_changes_application_technic':
                    log.debug('apply_changes_application_technic')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )
                    data = EditApplicationService.apply_changes_application_technic(
                        post_technic_title_shrt=post_technic_title_shrt,
                        post_technic_sheet_id=post_technic_sheet_id,
                        post_application_technic_id=post_application_technic_id,
                        post_application_technic_description=post_application_technic_description,
                        technic_titles_dict=technic_titles_dict,
                        current_day=current_day,
                        current_user=current_user,
                        app_today_inst=app_today,
                    )
                    return HttpResponse(json.dumps(data))

                case 'save_application_description':
                    log.debug('save_application_description')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )
                    data = EditApplicationService.save_application_description(
                        post_application_today_description=post_application_today_description,
                        app_today_inst=app_today
                    )
                    return HttpResponse(json.dumps(data))

                case 'save_application_materials':
                    log.debug('save_application_materials')
                    app_today = _prepare_app_today(
                        app_today_id=post_application_today_id,
                        construction_site_id=construction_site.id,
                        date_id=current_day.id
                    )
                    data = EditApplicationService.save_application_materials(
                        post_application_material_description=post_application_material_description,
                        app_today_inst=app_today,
                        current_user=current_user
                    )
                    return HttpResponse(json.dumps(data))

                case _:
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        application_today = ApplicationTodayService.get_queryset(
            construction_site=construction_site,
            date_id=current_day.id,
            isArchive=False
        ).first()

        if application_today:
            context['application_today'] = {
                'id': application_today.id,
                'date__date': application_today.date,
                'status': application_today.status,
                'description': application_today.description,
                'is_edited': application_today.is_edited
            }
            context['application_today']['application_technic'] = ApplicationTechnicService.get_queryset(
                isArchive=False,
                application_today=application_today).values(
                'id',
                'technic_sheet_id',
                'technic_sheet__technic__title',
                'technic_sheet__driver_sheet__driver__last_name',
                'technic_sheet__driver_sheet__driver__first_name',
                'is_cancelled',
                'isChecked',
                'description'
            )
            context['application_today']['application_material'] = ApplicationMaterialService.get_queryset(
                isArchive=False,
                application_today=application_today).values(
                'id',
                'description',
                'isChecked',
                'is_cancelled'
            ).first()

        return render(request, 'content/dashboard/edit_application.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    if request.method == 'GET':
        return render(request, 'content/login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        username = username.strip()
        password = request.POST.get('password')

        phn_user = UserService.get_user_by_phone(username)
        if phn_user:
            user = authenticate(request, username=phn_user.username, password=password)
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                username = username.capitalize()
                user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log.info(f"Пользователь {user} зашел в систему")
            return HttpResponseRedirect(ENDPOINTS.ROUTING_DASHBOARD)
        else:
            log.warning(f'Username: {username} or Password is incorrect')
            return render(request, 'content/login.html', {'error': ASSETS.ErrorMessages.invalid_signin.value})
    return HttpResponse(status=403)

def restore_password_view(request):
    context = {}
    if request.method == 'POST':
        _last_name = request.POST.get('last_name')
        last_name = _last_name.strip().lower().capitalize()
        _user = UserService.get_queryset(
            isArchive=False,
            last_name=last_name,
        )
        if _user.exists():
            context['users_list'] = _user
        else:
            context['msg'] = 'Данный пользователь не найден'
    user_id = request.GET.get('user_id')
    if Utilities.is_valid_str(user_id):
        restore_user = UserService.get_object(id=user_id)
        if restore_user:
            default_passwd = ParameterService.get_object(name=VAR.VAR_DEFAULT_PASSWORD['name'])
            if default_passwd:
                restore_user.set_password(default_passwd.value)
                restore_user.save(update_fields=['password'])
                context['msg_success'] = {'login': restore_user.username, 'password': default_passwd.value}
                log.info(f"Пароль пользователя {restore_user.username} успешно сброшен")
            else:
                log.error("Ошибка с параметром 'default_passwd'")
                context['msg'] = 'Произошла какая-то ошибка'
        else:
            log.error("restore_password_view(): restore_user не найден")
    return render(request, 'content/spec/restore_password.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        log.info(f"Пользователь {request.user.username} вышел из системы")
        logout(request)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def register_view(request):
    context = {
        'user_posts': {
            **ASSETS.UserPosts.EMPLOYEE.get_dict(),
            **ASSETS.UserPosts.DRIVER.get_dict(),
        }
    }

    if request.method == 'GET':
        return render(request, 'content/register.html', context)
    if request.method == 'POST':
        user_data = EditUserSchema(
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            telephone=request.POST.get('telephone'),
            post=request.POST.get('post'),
            supervisor_user_id=request.POST.get('supervisor_id'),
        )
        new_user, msg = UserService.create(user_data)

        if new_user is not None and request.user.is_anonymous:
            login(request, new_user)
            log.info("Пользователь успешно зарегистрирован")
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
        elif new_user is not None and request.user.is_authenticated:
            return HttpResponseRedirect('/')  # TODO redirect if create new user
        elif new_user is None and msg == ASSETS.UserEditResult.EXISTS:
            context['error'] = ASSETS.ErrorMessages.user_already_exists.value
            log.warning('User already exists')
            return render(request, 'content/register.html', context)
        else:
            context['error'] = ASSETS.ErrorMessages.invalid_register.value
            log.warning('Invalid register form')
            return render(request, 'content/register.html', context)

    return HttpResponse(status=403)


#   Sheets--------------------------------------------------------------------------------------------------------------
def workday_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Рабочие дни'}

        if request.method == 'POST' and request.POST.get('operation') == 'toggleWorkdayStatus':
            workday_id = request.POST.get('workday_id')
            if Utilities.is_valid_str(workday_id):
                status = WorkDayService.change_status(id=workday_id)
                if status:
                    return HttpResponse(b'ok')
                else:
                    return HttpResponse(b'fail')

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context=context, current_workday=current_day)
        current_date = current_day.date
        context['workdays'] = WorkDayService.get_range_of_workdays_with_weekdays(current_date, 3, 7)
        return render(request, 'content/sheet/workday_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def driver_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Табель: водители'}

        if request.method == "POST":
            driver_sheet_id = request.POST.get('item_id')
            operation = request.POST.get('operation')
            if Utilities.is_valid_str(driver_sheet_id) and operation == 'toggleDriverSheetStatus':
                status = DriverSheetService.change_status(driver_sheet_id=int(driver_sheet_id))
                if status:
                    return HttpResponse(b"true")
                elif not status:
                    return HttpResponse(b"false")
                else:
                    return HttpResponse(b"none")

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        if current_day.date >= Utilities.TODAY and current_day.status:
            Utilities.prepare_driver_sheet(current_day)
        driver_sheet = DriverSheetService.get_driver_sheet_for_date(current_day)
        drivers_list = UserService.get_driver_list()
        context['drivers_list'] = drivers_list

        context['driver_sheets'] = [
            {
                **ds.model_dump(),
                "driver": UserService.filter_user_by_id_from_data(ds.driver, drivers_list)
            }
            for ds in driver_sheet
        ]

        return render(request, 'content/sheet/driver_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def technic_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Табель: техника'}

        if request.method == 'POST':
            technic_sheet_id = request.POST.get('technic_sheet_id')
            driver_sheet_id = request.POST.get('driver_sheet_id')
            item_id = request.POST.get('item_id')
            operation = request.POST.get('operation')

            if operation == 'toggleTechnicSheetStatus' and Utilities.is_valid_str(item_id):
                technic_sheet_id = request.POST.get('item_id')
                status = TechnicSheetService.change_status(technic_sheet_id=int(technic_sheet_id))
                if status:
                    return HttpResponse(b"true")
                elif not status:
                    return HttpResponse(b"false")
                else:
                    return HttpResponse(b"none")

            if operation == 'changeDriverForTechnic' and Utilities.is_valid_str(technic_sheet_id):
                status = Utilities.change_driver_for_technic_sheet(
                    technic_sheet_id=technic_sheet_id,
                    driver_sheet_id=driver_sheet_id)
                if status:
                    return HttpResponse(b"true")
                elif status is None:
                    return HttpResponse(b"none")
                else:
                    return HttpResponse(b"false")

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        if current_day.date >= Utilities.TODAY and current_day.status:
            Utilities.prepare_driver_sheet(current_day)
            Utilities.prepare_technic_sheet(current_day)

        technic_sheet = (TechnicSheetService.get_queryset(date_id=current_day.id)
                         .select_related('driver_sheet__driver', 'technic__attached_driver')
                         .order_by('technic__title', 'driver_sheet__driver__last_name'))
        driver_sheet = DriverSheetService.get_queryset(
            date_id=current_day.id
        ).select_related("driver")

        context['technic_sheets'] = technic_sheet
        context['driver_sheets'] = driver_sheet

        return render(request, 'content/sheet/technic_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

#   --------------------------------------------------------------------------------------------------------------------

#   Technic-------------------------------------------------------------------------------------------------------------
def technic_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Техника'}

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)
        technics = TechnicService.get_all_technic_data()
        drivers = UserService.get_driver_list()

        technic_list = []
        for technic in technics:
            driver_ = [driver.model_dump() for driver in drivers if driver.id == technic.attached_driver]
            technic_list.append(
                {
                    **technic.model_dump(),
                    "attached_driver": driver_[0] if driver_ else None
                }
            )
        context['technics'] = technic_list
        return render(request, 'content/technic/technics.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def edit_technic_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Добавить технику'}

        technic_id = request.GET.get('tech_id')
        context['drivers'] = UserService.get_driver_list()

        context['supervisors'] = {
            **ASSETS.UserPosts.MECHANIC.get_dict(),
            **ASSETS.UserPosts.SUPPLY.get_dict()
        }

        technic_type_list = TechnicService.get_technic_type_list()
        context['technic_type_list'] = technic_type_list

        if technic_id:
            technic = TechnicService.get_object(id=technic_id)
            if technic:
                context['technic'] = technic
                context['title'] = 'Редактировать технику'
            else:
                return HttpResponseRedirect(ENDPOINTS.TECHNICS)

        if request.method == 'POST':
            data = request.POST
            attached_driver = data.get('attached_driver')
            technic_data = EditTechnicSchema(
                title=data.get('title'),
                type=data.get('type'),
                id_information=data.get('id_information'),
                description=data.get('description'),
                attached_driver=int(attached_driver) if attached_driver else None,
                supervisor_technic=data.get('supervisor'),
            )
            if technic_id:
                TechnicService.edit(int(technic_id), technic_data)
            else:
                TechnicService.create(technic_data)

            return HttpResponseRedirect(ENDPOINTS.TECHNICS)

        return render(request, 'content/technic/edit_technic.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def delete_technic_view(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        if Utilities.is_admin(current_user) or Utilities.is_mechanic(current_user):
            technic_id = request.GET.get('tech_id')
            if technic_id:
                Utilities.delete_technic(int(technic_id))
        return HttpResponseRedirect(ENDPOINTS.TECHNICS)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


#   --------------------------------------------------------------------------------------------------------------------


#   User----------------------------------------------------------------------------------------------------------------
def users_view(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Все пользователи',
            'users_list': [],
            'user_post': ASSETS.UserPosts.get_dict()
        }
        current_user = UserService.get_current_user(request.user.pk)
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))

        context = Utilities.get_prepared_data(context, current_day)
        context['current_day'] = current_day

        if Utilities.is_admin(current_user):
            users_list = UserService.get_all_users_list()

        elif Utilities.is_master(current_user) or Utilities.is_foreman(current_user):
            users_list = [
                user for user in UserService.get_all_users_list()
                if user.post != ASSETS.UserPosts.ADMINISTRATOR.title
            ]

        elif Utilities.is_mechanic(current_user):
            users_list = UserService.get_driver_list()
        else:
            users_list = []
        context['users_list'] = [user for user in users_list if user.isArchive == False]
        context['user_post'] = ASSETS.UserPosts.get_dict()
        return render(request, 'content/users/users.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def edit_user_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Добавить пользователя',
                   'posts': ASSETS.UserPosts.get_dict(),
                   'foreman_list': UserService.get_foreman_list()
                   }
        current_user = UserService.get_current_user(request.user.pk)

        if Utilities.is_mechanic(current_user):
            context['posts'] = ASSETS.UserPosts.DRIVER.get_dict()
        if Utilities.is_master(current_user) or Utilities.is_foreman(current_user):
            context['posts'] = ASSETS.UserPosts.EMPLOYEE.get_dict()

        user_id = request.GET.get('user_id')
        if Utilities.is_valid_str(user_id):
            user_ = UserService.get_object(id=user_id)
            if user_:
                context['user_list'] = user_
                context['title'] = 'Изменить пользователя'
            else:
                return HttpResponseRedirect(ENDPOINTS.USERS)

        if request.method == 'POST':
            user_data = EditUserSchema(
                username=request.POST.get('username'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                telephone=request.POST.get('telephone'),
                post=request.POST.get('post'),
                supervisor_user_id=request.POST.get('supervisor_id'),
            )
            if user_id:
                _user_rez = UserService.edit(int(user_id), user_data)
            else:
                _user_rez = UserService.create(user_data)


            if _user_rez[0] is not None:
                return HttpResponseRedirect(ENDPOINTS.USERS)
            else:
                context['error'] = ASSETS.ErrorMessages.user_already_exists.value

        return render(request, 'content/users/edit_user.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def delete_user_view(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        if Utilities.is_admin(current_user):
            user_id = request.GET.get('user_id')
            if Utilities.is_valid_str(user_id):
                user_id_int = int(user_id)
                Utilities.delete_user(user_id=user_id_int)
    return HttpResponseRedirect(ENDPOINTS.USERS)


#   --------------------------------------------------------------------------------------------------------------------


def construction_site_view(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Строительные объекты',
            'active_construction_sites': [],
            'hidden_construction_sites': []
        }

        current_user = UserService.get_current_user(request.user.pk)
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        construction_site_list = None
        foreman_list = UserService.get_foreman_list()
        context['foreman_list'] = foreman_list

        if Utilities.is_admin(current_user):
            construction_site_list = ConstructionSiteService.get_active_cs_list()

        if Utilities.is_foreman(current_user):
            construction_site_list = [
                cs for cs in ConstructionSiteService.get_active_cs_list()
                if cs.foreman == current_user.id
            ]

        if Utilities.is_master(current_user):
            construction_site_list = [
                cs for cs in ConstructionSiteService.get_active_cs_list()
                if cs.foreman == current_user.supervisor_user_id
            ]

        for construction_site in construction_site_list:
            if construction_site.status:
                context['active_construction_sites'].append(construction_site)
            else:
                context['hidden_construction_sites'].append(construction_site)

        hide_constr_site_id = request.GET.get('hide')
        if Utilities.is_valid_str(hide_constr_site_id):
            ConstructionSiteService.hide_or_show(id=hide_constr_site_id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        delete_constr_site_id = request.GET.get('delete')
        if Utilities.is_valid_str(delete_constr_site_id):
            Utilities.delete_construction_site(construction_site_id=int(delete_constr_site_id))
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, 'content/construction_site/construction_sites.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def archive_construction_site_view(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Архив объектов'
        }

        current_user = UserService.get_current_user(request.user.pk)
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        construction_site_list = None
        foreman_list = UserService.get_foreman_list()
        context['foreman_list'] = foreman_list


        if Utilities.is_admin(current_user):
            construction_site_list = ConstructionSiteService.get_deleted_cs_list()

        if Utilities.is_foreman(current_user):
            construction_site_list = [
                cs for cs in ConstructionSiteService.get_deleted_cs_list()
                if cs.foreman == current_user.id
            ]

        if Utilities.is_master(current_user):
            construction_site_list = [
                cs for cs in ConstructionSiteService.get_deleted_cs_list()
                if cs.foreman == current_user.supervisor_user_id
            ]

        context['construction_sites'] = construction_site_list
        delete_constr_site_id = request.GET.get('delete')

        if Utilities.is_valid_str(delete_constr_site_id):
            ConstructionSiteService.delete(id=delete_constr_site_id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, 'content/construction_site/archive_construction_sites.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def edit_construction_sites(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Изменить объект',
            "foreman_list": []
        }

        current_user = UserService.get_current_user(request.user.pk)

        if Utilities.is_foreman(current_user):
            foreman_list = [current_user]
            context['foreman_list'] = foreman_list
        elif Utilities.is_master(current_user):
            context['foreman_list'] = [
                foreman
                for foreman in UserService.get_foreman_list()
                if foreman.id == current_user.supervisor_user_id
            ]
        elif Utilities.is_admin(current_user):
            context['foreman_list'] = UserService.get_foreman_list()

        if request.method == 'POST':
            _id = request.POST.get('id')

            cs_data = EditConstructionSiteSchema(
                address=request.POST.get('address'),
                foreman=request.POST.get('foreman'),
            )

            cs_is_exists = (ConstructionSiteService.is_exist(data=cs_data))
            if cs_is_exists:
                ConstructionSiteService.restore_if_was_deleted(data=cs_data)
            else:
                if _id:
                    ConstructionSiteService.edit(constr_site_id=int(_id), data=cs_data)
                else:
                    ConstructionSiteService.create(data=cs_data)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        constr_site_id = request.GET.get('id')
        if Utilities.is_valid_str(constr_site_id):
            constr_site = ConstructionSiteService.get_object(id=constr_site_id)
            if constr_site:
                context['constr_site'] = constr_site
            else:
                return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, 'content/construction_site/edit_construction_site.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

#   -----------------------------------------------------------------------------------------------


def change_status_application_today(request):
    if request.user.is_authenticated:
        application_today_id = request.GET.get('application_today_id')
        current_day_str = request.GET.get('current_day')
        current_status = request.GET.get('current_status')

        workday = Utilities.get_current_day_data(current_day_str)

        if Utilities.is_valid_str(application_today_id):
            up_level_status = Utilities.change_up_status_for_application_today(
                workday_data=workday,
                application_today_id=application_today_id)
            if up_level_status == ASSETS.ApplicationTodayStatus.SEND.title:
                Utilities.send_app_by_telegram(workday_data=workday, application_today_id=application_today_id)

        elif Utilities.is_valid_str(current_day_str) and Utilities.is_valid_str(current_status):
            up_level_status = Utilities.change_up_status_for_application_today(
                workday_data=workday,
                current_status=current_status
            )
            if up_level_status == ASSETS.ApplicationTodayStatus.SEND.title:
                Utilities.send_app_by_telegram(workday_data=workday)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)

def change_weekend_to_workday(request):
    """
    Изменения выходного дня на рабочий
    :param request:
    :return:
    """
    if request.user.is_authenticated:
        _workday = request.GET.get('current_day')
        if Utilities.is_valid_str(_workday):
            current_workday = Utilities.get_current_day_data(_workday)
            workday = WorkDayService.get_object(id=current_workday.id)
            if not workday.status:
                workday.status = True
                workday.save(update_fields=['status'])
                cache.delete(WorkDayService.CacheKeys.RANGE_WORKDAYS.value)
                cache.delete(f"{WorkDayService.CacheKeys.CURRENT_DATE_DATA.value}:{current_workday.date}")
                workday_data = WorkDaySchema(**workday.to_dict())
                Utilities.prepare_driver_sheet(workday_data=workday_data)
                Utilities.prepare_technic_sheet(workday_data=workday_data)
            return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={workday.date}')
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def conflicts_list_view(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        current_day_str = request.GET.get('current_day')
        if Utilities.is_admin(current_user):
            context = {'title': 'Conflict List'}

            current_day = Utilities.get_current_day_data(current_day_str)
            context['current_day'] = current_day

            priority_id_list = Utilities.get_priority_ids_list(current_day)
            context['priority_id_list'] = priority_id_list

            busiest_technic_title_list = Utilities.get_busiest_technic_title(current_day)
            conflict_technic_sheet = Utilities.get_conflict_list_of_technic_sheet(
                busiest_technic_title=busiest_technic_title_list,
                priority_id_list=priority_id_list
            )
            if conflict_technic_sheet:
                for conflict_ts in conflict_technic_sheet:
                    conflict_ts.total_technic_sheet_count = ApplicationTechnicService.get_queryset(
                        isArchive=False,
                        is_cancelled=False,
                        isChecked=False,
                        technic_sheet_id__in=conflict_ts.id_list,
                        priority=1
                    ).values_list('priority', flat=True).count()

                context['conflict_technic_sheet'] = conflict_technic_sheet
                return render(request, 'content/spec/conflicts_list.html', context)
            else:
                return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day.date}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return HttpResponseRedirect(ENDPOINTS.LOGIN)

def conflict_resolution_view(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.pk)
        if Utilities.is_admin(current_user):
            context = {'title': 'Conflict Resolution'}

            conflict_list_id = request.GET.get('conflict_list_id')
            conflict_list_id = conflict_list_id.strip('[]').split(', ')
            current_day_str = request.GET.get('current_day')
            current_day = Utilities.get_current_day_data(current_day_str)
            context['current_day'] = current_day
            if conflict_list_id is None or len(conflict_list_id) <= 0:
                return HttpResponseRedirect(ENDPOINTS.CONFLICT_LIST)

            applications_technic = ApplicationTechnicService.get_queryset(
                technic_sheet__in=conflict_list_id,
                is_cancelled=False,
                isChecked=False,
                isArchive=False
            ).select_related(
                'technic_sheet',
                'application_today__construction_site__foreman'
            )
            conflict_applications_technic = applications_technic.values(
                'id',
                'technic_sheet_id',
                'priority',
                'application_today__construction_site__address',
                'application_today__construction_site__foreman__last_name',
                'description'
            )
            context['applications_technic'] = conflict_applications_technic
            total_count_apps = conflict_applications_technic.count()

            color_list = Utilities.set_color_for_list(conflict_list_id)
            context['color_list'] = color_list

            technic_title = applications_technic.values_list(
                'technic_sheet__technic__title', flat=True).first()
            context['technic_title'] = technic_title

            technic_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
            driver_sheet_for_date = DriverSheetService.get_driver_sheet_for_date(current_day)
            driver_sheet_ids = [
                ds.id
                for ds in driver_sheet_for_date
                if ds and ds.status
            ]
            technic_sheets_data = [
                ts
                for ts in technic_sheet_for_date
                if ts.driver_sheet in driver_sheet_ids
                   and ts.status and not ts.isArchive
            ]

            technic_sheets = TechnicSheetService.get_queryset(
                isArchive=False,
                status=True,
                driver_sheet__isnull=False,
                driver_sheet__status=True,
                date_id=current_day.id
            ).select_related('technic', 'driver_sheet__driver')

            technic_titles_dict = TechnicService.get_dict_short_technic_names(technic_sheets_data)
            context['technic_titles_dict'] = technic_titles_dict

            if request.method == 'POST':
                update_list = []
                application_technic_id_list = request.POST.getlist('application_technic_id')
                for application_technic_id in application_technic_id_list:
                    title = request.POST.get(f"{application_technic_id}_title")
                    technic_sheet_id = request.POST.get(f"{application_technic_id}_technic_sheet")
                    priority = request.POST.get(f"{application_technic_id}_priority")
                    description = request.POST.get(f"{application_technic_id}_description")

                    application_technic = ApplicationTechnicService.get_object(id=application_technic_id)
                    if not Utilities.is_valid_str(technic_sheet_id):
                        technic_title_dict = [*filter(lambda item: item['short_title'] == title,
                                                      technic_titles_dict)][0]
                        n_technic_title = technic_title_dict.get('title')
                        some_technic_sheet = TechnicSheetService.get_some_technic_sheet(
                            technic_title=n_technic_title, workday_sheet_id=current_day.id
                        )
                    else:
                        some_technic_sheet = TechnicSheetService.get_object(id=technic_sheet_id)
                    description = description if description else ''
                    if application_technic.technic_sheet.id != some_technic_sheet.id:
                        TechnicSheetService.decrement_count_application(application_technic.technic_sheet)
                        application_technic.technic_sheet = some_technic_sheet
                        TechnicSheetService.increment_count_application(some_technic_sheet)
                    application_technic.priority = priority
                    application_technic.description = description
                    update_list.append(application_technic)
                ApplicationTechnic.objects.bulk_update(update_list, ['technic_sheet', 'priority', 'description'])

            technic_driver_list = EditApplicationService.get_technic_driver_list(
                technic_titles=technic_titles_dict,
                technic_sheets_instance=technic_sheets)
            context['technic_driver_list'] = technic_driver_list


            priority_id_list = Utilities.get_priority_ids_list(workday_data=current_day)
            context['priority_id_list'] = priority_id_list
            busiest_technic_title_list = Utilities.get_busiest_technic_title(current_day)
            conflict_technic_sheet = Utilities.get_conflict_list_of_technic_sheet(
                busiest_technic_title=busiest_technic_title_list,
                priority_id_list=priority_id_list
            )

            if conflict_technic_sheet:
                conflict_ts = [
                    c.model_dump()
                    for c in conflict_technic_sheet
                    if c and c.technic_title == technic_title
                ]
                if conflict_ts:
                    conflict_ts = conflict_ts.pop()
                    conflict_ts['total_count_apps'] = total_count_apps
                    context['conflict_technic_sheet'] = conflict_ts
                else:
                    return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')
            else:
                return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')

                # end POST =============================================================
            return render(request, 'content/spec/conflict_resolution.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_technic_application(request):
    if request.user.is_authenticated:
        current_user = UserService.get_current_user(request.user.id)
        if Utilities.is_admin(current_user):
            template = 'content/applications_list/technic_application_list_for_admin.html'
        else:
            template = 'content/applications_list/technic_application_list.html'

        context = {'title': 'Заявки на технику'}

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)
        context = Utilities.prepare_data_for_filter(context)
        # context['current_day'] = current_day

        if request.method == 'POST':
            operation = request.POST.get('operation')
            if Utilities.is_valid_str(operation) and operation == 'set_props_for_filter':
                Utilities.set_data_for_filter(request)

            app_technic_id_list = request.POST.getlist('app_technic_id')
            app_technic_priority = request.POST.getlist('app_technic_priority')
            app_technic_description = request.POST.getlist('app_technic_description')

            list_for_updates = []
            for _id, _priority, _description in zip(app_technic_id_list, app_technic_priority, app_technic_description):
                if Utilities.is_valid_str(_priority) and Utilities.is_valid_str(_id):
                    app_technic = ApplicationTechnicService.get_object(id=_id)
                    if app_technic is not None:
                        app_technic.priority = _priority
                        app_technic.description = _description
                        list_for_updates.append(app_technic)
            ApplicationTechnic.objects.bulk_update(objs=list_for_updates, fields=['priority', 'description'])


        # TODO:===========================================================
        # app_today_for_date = ApplicationTodayService.get_app_today_for_date(current_day)
        # app_tech_for_date = ApplicationTechnicService.get_app_tech_for_date(current_day)
        # technic_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
        # driver_sheet_for_date = DriverSheetService.get_driver_sheet_for_date(current_day)
        # c_site_list = ConstructionSiteService.get_cs_active_list()
        #
        # application_today_list = [at for at in app_today_for_date
        #                      if at.status != ASSETS.ApplicationTodayStatus.SAVED.title]

        application_technic_list = (ApplicationTechnicService.get_queryset(
            application_today__date_id=current_day.id,
            isArchive=False,
            is_cancelled=False,
            isChecked=False
        ).select_related('application_today__construction_site__foreman')
                                    .exclude(application_today__status=ASSETS.ApplicationTodayStatus.SAVED.title))

        if not Utilities.is_admin(current_user):
            application_technic_list = application_technic_list.filter(
                application_today__status__in=ASSETS.SHOW_APPLICATIONS_WITH_STATUSES)
            # application_today_list = [at for at in application_today_list
            #                  if at.status in ASSETS.SHOW_APPLICATIONS_WITH_STATUSES]

        if current_user.filter_technic:
            application_technic_list = application_technic_list.filter(
                technic_sheet__technic__title=current_user.filter_technic)
        if current_user.filter_foreman != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site__foreman_id=current_user.filter_foreman)
            # c_site_list = [cs for cs in c_site_list if cs.foreman == current_user.filter_foreman]

        if current_user.filter_construction_site != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site_id=current_user.filter_construction_site)
            # c_site_list = [cs for cs in c_site_list if cs.id == current_user.filter_construction_site]

        technic_sheet_list = application_technic_list.values('technic_sheet').distinct()

        if current_user.sort_by == 'technic':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__technic__title')
        elif current_user.sort_by == 'driver':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__driver_sheet__driver__last_name')
        else:
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__driver_sheet__driver__last_name')

        technic_sheet_queryset_list = list(TechnicSheetService.get_queryset(
            date_id=current_day.id
        ).select_related('technic', 'driver_sheet__driver__last_name').values(
            'id',
            'technic__title',
            'driver_sheet__driver__last_name',
        ))

        application_technic_list = list(application_technic_list.values(
            'id',
            'technic_sheet_id',
            'priority',
            'application_today__construction_site__address',
            'application_today__construction_site__foreman__last_name',
            'description'
        ).order_by('priority'))

        application_technics = []
        for technic_sheet in technic_sheet_list:
            application_technics.append({
                # 'technic_sheet': TECHNIC_SHEET_SERVICE.get_technic_sheet(
                #     pk=technic_sheet['technic_sheet']
                # ),
                'technic_sheet': [t for t in technic_sheet_queryset_list
                                  if t['id']==technic_sheet['technic_sheet']][0],
                # 'applications_list': application_technic_list.filter(
                #     technic_sheet_id=technic_sheet['technic_sheet']).order_by('priority')
                'applications_list': [a for a in application_technic_list
                                      if a['technic_sheet_id'] == technic_sheet['technic_sheet']]
            })

        context['application_technics'] = application_technics

        # temp_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        #     isArchive=False,
        #     status=True,
        #     driver_sheet__isnull=False,
        #     date=current_day
        # )
        context['priority_id_list'] = Utilities.get_priority_ids_list(current_day)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_material_application(request):
    if request.user.is_authenticated:
        context = {'title': 'Materials Applications'}
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        current_user = UserService.get_current_user(request.user.id)
        context = Utilities.get_prepared_data(context, current_day)

        context = Utilities.prepare_data_for_filter(context)

        if request.method == 'POST':
            operation = request.POST.get('operation')
            if Utilities.is_valid_str(operation) and operation == 'set_props_for_filter':
                Utilities.set_data_for_filter(request)

        application_today_id_list = ApplicationTodayService.get_queryset(
            isArchive=False,
            date_id=current_day.id,
        ).exclude(status=ASSETS.ApplicationTodayStatus.SAVED.title).values_list('pk', flat=True)

        if current_user.filter_foreman != 0:
            application_today_id_list = application_today_id_list.filter(
                construction_site__foreman_id=current_user.filter_foreman
            )

        if current_user.filter_construction_site != 0:
            application_today_id_list = application_today_id_list.filter(
                construction_site_id=current_user.filter_construction_site
            )

        application_materials_list = ApplicationMaterialService.get_queryset(
            isArchive=False,
            application_today_id__in=application_today_id_list,
        ).select_related('application_today__construction_site__foreman')
        context['application_materials_list'] = application_materials_list

        return render(request, 'content/applications_list/material_application_list.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def material_application_supply_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Materials Applications'}
        _is_print = request.GET.get('print')

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        if Utilities.is_valid_str(_is_print):
            application_materials_list = ApplicationMaterialService.get_queryset(
                application_today__status__in=ASSETS.SHOW_APPLICATIONS_FOR_SUPPLY_WITH_STATUSES,
                isArchive=False,
                application_today__date_id=current_day.id,
                isChecked=True
            ).select_related('application_today__construction_site__foreman')
            context['application_materials_list'] = application_materials_list
            context['weekday'] = ASSETS.WEEKDAY[current_day.date.weekday()]
            return render(request, 'content/spec/print_material_application.html', context)

        if request.method == 'POST':
            application_material_id = request.POST.get('application_material_id')
            application_material_description = request.POST.get('app_material_description')
            operation = request.POST.get('operation')
            if operation == 'accept_application_material' and Utilities.is_valid_str(application_material_id):

                application_material = ApplicationMaterialService.get_object(id=application_material_id)
                if application_material:
                    if application_material_description != application_material.description or not application_material.isChecked:
                        application_material.description = application_material_description
                        application_material.isChecked = True
                        application_material.save()
                        return HttpResponse(b"true")
                    else:
                        application_material.isChecked = False
                        application_material.save()
                        return HttpResponse(b"false")
                else:
                    return HttpResponse(b"false")

        application_materials_list = ApplicationMaterialService.get_queryset(
            application_today__status__in=ASSETS.SHOW_APPLICATIONS_FOR_SUPPLY_WITH_STATUSES,
            isArchive=False,
            application_today__date_id=current_day.id
        ).select_related('application_today__construction_site__foreman')
        context['application_materials_list'] = application_materials_list

        return render(request, 'content/applications_list/material_application_list_for_supply.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def application_for_driver_view(request):
    if request.user.is_authenticated:
        context = {}
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        technic_sheet_list = TechnicSheetService.get_queryset(
            date_id=current_day.id,
            isArchive=False,
        ).select_related(
            "technic__attached_driver", "driver_sheet__driver"
        ).order_by(
            'driver_sheet__driver'
        )

        if not technic_sheet_list.exists():
            Utilities.prepare_sheets(current_day)

        context["technic_sheet_list"] = technic_sheet_list

        application_technic_list = list(ApplicationTechnicService.get_queryset(
            application_today__date_id=current_day.id,
            isArchive=False,
            is_cancelled=False,
        ).select_related(
            "application_today__construction_site__foreman"
        ).order_by("priority").values(
            "application_today__construction_site__address",
            "application_today__construction_site__foreman__last_name",
            "description",
            "technic_sheet_id"
        ))

        applications_technic = []
        for technic_sheet in technic_sheet_list:
            applications_technic.append(
                {
                    "technic_sheet_id": technic_sheet.id,
                    "applications": [at for at in application_technic_list if technic_sheet.id == at["technic_sheet_id"]]
                }
            )
        context["applications_technic"] = applications_technic

        return render(request, 'content/applications_list/application_for_drivers.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def profile_view(request):
    if request.user.is_authenticated:
        template = 'content/profile.html'
        context = {}

        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        context = Utilities.get_prepared_data(context, current_day)

        user_id = request.GET.get('user_id')
        if user_id is not None and user_id != '':
            current_user = UserService.get_current_user(user_id)
        else:
            current_user = UserService.get_current_user(request.user.id)

        current_user_key = TelegramService.get_user_key(current_user.id)
        context['user_key'] = current_user_key

        if request.method == 'POST':
            operation = request.POST.get('operation')
            new_password_0 = request.POST.get('new_password_0')
            new_password_1 = request.POST.get('new_password_1')

            username = request.POST.get('username')
            last_name = request.POST.get('last_name')
            first_name = request.POST.get('first_name')
            telephone = request.POST.get('telephone')
            user = UserService.get_object(id=current_user.id)

            if operation == 'change_profiler':
                if user:
                    if Utilities.is_valid_str(username):
                        user.username = username
                    if Utilities.is_valid_str(last_name):
                        user.last_name = last_name
                    if Utilities.is_valid_str(first_name):
                        user.first_name = first_name
                    if Utilities.is_valid_str(telephone):
                        user.telephone = UserService.validate_telephone(telephone)
                    user.save()
                    cache.delete(f"{UserService.CacheKeys.ALL_USER_LIST.value}")
                    cache.delete(f"{UserService.CacheKeys.CURRENT_USER.value}:{current_user.id}")
                log.info("Changed profile successfully")
                return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

            if operation == 'changePassword':
                if user:
                    if Utilities.is_valid_str(new_password_0) and Utilities.is_valid_str(new_password_1):
                        if new_password_0 == new_password_1:
                            user.set_password(new_password_0)
                            user.save()
                            log.info("Changed password successfully")
                            return HttpResponse(b"accept")

            _user_key = request.POST.get('user_key')
            if _user_key is not None and _user_key != '':
                _chat_id = telegram.get_id_chat(key=_user_key, result=telegram.get_result())
                if _chat_id:
                    user.telegram_id_chat = _chat_id
                    user.save()
                    TelegramService.send_messages(chat_id=_chat_id, messages='Связь установлена')
                    cache.delete(f"{UserService.CacheKeys.ALL_USER_LIST.value}")
                    cache.delete(f"{UserService.CacheKeys.CURRENT_USER.value}:{current_user.id}")

        context['current_user'] = current_user
        return render(request, template, context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def def_test(request):  # TODO: def TEST
    context = {}
    # current_day = WORK_DAY_SERVICE.get_current_day(request)
    # context = U.get_prepared_data(context, current_day)
    # context['current_day'] = current_day
    # _current_day = request.GET.get('current_day')
    # if _current_day:
    #     current_day = WorkDaySheet.objects.get(date=_current_day)
    # else:
    #     current_day = WorkDaySheet.objects.get(date=U.TODAY)
    # work_days = U.get_work_days().values()
    # for work_day in work_days:
    #     work_day['weekday'] = ASSETS.WEEKDAY[work_day['date'].weekday()][:3]

    # if request.GET.get('chat_id'):
    #     chat_id = request.GET.get('chat_id')
    #     print(
    #         f"{request.user.id} -- {chat_id}"
    #     )
    #     return HttpResponse(chat_id)
    # context = {
    #     'title': 'Test',
    #     'today': U.TODAY,
    #     'current_day': current_day,
    #     'work_days': work_days,
    #     # 'weekday': ASSETS.WEEKDAY
    # }

    # driver_mess = request.POST.get('driver')
    # foreman_mess = request.POST.get('foreman')
    # admin_mess = request.POST.get('admin')
    #
    # wd = WORK_DAY_SERVICE.get_current_day(request)
    #
    # if U.is_valid_get_request(driver_mess):
    #     U.send_application_by_telegram_for_driver(wd, messages=driver_mess)
    #
    # if U.is_valid_get_request(foreman_mess):
    #     U.send_application_by_telegram_for_foreman(wd, messages=foreman_mess)
    #
    # if U.is_valid_get_request(admin_mess):
    #     U.send_application_by_telegram_for_admin(wd, messages=admin_mess)
    return render(request, 'content/tests/change_workday.html', context)


def maintenance_view(request):
    template = 'content/spec/maintenance.html'
    context = {}
    return render(request, template, context)


def settings_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Параметры'}
        current_user = UserService.get_current_user(request.user.id)
        ParameterService.prepare_global_parameters()

        if request.method == 'POST':

            request_data = request.POST
            parameter_name_list = request_data.getlist("parameters_name")

            set_param_list = []
            for raw_par_name in parameter_name_list:
                name_=str(raw_par_name).strip()
                set_param_list.append(
                    SetParameterSchema(
                        name=name_,
                        value = request_data.get(f"{name_}__value"),
                        flag = request_data.get(f"{name_}__flag", False),
                        time = request_data.get(f"{name_}__time"),
                        date = request_data.get(f"{name_}__date"),
                        description = request_data.get(f"{name_}__description")
                    )
                )
            ParameterService.set_parameters(set_param_list)

            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
        if Utilities.is_admin(current_user):
            parameter_list = ParameterService.get_queryset()
        elif Utilities.is_supply(current_user):
            parameter_list = ParameterService.get_parameter_for_supply()
        else:
            parameter_list = None
        context['parameter_list'] = parameter_list
        return render(request, 'content/spec/settings.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def task_desc_for_spec_constr_site_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Шаблоны заданий для "Спец. объекта"'}

        if request.method == 'POST':
            if request.POST.get('operation') == 'set_task_description':
                technic_id = request.POST.get('technic_id')
                task_mode = request.POST.get('task_mode')
                manual_description = request.POST.get('manual_description')

                TemplateDescService.set_task_description(int(technic_id), task_mode, manual_description)

        default_task_description = ParameterService.get_object(
            name=VAR.VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE['name']
        )
        technic_list = list(TechnicService.get_queryset(
            isArchive=False,
        ).values('id', 'title', 'attached_driver__last_name'))

        if request.POST.get('default_task_description') is not None:
            default_task_description.value = request.POST.get('default_task_description')
            default_task_description.save()
            context['default_task_description'] = request.POST.get('default_task_description')
        else:
            context['default_task_description'] = default_task_description.value

        task_description_list = TemplateDescService.get_queryset().values(
            'technic',
            'description',
            'is_auto_mode',
            'is_default_mode'
        )
        task_description_list = {task['technic']: {
            'description': task['description'],
            'is_auto_mode': task['is_auto_mode'],
            'is_default_mode': task['is_default_mode'],
        } for task in task_description_list}


        for technic in technic_list:
            technic['task_description'] = task_description_list.get(technic['id'])
        context['technic_list'] = technic_list

        return render(request, 'content/spec/task_description_for_spec_constr_site.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def calculate_all_applications(request):
    if request.user.is_authenticated:
        current_day = Utilities.get_current_day_data(request.GET.get('current_day'))
        technic_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
        ts_ids = [ts.id for ts in technic_sheet_for_date]
        Utilities.calculate_all_app_for_technic_sheet(ts_ids)
        cache.delete(f"{TechnicSheetService.CacheKeys.TECH_SHEET_FOR_DAY.value}:{current_day.date}")
        log.info(f"Считаем все заявки на технику за {current_day.date}")
        return HttpResponseRedirect(f"{ENDPOINTS.DASHBOARD}?current_day={current_day.date}")
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def spec_page_view(request):
    if request.user.is_authenticated:
        page_type = request.GET.get('page_type')
        from config.settings import BASE_DIR
        if page_type == 'info':
            file_url = f'{BASE_DIR}/logs/info.log'
        elif page_type == 'error':
            file_url = f'{BASE_DIR}/logs/errors.log'
        else:
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        # file = ''

        try:
            with open(file_url, 'rt') as f:
                file = f.readlines()[-200:]
        except FileNotFoundError:
            file = 'FileNotFoundError'
            log.error('spec_page_view(): FileNotFoundError')

        return HttpResponse(file, content_type='text/plain')
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def test_page_view(request):
    import time
    start_time = time.time()



    end_time = time.time()
    print(end_time - start_time)
    return HttpResponse('mess')
