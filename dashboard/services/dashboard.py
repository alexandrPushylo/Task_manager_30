from dashboard.models import WorkDaySheet, ConstructionSite, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial, User
from logger import getLogger
import dashboard.utilities as U
import dashboard.assets as ASSETS

import dashboard.services.user as USERS_SERVICE
import dashboard.services.technic as TECHNIC_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE

import dashboard.services.application_today as APP_TODAY_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE


log = getLogger(__name__)


def get_dashboard_for_admin(request, current_day: WorkDaySheet, context: dict) -> dict:
    VIEW_MODE = context.get('VIEW_MODE')
    if request.POST.get('operation') == 'set_spec_task':
        technic_sheet_id = request.POST.get('technic_sheet_id')
        if technic_sheet_id:
            U.set_spec_task(technic_sheet_id)

    if request.POST.get('operation') == 'toggle_panel':
        _hide_panel = 'change'
        if _hide_panel:
            _user = USERS_SERVICE.get_user(pk=request.user.id)
            _user.is_show_panel = False if _user.is_show_panel else True
            _user.save(update_fields=['is_show_panel'])

    if VIEW_MODE == ASSETS.VIEW_MODE_ARCHIVE:
        construction_sites = CONSTR_SITE_SERVICE.get_construction_site_queryset(
            applicationtoday__date=current_day
        )
    else:
        construction_sites = CONSTR_SITE_SERVICE.get_construction_site_queryset(
            isArchive=False,
            status=True
        )

    if not request.user.is_show_absent_app:
        construction_sites = construction_sites.filter(applicationtoday__date=current_day)
    if not request.user.is_show_saved_app:
        construction_sites = construction_sites.exclude(applicationtoday__status=ASSETS.SAVED)

    applications_today = APP_TODAY_SERVICE.get_apps_today_queryset(
        order_by=('status',),
        isArchive=False,
        date=current_day,
        construction_site__in=construction_sites
    )

    if request.user.is_show_technic_app:
        applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
            isArchive=False,
            application_today__in=applications_today)
    else:
        applications_technic = ApplicationTechnic.objects.none()

    if request.user.is_show_material_app:
        application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
            isArchive=False,
            application_today__in=applications_today)
    else:
        application_material = ApplicationMaterial.objects.none()

    context['table_working_technic_sheet'] = U.get_table_working_technic_sheet(current_day)
    context['applications_today_list'] = applications_today
    context['construction_sites'] = construction_sites.values()

    for construction_site in context['construction_sites']:
        foreman_id = construction_site.get('foreman_id')
        construction_site['foreman'] = USERS_SERVICE.get_user(pk=foreman_id) if foreman_id else None

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

    technic_sheet_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        date=current_day,
        driver_sheet__isnull=False,
        status=True,
        isArchive=False
    )

    priority_id_list = U.get_priority_id_list(technic_sheet=technic_sheet_list)
    context['priority_id_list'] = priority_id_list

    busiest_technic_title_list = U.get_busiest_technic_title(technic_sheet_list)
    conflict_technic_sheet = U.get_conflict_list_of_technic_sheet(
        busiest_technic_title=busiest_technic_title_list,
        priority_id_list=priority_id_list,
        get_only_id_list=True
    )
    context['conflict_technic_sheet'] = conflict_technic_sheet

    return context


def get_dashboard_for_foreman_or_master(request, foreman: User, current_day: WorkDaySheet, context: dict) -> dict:
    VIEW_MODE = context.get('VIEW_MODE')

    if VIEW_MODE == ASSETS.VIEW_MODE_ARCHIVE:
        construction_sites = CONSTR_SITE_SERVICE.get_construction_site_queryset(
            foreman=foreman, applicationtoday__date=current_day)
    else:
        construction_sites = CONSTR_SITE_SERVICE.get_construction_site_queryset(
            foreman=foreman, isArchive=False, status=True)

    if not request.user.is_show_absent_app:
        construction_sites = construction_sites.filter(applicationtoday__date=current_day)
    if not request.user.is_show_saved_app:
        construction_sites = construction_sites.exclude(applicationtoday__status=ASSETS.SAVED)

    applications_today = APP_TODAY_SERVICE.get_apps_today_queryset(
        order_by=('status',),
        isArchive=False,
        date=current_day,
        construction_site__in=construction_sites
    )

    if request.user.is_show_technic_app:
        applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
            isArchive=False,
            application_today__in=applications_today)
    else:
        applications_technic = ApplicationTechnic.objects.none()

    if request.user.is_show_material_app:
        application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
            isArchive=False,
            application_today__in=applications_today)
    else:
        application_material = ApplicationMaterial.objects.none()

    context['applications_today_list'] = applications_today
    context['construction_sites'] = construction_sites.values()

    for construction_site in context['construction_sites']:
        construction_site['foreman'] = foreman

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
    return context


def get_dashboard_for_mechanic(request, current_day: WorkDaySheet, context: dict) -> dict:
    technic_sheet_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        select_related=('technic__attached_driver', 'driver_sheet__driver'),
        date=current_day, isArchive=False)

    context['technic_sheet_list'] = technic_sheet_list

    application_technic_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        select_related=('application_today__construction_site__foreman',),
        application_today__date=current_day,
        application_today__status=ASSETS.SEND,
        isArchive=False,
        is_cancelled=False)
    applications_technic = []
    for technic_sheet in technic_sheet_list:
        applications_technic.append({
            'technic_sheet_id': technic_sheet.id,
            'applications': application_technic_list.filter(technic_sheet=technic_sheet)
            .values(
                'application_today__construction_site__address',
                'application_today__construction_site__foreman__last_name',
                'description')
            .order_by('priority')
        })
    context['applications_technic'] = applications_technic

    return context


def get_dashboard_for_supply(request, current_day: WorkDaySheet, context: dict) -> dict:
    construction_site, _created = ConstructionSite.objects.get_or_create(address=ASSETS.CS_SUPPLY_TITLE)
    application_today = APP_TODAY_SERVICE.get_apps_today(
        date=current_day,
        construction_site=construction_site,
        isArchive=False)

    if request.method == 'POST':
        application_technic_id = request.POST.get('applicationTechnicId')
        operation = request.POST.get('operation')
        application_today_id = request.POST.get('application_today_id')

        #   Отвергнуть заявку
        if application_technic_id and operation == 'reject':
            APP_TECHNIC_SERVICE.toggle_reject_apps_technic(app_tech_id=application_technic_id)

        elif application_technic_id and operation == 'accept':
            if not application_today_id:
                _application_today = ApplicationToday.objects.create(date=current_day,
                                                                     construction_site=construction_site,
                                                                     status=ASSETS.SAVED)
                application_today_id = _application_today.id
            U.accept_app_tech_to_supply(application_technic_id, application_today_id)

    count_not_checked_app_mater = APP_MATERIAL_SERVICE.get_apps_material_queryset(
        isArchive=False,
        application_today__date=current_day,
        isChecked=False
    ).count()
    if count_not_checked_app_mater > 0:
        context['count_not_checked_app_mater'] = count_not_checked_app_mater

    applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        isArchive=False,
        application_today=application_today
    )
    applications_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
        isArchive=False,
        application_today=application_today
    )
    supply_technic_list = TECHNIC_SERVICE.get_technics_queryset(
        isArchive=False,
        supervisor_technic=ASSETS.SUPPLY)

    applications_technic_for_supply = []
    _app_tech = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        select_related=('application_today__construction_site',),
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

    return context


def get_dashboard_for_employee(request, current_day: WorkDaySheet, context: dict) -> dict:
    applications_today = APP_TODAY_SERVICE.get_apps_today_queryset(
        order_by=('status',),
        isArchive=False,
        status=ASSETS.SEND,
        date=current_day
    )
    construction_sites = CONSTR_SITE_SERVICE.get_construction_site_queryset(
        isArchive=False,
        status=True,
        applicationtoday__in=applications_today
    )

    if request.user.is_show_technic_app:
        applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
            isArchive=False,
            application_today__in=applications_today,
            isChecked=False,
            is_cancelled=False
        )
    else:
        applications_technic = ApplicationTechnic.objects.none()
    if request.user.is_show_material_app:
        application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
            isArchive=False,
            application_today__in=applications_today
        )
    else:
        application_material = ApplicationMaterial.objects.none()

    context['construction_sites'] = construction_sites.values()
    for construction_site in context['construction_sites']:
        construction_site['foreman'] = USERS_SERVICE.get_user(pk=construction_site['foreman_id'])

        construction_site['application_today'] = APP_TODAY_SERVICE.get_apps_today_queryset(
            construction_site_id=construction_site['id']
        ).values().first()

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
                'description'
            )
    return context


def get_dashboard_for_driver(request, current_day: WorkDaySheet, context: dict) -> dict:
    current_driver = request.user

    current_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        select_related=('driver_sheet__driver', 'technic'),
        driver_sheet__driver=current_driver,
        isArchive=False,
        status=True,
        date=current_day
    )
    applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        select_related=('application_today__construction_site__foreman', ),
        isArchive=False,
        isChecked=False,
        is_cancelled=False,
        application_today__date=current_day,
        application_today__status=ASSETS.SEND
    )

    technic_application_list = []
    for tech_sheet in current_technic_sheet:
        technic_application_list.append({
            'technic_sheet': tech_sheet,
            'applications_technic': applications_technic.filter(technic_sheet=tech_sheet).order_by('priority')
        })
    context['technic_application_list'] = technic_application_list
    return context

