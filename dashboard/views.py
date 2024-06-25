from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate, get_user_model
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q

from dashboard.models import User
from django.contrib.auth import login, logout, authenticate
# from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import Technic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter#, Telebot

from dashboard.assets import ERROR_MESSAGES, MESSAGES
import dashboard.assets as ASSETS
import Task_manager_30.endpoints as ENDPOINTS
import dashboard.utilities as U
import dashboard.variables as VAR
# import dashboard.telegram_bot as T

#   rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
import dashboard.func.user as USERS_FUNC
import dashboard.func.technic as TECHNIC_FUNC
import dashboard.func.construction_site as CONSTR_SITE_FUNC
#   rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr

from logger import getLogger
log = getLogger(__name__)

# Create your views here.


def dashboard(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)

    _current_day = request.GET.get('current_day')
    if _current_day is None or _current_day == '':
        try:
            current_day = WorkDaySheet.objects.get(date=U.TODAY)
        except WorkDaySheet.DoesNotExist:
            current_day = U.prepare_workday(U.TODAY)
    else:
        try:
            current_day = WorkDaySheet.objects.get(date=_current_day)
        except WorkDaySheet.DoesNotExist:
            U.prepare_workday(_current_day)
            current_day = U.get_create_workday(_current_day)


    if request.POST.get('operation') == 'change_read_only_mode':
        print(request.POST.get('read_only'))
        if request.POST.get('read_only') == '0':
            U.change_reception_apps_mode_manual(current_day, False)
            # current_day.is_only_read = False
            # current_day.save(update_fields=['is_only_read'])
        if request.POST.get('read_only') == '1':
            U.change_reception_apps_mode_manual(current_day, True)
            # current_day.is_only_read = True
            # current_day.save(update_fields=['is_only_read'])

    # print(
    #     U.get_create_workday(_current_day)
    # )

    context = {
        'title': request.user,
        'current_day': current_day,
        'weekday': U.get_weekday(current_day),
        'ONLY_READ': current_day.is_only_read,
        # 'ONLY_READ_time': '16.00',
        'APPLICATION_STATUS': ASSETS.APPLICATION_STATUS_dict
    }
    context = U.get_prepared_data(context, current_day.date)
    context = U.get_prepare_filter(context)

    if not current_day.status:
        if _current_day is None or _current_day == '':
            return HttpResponseRedirect(
                ENDPOINTS.DASHBOARD + f'?current_day={U.get_next_work_day(current_day.date).date}')
        return render(request, 'content/spec/weekend.html', context)

    status_list_application_today = U.get_status_list_application_today(current_day)
    context['status_list_application_today'] = status_list_application_today    # TODO: fix for supply and ...

    if request.method == 'POST':
        U.set_prepare_filter(request)

        if request.POST.get('operation') == 'copy':
            target_day = request.POST.get('target_day')
            application_id = request.POST.get('application_id')
            if all((target_day, application_id)):
                if U.is_administrator(request.user):
                    default_app_status = ASSETS.SUBMITTED
                else:
                    default_app_status = ASSETS.SAVED
                U.copy_application(application_id, target_day, default_app_status)

    if U.is_administrator(request.user):
        if request.method == 'POST':
            if request.POST.get('operation') == 'set_spec_task':
                technic_sheet_id = request.POST.get('technic_sheet_id')
                if technic_sheet_id:
                    U.set_spec_task(technic_sheet_id)

        priority_id_list = U.get_priority_id_list(current_day)
        context['priority_id_list'] = priority_id_list
        conflict_technic_sheet = U.get_conflict_technic_sheet(
            U.get_busiest_technic_title(current_day),
            priority_id_list, get_id_list=True)
        context['conflict_technic_sheet'] = conflict_technic_sheet

        # print(conflict_technic_sheet)
        # print(status_list_application_today)

        construction_sites = ConstructionSite.objects.filter(isArchive=False, status=True)

        if not request.user.is_show_absent_app:
            construction_sites = construction_sites.filter(applicationtoday__date=current_day)

        if not request.user.is_show_saved_app:
            construction_sites = construction_sites.exclude(applicationtoday__status=ASSETS.SAVED)

        applications_today = ApplicationToday.objects.filter(isArchive=False,
                                                             construction_site__in=construction_sites,
                                                             date=current_day).order_by('status')
        if request.user.is_show_technic_app:
            applications_technic = ApplicationTechnic.objects.filter(isArchive=False,
                                                                     application_today__in=applications_today)
        else:
            applications_technic = ApplicationTechnic.objects.none()
        if request.user.is_show_material_app:
            application_material = ApplicationMaterial.objects.filter(isArchive=False,
                                                                      application_today__in=applications_today)
        else:
            application_material = ApplicationMaterial.objects.none()

        context['table_working_technic_sheet'] = U.get_table_working_technic_sheet(current_day)

        context['applications_today_list'] = applications_today
        context['construction_sites'] = construction_sites.values()
        for construction_site in context['construction_sites']:
            construction_site['foreman'] = User.objects.get(
                id=construction_site['foreman_id']) if construction_site['foreman_id'] is not None else None

            construction_site['application_today'] = applications_today.filter(
                construction_site_id=construction_site['id']).values().first()
            if construction_site['application_today']:
                construction_site['application_today']['application_material'] = application_material.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id', 'isChecked', 'description').first()
                construction_site['application_today']['application_technic'] = applications_technic.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id',
                    'technic_sheet__technic__title',
                    'technic_sheet__driver_sheet__driver__last_name',
                    'technic_sheet__driver_sheet__driver__first_name',
                    'technic_sheet__driver_sheet__status',
                    'technic_sheet__count_application',
                    'technic_sheet__status',
                    'priority',
                    'description',
                    'is_cancelled',
                    'isChecked',
                    'technic_sheet_id'
                )

        return render(request, 'content/dashboard/admin_dashboard.html', context)
    # elif is_foreman(request.user):
    # return render(request, 'content/dashboard/foreman_dashboard.html', context)

    elif U.is_master(request.user) or U.is_foreman(request.user):
        if U.is_foreman(request.user):
            _foreman = request.user
        else:
            try:
                _foreman = User.objects.get(id=request.user.supervisor_user_id)
            except User.DoesNotExist:
                return HttpResponseRedirect(ENDPOINTS.ERROR)

        construction_sites = ConstructionSite.objects.filter(foreman=_foreman, isArchive=False, status=True)

        if not request.user.is_show_absent_app:
            construction_sites = construction_sites.filter(applicationtoday__date=current_day)

        if not request.user.is_show_saved_app:
            construction_sites = construction_sites.exclude(applicationtoday__status=ASSETS.SAVED)

        applications_today = ApplicationToday.objects.filter(isArchive=False,
                                                             construction_site__in=construction_sites,
                                                             date=current_day)
        if request.user.is_show_technic_app:
            applications_technic = ApplicationTechnic.objects.filter(isArchive=False,
                                                                     application_today__in=applications_today)
        else:
            applications_technic = ApplicationTechnic.objects.none()
        if request.user.is_show_material_app:
            application_material = ApplicationMaterial.objects.filter(isArchive=False,
                                                                      application_today__in=applications_today)
        else:
            application_material = ApplicationMaterial.objects.none()
        context['applications_today_list'] = applications_today
        context['construction_sites'] = construction_sites.values()

        for construction_site in context['construction_sites']:
            construction_site['foreman'] = _foreman
            construction_site['application_today'] = applications_today.filter(
                construction_site_id=construction_site['id']).values().first()
            if construction_site['application_today']:
                construction_site['application_today']['application_material'] = application_material.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id', 'isChecked', 'description').first()
                construction_site['application_today']['application_technic'] = applications_technic.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id',
                    'technic_sheet__technic__title',
                    'technic_sheet__driver_sheet__driver__last_name',
                    'technic_sheet__driver_sheet__driver__first_name',
                    'technic_sheet__count_application',
                    'technic_sheet__status',
                    'priority',
                    'description',
                    'is_cancelled',
                    'isChecked'
                )
        return render(request, 'content/dashboard/foreman_dashboard.html', context)

    elif U.is_mechanic(request.user):

        technic_sheet_list = TechnicSheet.objects.filter(date=current_day,
                                                         isArchive=False)
        context['technic_sheet_list'] = technic_sheet_list
        application_technic_list = ApplicationTechnic.objects.filter(application_today__date=current_day,
                                                                     application_today__status=ASSETS.SEND,
                                                                     isArchive=False,
                                                                     is_cancelled=False)
        applications_technic = []
        for technic_sheet in technic_sheet_list:
            applications_technic.append({
                'technic_sheet_id': technic_sheet.id,
                'applications': application_technic_list.filter(technic_sheet=technic_sheet).order_by('priority')
            })
        context['applications_technic'] = applications_technic

        return render(request, 'content/dashboard/mechanic_dashboard.html', context)

    elif U.is_supply(request.user):
        construction_site, _created = ConstructionSite.objects.get_or_create(address=ASSETS.CS_SUPPLY_TITLE)
        application_today = ApplicationToday.objects.filter(date=current_day,
                                                            construction_site=construction_site,
                                                            isArchive=False
                                                            ).first()
        if request.method == 'POST':
            application_technic_id = request.POST.get('applicationTechnicId')
            _operation = request.POST.get('operation')
            application_today_id = request.POST.get('application_today_id')

            if application_technic_id and _operation == 'reject':
                U.change_is_cancelled(application_technic_id)
                # if not applications_technic.exists():
                #     application_today.

            elif application_technic_id and _operation == 'accept':
                if not application_today_id:
                    _application_today = ApplicationToday.objects.create(date=current_day,
                                                                         construction_site=construction_site,
                                                                         status=ASSETS.SAVED)
                    application_today_id = _application_today.id
                print(request.POST)
                U.change_is_checked(application_technic_id, application_today_id)

        count_app_mater_not_checked = ApplicationMaterial.objects.filter(isArchive=False,
                                                                         application_today__date=current_day,
                                                                         isChecked=False).count()
        if count_app_mater_not_checked > 0:
            context['count_app_mater_not_checked'] = count_app_mater_not_checked

        applications_technic = ApplicationTechnic.objects.filter(isArchive=False,
                                                                 application_today=application_today)
        applications_material = ApplicationMaterial.objects.filter(isArchive=False,
                                                                   application_today=application_today).first()

        supply_technic_list = Technic.objects.filter(isArchive=False,
                                                     supervisor_technic=ASSETS.SUPPLY)
        applications_technic_for_supply = []
        _app_tech = ApplicationTechnic.objects.filter(
            application_today__date=current_day,
            isArchive=False
        ).exclude(application_today__construction_site=construction_site)
        _app_tech = _app_tech.exclude(application_today__status=ASSETS.SAVED)

        for _technic in supply_technic_list:
            _application_technic = _app_tech.filter(technic_sheet__technic=_technic)
            applications_technic_for_supply.append({
                'technic': _technic,
                'application_technic': _application_technic
            })
            if _application_technic.exists():
                context['a_m_exists'] = True

        context['application_today'] = application_today
        context['construction_site'] = construction_site
        context['applications_technic'] = applications_technic
        context['applications_material'] = applications_material
        context['applications_technic_for_supply'] = applications_technic_for_supply

        return render(request, 'content/dashboard/supply_dashboard.html', context)



    elif U.is_employee(request.user):
        priority_id_list = U.get_priority_id_list(current_day)
        applications_today = ApplicationToday.objects.filter(isArchive=False,
                                                             status=ASSETS.SEND,
                                                             date=current_day).order_by('status')
        construction_sites = ConstructionSite.objects.filter(
            isArchive=False, status=True, applicationtoday__in=applications_today)

        if request.user.is_show_technic_app:
            applications_technic = ApplicationTechnic.objects.filter(
                isArchive=False, application_today__in=applications_today, isChecked=False, is_cancelled=False)
        else:
            applications_technic = ApplicationTechnic.objects.none()
        if request.user.is_show_material_app:
            application_material = ApplicationMaterial.objects.filter(
                isArchive=False, application_today__in=applications_today)
        else:
            application_material = ApplicationMaterial.objects.none()


        context['construction_sites'] = construction_sites.values()
        for construction_site in context['construction_sites']:
            construction_site['foreman'] = User.objects.get(
                id=construction_site['foreman_id']) if construction_site['foreman_id'] is not None else None

            construction_site['application_today'] = applications_today.filter(
                construction_site_id=construction_site['id']).values().first()
            if construction_site['application_today']:

                construction_site['application_today']['application_material'] = application_material.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id', 'isChecked', 'description').first()

                construction_site['application_today']['application_technic'] = applications_technic.filter(
                    application_today_id=construction_site['application_today']['id']).values(
                    'id',
                    'technic_sheet__technic__title',
                    'technic_sheet__driver_sheet__driver__last_name',
                    'technic_sheet__driver_sheet__driver__first_name',
                    'technic_sheet__driver_sheet__status',
                    'technic_sheet__count_application',
                    'technic_sheet__status',
                    'priority',
                    'description',
                    # 'is_cancelled',
                    # 'isChecked',
                    # 'technic_sheet_id'
                )

        return render(request, 'content/dashboard/employee_dashboard.html', context)

    elif U.is_driver(request.user):

        current_driver = request.user
        current_technic_sheet = TechnicSheet.objects.filter(
            driver_sheet__driver=current_driver, isArchive=False, status=True, date=current_day)
        _technic_application = ApplicationTechnic.objects.filter(
            isArchive=False, isChecked=False, is_cancelled=False, application_today__date=current_day,
            application_today__status=ASSETS.SEND)
        technic_application_list = []
        for tech_sheet in current_technic_sheet:
            technic_application_list.append({
                'technic_sheet': tech_sheet,
                'applications_technic': _technic_application.filter(technic_sheet=tech_sheet).order_by('priority')
            })
        context['technic_application_list'] = technic_application_list
        return render(request, 'content/dashboard/driver_dashboard.html', context)
    else:
        return HttpResponse(status=404)


def clear_application_today(request):
    if request.user.is_authenticated:
        if U.is_administrator(request.user) or U.is_foreman(request.user) or U.is_master(request.user) or U.is_supply(request.user):
            _foreman = None
            if U.is_foreman(request.user):
                _foreman = request.user
            if U.is_master(request.user):
                _foreman = User.objects.get(id=request.user.supervisor_user_id)
            app_today_id = request.GET.get('app_today_id')
            if app_today_id:
                try:
                    application_today = ApplicationToday.objects.get(id=app_today_id)
                except ApplicationToday.DoesNotExist:
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
                if _foreman != application_today.construction_site.foreman and not U.is_administrator(request.user):
                    return HttpResponseRedirect(ENDPOINTS.ERROR)
                else:
                    technic_sheet_id_list = ApplicationTechnic.objects.filter(
                        isArchive=False, application_today=application_today).values_list('technic_sheet', flat=True)
                    if U.is_supply(request.user):
                        supply_technic_list = U.get_supply_technic_list()
                        app_technic_list = ApplicationTechnic.objects.filter(
                            application_today__date=application_today.date,
                            isArchive=False,
                            technic_sheet__technic__in=supply_technic_list).exclude(application_today=application_today)
                        app_technic_list.update(isChecked=False)
                    U.calculate_technic_sheet_count_application(technic_sheet_id_list)
                    application_today.delete()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return HttpResponseRedirect(ENDPOINTS.ERROR)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def check_application_status(request):
    if request.user.is_authenticated:
        app_today_id = request.GET.get('app_today_id')
        current_day = request.GET.get('current_day')
        if U.is_administrator(request.user):
            _default_status = ASSETS.SUBMITTED
        else:
            _default_status = ASSETS.SAVED
        if app_today_id:
            try:
                app_today = ApplicationToday.objects.get(id=app_today_id)
            except ApplicationToday.DoesNotExist:
                return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

            U.check_application_today(app_today=app_today, default_status=_default_status)

            # _at_desc = app_today.description is not None and app_today.description != ''
            # _at_at = ApplicationTechnic.objects.filter(application_today=app_today).exists()
            # _at_am = ApplicationMaterial.objects.filter(application_today=app_today).exists()
            # # _at_status = app_today.status != ASSETS.ABSENT
            #
            # if any([_at_desc, _at_at, _at_am]):
            #     app_today.status = _default_status
            #     app_today.save()
            # else:
            #     app_today.delete()

            return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day}')
        return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day}')
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_application_view(request):
    if request.user.is_authenticated:
        template = 'content/dashboard/edit_application.html'
        context = {
            'title': 'Edit application'
        }

        app_today_date = request.GET.get('current_day')
        if app_today_date is not None or app_today_date != 'None':
            current_date = WorkDaySheet.objects.get(date=app_today_date)
        else:
            current_date = WorkDaySheet.objects.get(date=U.TODAY)

        context['current_day'] = current_date
        context['weekday'] = ASSETS.WEEKDAY[current_date.date.weekday()]

        if not current_date.status:
            return render(request, 'content/spec/weekend.html', context)

        context['technics'] = Technic.objects.filter(isArchive=False).distinct().values_list('title', flat=True)

        technic_sheets = TechnicSheet.objects.filter(isArchive=False,
                                                     status=True,
                                                     driver_sheet__isnull=False,
                                                     driver_sheet__status=True,
                                                     date=current_date)

        if not technic_sheets.exists():
            print('No technic sheets')
            U.prepare_sheets(current_date)

        technic_titles_dict = U.get_short_technic_name_dict(current_date)
        context['technic_titles_dict'] = technic_titles_dict

        technic_driver_list = []
        for title_short, title in technic_titles_dict.items():
            technic_driver_list.append(
                {
                    'title_short': title_short,
                    'title': title,
                    'technic_sheets': technic_sheets.filter(technic__title=title)
                }
            )
        context['technic_driver_list'] = technic_driver_list

        if request.method == 'POST':
            # print(request.POST)
            application_id = request.POST.get('application_id')  # id application_today
            construction_site_id = request.POST.get('construction_site_id')  # id construction_site
            application_description = request.POST.get('application_description')  # application_today description

            if application_id:
                application_today = ApplicationToday.objects.get(id=application_id)
            else:
                application_today = ApplicationToday.objects.create(date=current_date,
                                                                    construction_site_id=construction_site_id)

            #   Application Today -------------------------------------------------------------------------
            changed_desc_app = request.POST.get('changed_desc_app')
            if (application_id and changed_desc_app) or (changed_desc_app == 'true' and application_description):
                application_today.description = application_description
                application_today.save(update_fields=['description'])

            #   -------------------------------------------------------------------------------------------

            #   ajax - reject ------------------------------------------------------------------------------
            application_technic_id = request.POST.get('applicationTechnicId')
            _operation = request.POST.get('operation')
            if application_technic_id and _operation == 'reject':
                U.change_is_cancelled(application_technic_id)
            #   ----------------------------------------------------------------------------------------------

            #   ajax - add AT --------------------------------------------------------------------------------
            apply_application_technic_id = request.POST.get('apply_application_technic_id')
            technic_title_shrt = request.POST.get('technic_title_shrt')
            if technic_title_shrt and technic_title_shrt != 'none':
                technic_sheet_id = request.POST.get('technic_sheet_id')
                app_tech_desc = request.POST.get('app_tech_desc')
                desc = app_tech_desc if app_tech_desc is not None else ''

                if technic_sheet_id is None or technic_sheet_id == '':
                    n_technic_titles = U.get_short_technic_name(technic_title_shrt, current_date)
                    some_technic_sheet = U.get_some_technic_sheet(n_technic_titles, current_date)
                else:
                    some_technic_sheet = TechnicSheet.objects.get(id=technic_sheet_id)
                if apply_application_technic_id:
                    _at = ApplicationTechnic.objects.get(id=apply_application_technic_id)
                    U.calculate_technic_sheet_count_application(_at.technic_sheet)
                    if _at.technic_sheet_id != some_technic_sheet.id:

                        _at.technic_sheet.decrement_count_application()
                        some_technic_sheet.increment_count_application()
                    _at.technic_sheet = some_technic_sheet
                    _at.description = desc
                    _at.save(update_fields=['technic_sheet', 'description'])
                else:
                    ApplicationTechnic.objects.create(
                        application_today=application_today,
                        technic_sheet=some_technic_sheet,
                        description=desc
                    )
                    some_technic_sheet.increment_count_application()
            #   ---------------------------------------------------------------------------------------------

            # Application Material --------------------------------------------------------------------------
            app_material_id = request.POST.get('app_material_id')
            app_material_description = request.POST.get('material_description')
            if app_material_id and app_material_description == '':
                ApplicationMaterial.objects.get(id=app_material_id).delete()
            elif not app_material_id and app_material_description:
                ApplicationMaterial.objects.create(
                    application_today=application_today,
                    description=app_material_description
                )
            elif app_material_id and app_material_description:
                app_material = ApplicationMaterial.objects.get(id=app_material_id)
                app_material.description = app_material_description
                app_material.save(update_fields=['description'])
            #   ---------------------------------------------------------------------------------------------

            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        #   method GET --------------------------------------------------------------------------------------
        constr_site_id = request.GET.get('constr_site_id')
        if constr_site_id:
            try:
                construction_site = ConstructionSite.objects.get(id=constr_site_id, isArchive=False)
                context['construction_site'] = construction_site
            except ConstructionSite.DoesNotExist:
                return HttpResponseRedirect(ENDPOINTS.ERROR)

            application_today = ApplicationToday.objects.filter(
                construction_site=construction_site,
                date=current_date,
                isArchive=False
            )

            if application_today.exists():
                application_technic = ApplicationTechnic.objects.filter(isArchive=False,
                                                                        application_today__in=application_today)
                application_material = ApplicationMaterial.objects.filter(isArchive=False,
                                                                          application_today__in=application_today)

                context['application_today'] = application_today.values(
                    'id',
                    'date__date',
                    'status',
                    'description'
                ).first()
                context['application_today']['application_technic'] = application_technic.filter(
                    application_today=context['application_today']['id']).values(
                    'id',
                    'technic_sheet_id',
                    'technic_sheet__technic__title',
                    'technic_sheet__driver_sheet__driver__last_name',
                    'technic_sheet__driver_sheet__driver__first_name',
                    'is_cancelled',
                    'description'
                )
                context['application_today']['application_material'] = application_material.filter(
                    application_today=context['application_today']['id']).values(
                    'id',
                    'description',
                    'isChecked',
                    'is_cancelled'
                ).first()

        return render(request, template, context)
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
        user = authenticate(request, username=username, password=password)
        if user is None:
            username = username.capitalize()
            user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)  # TODO: redirect to Home page
        else:
            return render(request, 'content/login.html', {'error': ASSETS.ERROR_MESSAGES['login']})
    return HttpResponse(status=403)


def restore_password_view(request):
    template = 'content/spec/restore_password.html'
    context = {}
    if request.method == 'POST':
        _last_name = request.POST.get('last_name')
        last_name = _last_name.strip().lower().capitalize()
        _user = User.objects.filter(last_name=last_name)
        if _user.exists():
            context['users_list'] = _user
        else:
            context['msg'] = 'Данный пользователь не найден'
    try:
        _default_passwd = Parameter.objects.get(name=VAR.VAR_DEFAULT_PASSWORD['name']).value
    except Parameter.DoesNotExist:
        _default_passwd = '1234'

    user_id = request.GET.get('user_id')
    if user_id is not None and user_id != '':
        try:
            restore_user = User.objects.get(pk=user_id)
            restore_user.set_password(_default_passwd)
            restore_user.save()
            context['msg_success'] = {'login': restore_user.username, 'password': _default_passwd}
        except User.DoesNotExist:
            pass
    return render(request, template, context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def register_view(request):
    template = 'content/register.html'
    context = {
        'user_posts': {
            ASSETS.EMPLOYEE: ASSETS.USER_POSTS_dict[ASSETS.EMPLOYEE],
            ASSETS.DRIVER: ASSETS.USER_POSTS_dict[ASSETS.DRIVER],
        },
        'foreman_list': User.objects.filter(post=ASSETS.FOREMAN)
    }

    if request.method == 'GET':
        return render(request, template, context)
    if request.method == 'POST':
        data = request.POST
        new_user = USERS_FUNC.add_or_edit_user(data, user_id=None)
        if new_user is not None and request.user.is_anonymous:
            login(request, new_user)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
        elif new_user is not None and request.user.is_authenticated:
            return HttpResponseRedirect('/')  # TODO redirect if create new user
        else:
            context['error'] = ASSETS.ERROR_MESSAGES['register']
            return render(request, template, context)

    return HttpResponse(status=403)


#   Sheets--------------------------------------------------------------------------------------------------------------
def workday_sheet_view(request):
    if request.user.is_authenticated:
        template = 'content/sheet/workday_sheet.html'
        context = {
            'title': 'Рабочие дни'
        }
        context = U.get_prepared_data(context)
        if request.method == 'POST':
            day_id = request.POST.get('item_id')
            if day_id is not None and day_id != '':
                try:
                    _day = WorkDaySheet.objects.get(id=day_id)
                    _day.status = False if _day.status else True
                    _day.save(update_fields=['status'])
                except WorkDaySheet.DoesNotExist:
                    pass

        current_day = request.GET.get('current_day')
        if current_day is None or current_day == '':
            current_day = U.TODAY
        U.prepare_workday(current_day)

        workday = WorkDaySheet.objects.filter(Q(date__gte=current_day - U.timedelta(days=3)) &
                                              Q(date__lte=current_day + U.timedelta(days=14))).values()

        for day in workday:
            day['weekday'] = ASSETS.WEEKDAY[day['date'].weekday()]

        context['workday'] = workday
        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def driver_sheet_view(request):
    if request.user.is_authenticated:
        template = 'content/sheet/driver_sheet.html'
        context = {
            'title': 'Табель: водители'
        }

        if request.method == "POST":
            driver_sheet_id = request.POST.get('item_id')
            if driver_sheet_id is not None and driver_sheet_id != '':
                try:
                    _ds = DriverSheet.objects.get(id=driver_sheet_id)
                    _ds.status = False if _ds.status else True
                    _ds.save(update_fields=['status'])
                except DriverSheet.DoesNotExist:
                    pass
        if True:
            current_day = request.GET.get('current_day')
            if current_day is None or current_day == '':
                current_day = WorkDaySheet.objects.get(date=U.TODAY)
            else:
                current_day = WorkDaySheet.objects.get(date=current_day)
            context = U.get_prepared_data(context, current_day.date)
            if current_day.status:
                U.prepare_driver_sheet(current_day)
            driver_sheet = DriverSheet.objects.filter(isArchive=False, date=current_day).order_by('driver__last_name')
            context['driver_sheets'] = driver_sheet
            context['current_day'] = current_day

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def technic_sheet_view(request):
    if request.user.is_authenticated:
        template = 'content/sheet/technic_sheet.html'
        context = {'title': 'Табель: техника'}

        if request.method == 'POST':
            technic_sheet_id = request.POST.get('item_id')
            if technic_sheet_id is not None and technic_sheet_id != '':
                try:
                    _ts = TechnicSheet.objects.get(id=technic_sheet_id)
                    _ts.status = False if _ts.status else True
                    _ts.save(update_fields=['status'])
                except TechnicSheet.DoesNotExist:
                    pass

            technic_sheet_id = request.POST.get('technic_sheet_id')
            driver_sheet_id = request.POST.get('driver_sheet_id')
            if all((technic_sheet_id, driver_sheet_id)):
                try:
                    _ts = TechnicSheet.objects.get(id=technic_sheet_id)
                    _ds = DriverSheet.objects.get(id=driver_sheet_id)
                    _ts.driver_sheet = _ds
                    _ts.save(update_fields=['driver_sheet'])
                except (TechnicSheet.DoesNotExist, DriverSheet.DoesNotExist):
                    pass
        if True:
            current_day = request.GET.get('current_day')
            if current_day is None or current_day == '':
                current_day = WorkDaySheet.objects.get(date=U.TODAY)
            else:
                current_day = WorkDaySheet.objects.get(date=current_day)
            context['current_day'] = current_day
            context = U.get_prepared_data(context, current_day.date)
            if current_day.status:
                U.prepare_technic_sheet(current_day)
            technic_sheet = TechnicSheet.objects.filter(isArchive=False, date=current_day).order_by('technic__title')
            driver_sheet = DriverSheet.objects.filter(isArchive=False, date=current_day)
            context['technic_sheets'] = technic_sheet
            context['driver_sheets'] = driver_sheet
        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


#   --------------------------------------------------------------------------------------------------------------------


#   Technic-------------------------------------------------------------------------------------------------------------
def technic_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Техника'}
        technics = (Technic.objects.filter(isArchive=False).order_by('title')
                    .select_related('attached_driver'))
        context['technics'] = technics
        return render(request, 'content/technic/technics.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_technic_view(request):
    if request.user.is_authenticated:
        template = 'content/technic/edit_technic.html'
        context = {'title': 'Добавить технику'}

        technic_id = request.GET.get('tech_id')
        context['drivers'] = User.objects.filter(post=ASSETS.DRIVER)
        context['supervisors'] = dict(
            [(key, value) for key, value in ASSETS.USER_POSTS_dict.items() if key in (ASSETS.MECHANIC, ASSETS.SUPPLY)])
        technic_type_list = set(Technic.objects.filter().values_list('type', flat=True))
        context['technic_type_list'] = sorted(technic_type_list)

        if technic_id:
            try:
                technic = Technic.objects.get(pk=technic_id)
                context['technic'] = technic
                context['title'] = 'Редактировать технику'
            except Technic.DoesNotExist:
                log.error(f'Техники с id={technic_id} не существует')
                return HttpResponseRedirect(ENDPOINTS.TECHNICS)

        if request.method == 'POST':
            data = request.POST
            TECHNIC_FUNC.add_or_edit_technic(data, technic_id)
            return HttpResponseRedirect(ENDPOINTS.TECHNICS)
        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_technic_view(request):
    if request.user.is_authenticated:
        if U.is_administrator(request.user) or U.is_mechanic(request.user):
            technic_id = request.GET.get('tech_id')
            if technic_id:
                technic = TECHNIC_FUNC.delete_technic(technic_id)
                if technic:
                    _technic_sheet = TechnicSheet.objects.filter(technic=technic, date__date__gte=U.TODAY)
                    _application_technic = ApplicationTechnic.objects.filter(technic_sheet__in=_technic_sheet)
                    _application_today = ApplicationToday.objects.filter(date__date__gte=U.TODAY)
                    # _application_today = ApplicationToday.objects.filter(applicationtechnic__in=_application_technic)

                    _application_technic.delete()
                    _technic_sheet.delete()
                    for _app_today in _application_today:
                        U.check_application_today(_app_today)
                # try:
                #     technic = Technic.objects.get(pk=technic_id)
                #     technic.isArchive = True
                #     technic.save(update_fields=['isArchive'])
                #     _technic_sheet = TechnicSheet.objects.filter(technic=technic, date__date__gte=U.TODAY)
                #     _application_technic = ApplicationTechnic.objects.filter(technic_sheet__in=_technic_sheet)
                #     _application_today = ApplicationToday.objects.filter(date__date__gte=U.TODAY)
                #     # _application_today = ApplicationToday.objects.filter(applicationtechnic__in=_application_technic)
                #
                #     _application_technic.delete()
                #     _technic_sheet.delete()
                #     for _app_today in _application_today:
                #         U.check_application_today(_app_today)
                #     # technic.delete()
                # except Technic.DoesNotExist:
                #     return HttpResponseRedirect(ENDPOINTS.ERROR)
    return HttpResponseRedirect(ENDPOINTS.TECHNICS)


#   --------------------------------------------------------------------------------------------------------------------


#   User----------------------------------------------------------------------------------------------------------------
def users_view(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Все пользователи',
            'users_list': [],
            'user_post': ASSETS.USER_POSTS_dict
        }
        if U.is_administrator(request.user):
            users_list = User.objects.filter(isArchive=False,
                                             is_staff=False).order_by('last_name')
        elif U.is_mechanic(request.user):
            users_list = User.objects.filter(isArchive=False,
                                             is_staff=False,
                                             post=ASSETS.DRIVER).order_by('last_name')
        else:
            users_list = []
        context['users_list'] = users_list
        return render(request, 'content/users/users.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_user_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Добавить пользователя',
                   'posts': ASSETS.USER_POSTS_dict,
                   'foreman_list': User.objects.filter(post=ASSETS.FOREMAN)
                   }
        if U.is_mechanic(request.user):
            context['posts'] = {ASSETS.DRIVER: ASSETS.USER_POSTS_dict[ASSETS.DRIVER]}
        user_id = request.GET.get('user_id')
        if user_id:
            try:
                _user = User.objects.get(pk=user_id)
                context['user_list'] = _user
                context['title'] = 'Изменить пользователя'
            except User.DoesNotExist:
                log.error(f'Пользователя с id={user_id} не существует')
                return HttpResponseRedirect(ENDPOINTS.USERS)

        if request.method == 'POST':
            data = request.POST
            _user = USERS_FUNC.add_or_edit_user(data, user_id)
            return HttpResponseRedirect(ENDPOINTS.USERS)

        return render(request, 'content/users/edit_user.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_user_view(request):
    if request.user.is_authenticated:
        if request.user.post == ASSETS.ADMINISTRATOR:
            user_id = request.GET.get('user_id')
            if user_id:
                _user = USERS_FUNC.delete_user(user_id)
                if _user:
                    DriverSheet.objects.filter(driver=_user, date__date__gte=U.TODAY).delete()
    return HttpResponseRedirect(ENDPOINTS.USERS)


#   --------------------------------------------------------------------------------------------------------------------


def construction_site_view(request):
    if request.user.is_authenticated:
        template = 'content/construction_site/construction_sites.html'
        context = {
            'title': 'Строительные объекты'
        }
        if U.is_administrator(request.user):
            context['construction_sites'] = ConstructionSite.objects.filter(
                isArchive=False)
        if U.is_foreman(request.user):
            context['construction_sites'] = ConstructionSite.objects.filter(
                foreman=request.user, isArchive=False).exclude(
                address__in=(ASSETS.CS_SUPPLY_TITLE, ASSETS.CS_SPEC_TITLE))
        if U.is_master(request.user):
            context['construction_sites'] = ConstructionSite.objects.filter(
                foreman_id=request.user.supervisor_user_id, isArchive=False).exclude(
                address__in=(ASSETS.CS_SUPPLY_TITLE, ASSETS.CS_SPEC_TITLE))

        hide_constr_site_id = request.GET.get('hide')
        if hide_constr_site_id:
            CONSTR_SITE_FUNC.hide_construction_site(constr_site_id=hide_constr_site_id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        delete_constr_site_id = request.GET.get('delete')
        if delete_constr_site_id:
            CONSTR_SITE_FUNC.delete_construction_site(constr_site_id=delete_constr_site_id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_construction_sites(request):
    if request.user.is_authenticated:
        template = 'content/construction_site/edit_construction_site.html'
        context = {
            'title': 'Изменить объект',
            'foreman_list': User.objects.filter(isArchive=False, post=ASSETS.FOREMAN)
        }

        if request.method == 'POST':
            _id = request.POST.get('id')
            data = request.POST
            CONSTR_SITE_FUNC.create_or_edit_construction_site(data, _id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        constr_site_id = request.GET.get('id')
        if constr_site_id:
            context['constr_site'] = ConstructionSite.objects.get(id=constr_site_id)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def change_status_application_today(request):
    if request.user.is_authenticated:
        application_today_id = request.GET.get('application_today_id')
        current_day = request.GET.get('current_day')
        current_status = request.GET.get('current_status')

        if application_today_id:
            current_application_today = ApplicationToday.objects.get(id=application_today_id)
            if U.is_administrator(request.user):
                status_set = ASSETS.APPLICATION_STATUS_set
            elif U.is_foreman(request.user) or U.is_master(request.user) or U.is_supply(request.user):
                status_set = (ASSETS.ABSENT, ASSETS.SAVED)
            else:
                status_set = 'None'
            if current_application_today.status in status_set:
                up_status = U.get_nxt_status(current_application_today.status)
                current_application_today.status = up_status
                current_application_today.save()
                if up_status == ASSETS.SEND:
                    var_send, _ = Parameter.objects.get_or_create(
                        name=VAR.VAR_APPLICATION_SEND['name'],
                        title=VAR.VAR_APPLICATION_SEND['title'],
                        date=current_application_today.date.date)

                    var_send.time = U.NOW
                    var_send.flag = True
                    var_send.save(update_fields=['time', 'flag'])
                    U.send_application_for_all(current_application_today.date,
                                               application_today_id=current_application_today.id)

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        elif current_day and current_status:
            try:
                _c_day = WorkDaySheet.objects.get(date=current_day)
                application_today_list = ApplicationToday.objects.filter(isArchive=False, date=_c_day,
                                                                         status=current_status)

                up_status = U.get_nxt_status(current_status)
                application_today_list.update(status=up_status)
                if up_status == ASSETS.SEND:
                    var_send, _ = Parameter.objects.get_or_create(
                        name=VAR.VAR_APPLICATION_SEND['name'],
                        title=VAR.VAR_APPLICATION_SEND['title'],
                        date=_c_day.date)
                    var_send.time = U.NOW
                    var_send.flag = True
                    var_send.save(update_fields=['time', 'flag'])
                    U.send_application_for_all(_c_day)

                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except WorkDaySheet.DoesNotExist:
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def prepare_workday_for_app(request):
    if request.user.is_authenticated:
        _workday = request.GET.get('current_day')
        if _workday:
            workday = WorkDaySheet.objects.get(date=_workday)
            if not workday.status:
                workday.status = True
                workday.save(update_fields=['status'])
                U.prepare_driver_sheet(workday)
                U.prepare_technic_sheet(workday)
            return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={workday.date}')
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def conflicts_list_view(request):
    if request.user.is_authenticated:
        if U.is_administrator(request.user):
            template = 'content/spec/conflicts_list.html'
            context = {
                'title': 'Conflict List'
            }
            _current_day = request.GET.get('current_day')
            if _current_day is None or _current_day == '':
                current_day = WorkDaySheet.objects.get(date=U.TODAY)
            else:
                current_day = WorkDaySheet.objects.get(date=_current_day)
            context['current_day'] = current_day
            priority_id_list = U.get_priority_id_list(current_day)
            context['priority_id_list'] = priority_id_list
            conflict_technic_sheet = U.get_conflict_technic_sheet(
                U.get_busiest_technic_title(current_day),
                priority_id_list, get_id_list=False)
            if conflict_technic_sheet:
                for conflict_ts in conflict_technic_sheet:
                    conflict_ts['total_count_apps'] = ApplicationTechnic.objects.filter(
                        isChecked=False,
                        technic_sheet_id__in=conflict_ts['id_list'],
                        priority=1).values_list('priority', flat=True).count()
                context['conflict_technic_sheet'] = conflict_technic_sheet
                return render(request, template, context)
            else:
                return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day.date}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def conflict_resolution_view(request):
    if request.user.is_authenticated:
        if U.is_administrator(request.user):
            template = 'content/spec/conflict_resolution.html'
            context = {
                'title': 'Conflict Resolution'
            }

            conflict_list_id = request.GET.get('conflict_list_id')
            conflict_list_id = conflict_list_id.strip('[]').split(', ')

            _current_day = request.GET.get('current_day')
            if _current_day is None or _current_day == '':
                current_day = WorkDaySheet.objects.get(date=U.TODAY)
            else:
                current_day = WorkDaySheet.objects.get(date=_current_day)
            context['current_day'] = current_day

            if request.method == 'POST':
                app_technic_id = request.POST.get('app_technic_id')
                app_technic_priority = request.POST.get('app_technic_priority')

                technic_title_short = request.POST.get('technic_title_short')
                technic_sheet_id = request.POST.get('technic_sheet_id')
                technic_description = request.POST.get('technic_description')

                if all((app_technic_id, app_technic_priority)):
                    app_technic = ApplicationTechnic.objects.get(id=app_technic_id)
                    app_technic.priority = app_technic_priority
                    app_technic.save(update_fields=['priority'])

                if all((technic_sheet_id, app_technic_id)):
                    app_technic = ApplicationTechnic.objects.get(id=app_technic_id)

                    if technic_sheet_id is None or technic_sheet_id == '':
                        n_technic_titles = U.get_short_technic_name(technic_title_short, current_day)
                        some_technic_sheet = U.get_some_technic_sheet(n_technic_titles, current_day)
                    else:
                        some_technic_sheet = TechnicSheet.objects.get(id=technic_sheet_id)

                    _old_ts = app_technic.technic_sheet
                    _old_ts.decrement_count_application()
                    _old_ts.save()

                    some_technic_sheet.increment_count_application()
                    some_technic_sheet.save()

                    app_technic.technic_sheet = some_technic_sheet

                    if technic_description:
                        app_technic.description = technic_description
                    app_technic.save()

            if conflict_list_id is not None and len(conflict_list_id) > 0:
                applications_technic = ApplicationTechnic.objects.filter(technic_sheet__in=conflict_list_id,
                                                                         isChecked=False,
                                                                         isArchive=False)
                context['applications_technic'] = applications_technic

                color_list = U.set_color_for_list(conflict_list_id)
                context['color_list'] = color_list

                technic_title = applications_technic.values_list(
                    'technic_sheet__technic__title', flat=True).first()
                context['technic_title'] = technic_title

                technic_sheets = TechnicSheet.objects.filter(isArchive=False,
                                                             status=True,
                                                             driver_sheet__isnull=False,
                                                             date=current_day)
                technic_titles_dict = U.get_short_technic_name_dict(current_day)
                context['technic_titles_dict'] = technic_titles_dict

                technic_driver_list = []
                for title_short, title in technic_titles_dict.items():
                    technic_driver_list.append({
                        'title_short': title_short,
                        'title': title,
                        'technic_sheets': technic_sheets.filter(technic__title=title)
                    })
                context['technic_driver_list'] = technic_driver_list

                priority_id_list = U.get_priority_id_list(current_day)
                context['priority_id_list'] = priority_id_list

                conflict_technic_sheet = U.get_conflict_technic_sheet(
                    U.get_busiest_technic_title(current_day),
                    priority_id_list, get_id_list=False)

                if conflict_technic_sheet:
                    print(conflict_technic_sheet)

                    conflict_ts = list(filter(lambda item: item['technic_title'] == technic_title,
                                                      conflict_technic_sheet))
                    if conflict_ts:
                        conflict_ts = conflict_ts[0]
                        conflict_ts['total_count_apps'] = ApplicationTechnic.objects.filter(
                            isChecked=False,
                            technic_sheet_id__in=conflict_ts['id_list'],
                            priority=1).values_list('priority', flat=True).count()
                        context['conflict_technic_sheet'] = conflict_ts
                    else:
                        return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')
                else:
                    return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')
            return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_technic_application(request):
    if request.user.is_authenticated:
        if U.is_administrator(request.user):
            template = 'content/applications_list/technic_application_list_for_admin.html'
        else:
            template = 'content/applications_list/technic_application_list.html'
        context = {
            'title': 'Заявки на технику'
        }
        _current_day = request.GET.get('current_day')
        if _current_day is None or _current_day == '':
            current_day = WorkDaySheet.objects.get(date=U.TODAY)
        else:
            current_day = WorkDaySheet.objects.get(date=_current_day)
        context = U.get_prepared_data(context, current_day.date)
        context = U.get_prepare_filter(context)
        context['current_day'] = current_day

        if request.method == 'POST':
            print(request.POST)
            U.set_prepare_filter(request)
            app_technic_id_list = request.POST.getlist('app_technic_id')
            app_technic_priority = request.POST.getlist('app_technic_priority')
            app_technic_description = request.POST.getlist('app_technic_description')

            for _id, _priority, _description in zip(app_technic_id_list, app_technic_priority, app_technic_description):
                ApplicationTechnic.objects.filter(id=_id).update(
                    priority=_priority,
                    description=_description)

        application_technic_list = ApplicationTechnic.objects.filter(application_today__date=current_day,
                                                                     isArchive=False,
                                                                     is_cancelled=False,
                                                                     isChecked=False)
        if not U.is_administrator(request.user):
            application_technic_list = application_technic_list.filter(application_today__status=ASSETS.SEND)

        if request.user.filter_technic:
            application_technic_list = application_technic_list.filter(
                technic_sheet__technic__title=request.user.filter_technic)
        if request.user.filter_foreman != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site__foreman_id=request.user.filter_foreman)
        if request.user.filter_construction_site != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site_id=request.user.filter_construction_site)



        technic_sheet_list = application_technic_list.values('technic_sheet').distinct()

        if request.user.sort_by == 'technic':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__technic__title')
        elif request.user.sort_by == 'driver':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__driver_sheet__driver__last_name')

        application_technics = []
        for technic_sheet in technic_sheet_list:
            application_technics.append({
                'technic_sheet': TechnicSheet.objects.get(id=technic_sheet['technic_sheet']),
                'applications_list': application_technic_list.filter(
                    technic_sheet_id=technic_sheet['technic_sheet']).order_by('priority')
            })

        context['application_technics'] = application_technics
        context['priority_id_list'] = U.get_priority_id_list(current_day)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_material_application(request):
    if request.user.is_authenticated:
        template = 'content/applications_list/material_application_list.html'
        context = {
            'title': 'Materials Applications'
        }
        _current_day = request.GET.get('current_day')
        if _current_day is None or _current_day == '':
            current_day = WorkDaySheet.objects.get(date=U.TODAY)
        else:
            current_day = WorkDaySheet.objects.get(date=_current_day)
        context = U.get_prepared_data(context, current_day.date)
        context = U.get_prepare_filter(context)
        context['current_day'] = current_day

        application_materials_list = ApplicationMaterial.objects.filter(
            isArchive=False, application_today__date=current_day).exclude(application_today__status=ASSETS.SAVED)
        context['application_materials_list'] = application_materials_list

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def material_application_supply_view(request):
    if request.user.is_authenticated:
        template = 'content/applications_list/material_application_list_for_supply.html'
        context = {
            'title': 'Materials Applications'
        }
        _current_day = request.GET.get('current_day')
        _is_print = request.GET.get('print')
        if _current_day is None or _current_day == '':
            current_day = WorkDaySheet.objects.get(date=U.TODAY)
        else:
            current_day = WorkDaySheet.objects.get(date=_current_day)
        context = U.get_prepared_data(context, current_day.date)
        context['current_day'] = current_day

        if _is_print:
            template = 'content/spec/print_material_application.html'
            application_materials_list = ApplicationMaterial.objects.filter(isArchive=False,
                                                                            application_today__date=current_day,
                                                                            isChecked=True)
            context['application_materials_list'] = application_materials_list
            context['weekday'] = ASSETS.WEEKDAY[current_day.date.weekday()]
            return render(request, template, context)

        if request.method == 'POST':
            application_material_id = request.POST.get('application_material_id')
            application_material_description = request.POST.get('application_material_description')
            if application_material_id is not None and application_material_id != '':
                try:
                    _application_material = ApplicationMaterial.objects.get(id=application_material_id)
                except ApplicationMaterial.DoesNotExist:
                    return HttpResponseRedirect(ENDPOINTS.ERROR)
                if application_material_description != _application_material.description or not _application_material.isChecked:
                    _application_material.description = application_material_description
                    _application_material.isChecked = True
                    _application_material.save()
                else:
                    _application_material.isChecked = False
                    _application_material.save()

        application_materials_list = ApplicationMaterial.objects.filter(isArchive=False,
                                                                        application_today__date=current_day)
        context['application_materials_list'] = application_materials_list

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def profile_view(request):
    if request.user.is_authenticated:
        template = 'content/profile.html'
        context = {}

        user_id = request.GET.get('user_id')
        if user_id is not None and user_id != '':
            current_user = User.objects.get(pk=user_id)
        else:
            current_user = User.objects.get(pk=request.user.id)

        current_user_key = U.get_user_key(current_user.id)
        context['user_key'] = current_user_key

        if request.method == 'POST':
            _user_key = request.POST.get('user_key')
            if _user_key is not None and _user_key != '':
                _chat_id = U.T.get_id_chat(key=_user_key, result=U.T.get_result())
                if _chat_id:
                    current_user.telegram_id_chat = _chat_id
                    current_user.save()
                    U.send_messages(chat_id=_chat_id,
                                    messages='Связь установлена')

        context['current_user'] = current_user
        return render(request, template, context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def def_test(request):  # TODO: def TEST
    _current_day = request.GET.get('current_day')
    if _current_day:
        current_day = WorkDaySheet.objects.get(date=_current_day)
    else:
        current_day = WorkDaySheet.objects.get(date=U.TODAY)
    work_days = U.get_work_days().values()
    for work_day in work_days:
        work_day['weekday'] = ASSETS.WEEKDAY[work_day['date'].weekday()][:3]
    template = 'content/tests/change_workday.html'
    context = {
        'title': 'Test',
        'today': U.TODAY,
        'current_day': current_day,
        'work_days': work_days,
        # 'weekday': ASSETS.WEEKDAY
    }

    # U.send_application_for_driver(current_day)
    # U.send_application_for_foreman(current_day)
    U.send_application_for_admin(current_day)

    return render(request, template, context)


def maintenance_view(request):
    template = 'content/spec/maintenance.html'
    context = {}
    return render(request, template, context)


def settings_view(request):
    if request.user.is_authenticated:
        template = 'content/spec/settings.html'
        context = {
            'title': 'Settings',
        }

        rez = U.prepare_variables()
        print(rez)

        return render(request, template, context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)
