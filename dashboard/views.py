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
# from dashboard.models import Parameter#, Telebot

# from dashboard.assets import USER_POSTS_set, ERROR_MESSAGES
import dashboard.assets as ASSETS
import Task_manager_30.endpoints as ENDPOINTS

from dashboard.utilities import TODAY
from dashboard.utilities import add_user, prepare_workday, prepare_driver_sheet
from dashboard.utilities import is_administrator, is_foreman, is_master, is_driver, is_mechanic, is_supply, is_employee


# Create your views here.


def dashboard(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)

    context = {
        'post': request.user
    }

    if is_administrator(request.user):
        return render(request, 'content/dashboard/admin_dashboard.html', context)
    elif is_foreman(request.user):
        return render(request, 'content/dashboard/foreman_dashboard.html', context)
    elif is_master(request.user):
        return render(request, 'content/dashboard/foreman_dashboard.html', context)
    elif is_mechanic(request.user):
        return render(request, '', context)
    elif is_supply(request.user):
        return render(request, '', context)
    elif is_employee(request.user):
        return render(request, '', context)
    elif is_driver(request.user):
        return render(request, '', context)
    else:
        return HttpResponse(status=404)


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    if request.method == 'GET':
        return render(request, 'content/login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)  # TODO: redirect to Home page
        else:
            return render(request, 'content/login.html', {'error': ASSETS.ERROR_MESSAGES['login']})
    return HttpResponse(status=403)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def register_view(request):
    template = 'content/register.html'
    context = {
        'user_posts': ASSETS.USER_POSTS_dict,
        'foreman_list': User.objects.filter(post=ASSETS.FOREMAN)
    }

    if request.method == 'GET':
        return render(request, template, context)
    if request.method == 'POST':
        data = request.POST
        new_user = add_user(data)
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
        # if request.method == 'GET':
        if request.method == 'POST':
            id_day_list = request.POST.getlist('id')
            for id_day in id_day_list:
                _status = request.POST.get(f"status_{id_day}")
                workday = WorkDaySheet.objects.get(id=id_day)
                if _status is None:
                    workday.status = False
                else:
                    workday.status = True
                workday.save(update_fields=['status'])
        current_day = request.GET.get('date')
        if current_day is None:
            current_day = TODAY
        prepare_workday(current_day)
        workday = WorkDaySheet.objects.filter(date__gte=current_day).values()
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
            driver_sheet_id_list = request.POST.getlist('id')
            for driver_sheet_id in driver_sheet_id_list:
                _status = request.POST.get(f'status_{driver_sheet_id}')
                driver_sheet = DriverSheet.objects.get(id=driver_sheet_id)
                if _status is None:
                    driver_sheet.status = False
                else:
                    driver_sheet.status = True
                driver_sheet.save(update_fields=['status'])

        if True:
            current_day = request.GET.get('date')
            if current_day is None:
                current_day = TODAY
            workday = WorkDaySheet.objects.get(date=current_day)
            if workday.status or True:  #   TODO:#########################
                prepare_driver_sheet(workday)
            driver_sheet = DriverSheet.objects.filter(isArchive=False, date=workday).order_by('driver__last_name')
            context['driver_sheets'] = driver_sheet

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)
#   --------------------------------------------------------------------------------------------------------------------


#   Technic-------------------------------------------------------------------------------------------------------------
def technic_view(request):
    if request.user.is_authenticated:
        template = 'content/technic/technics.html'
        context = {'title': 'Техника'}
        technics = Technic.objects.filter(isArchive=False).order_by('title')
        context['technics'] = technics
        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_technic_view(request):
    if request.user.is_authenticated:
        template = 'content/technic/edit_technic.html'
        context = {'title': 'Добавить технику'}

        technic_id = request.GET.get('tech_id')
        context['drivers'] = User.objects.filter(post=ASSETS.DRIVER)
        context['supervisors'] = dict(
            [(key, value) for key, value in ASSETS.USER_POSTS_dict.items() if key in (ASSETS.MECHANIC, ASSETS.SUPPLY)])

        if technic_id is not None:
            technic = Technic.objects.get(pk=technic_id)
            context['technic'] = technic
            context['title'] = 'Редактировать технику'

        if request.method == 'POST':
            _title = request.POST.get('title')
            _type = request.POST.get('type')
            _attached_driver = request.POST.get('attached_driver')
            _supervisor = request.POST.get('supervisor')
            _id_information = request.POST.get('id_information')
            _description = request.POST.get('description')

            if all([_title, _type, _id_information]):
                if technic_id is None:
                    Technic.objects.create(
                        title=_title,
                        type=_type,
                        id_information=_id_information,
                        attached_driver=User.objects.get(pk=_attached_driver) if _attached_driver else None,
                        supervisor_technic=_supervisor,
                        description=_description
                    )
                else:
                    try:
                        technic = Technic.objects.get(pk=technic_id)
                        technic.title = _title
                        technic.type = _type
                        technic.id_information = _id_information
                        technic.attached_driver = User.objects.get(pk=_attached_driver) if _attached_driver else None
                        technic.supervisor_technic = _supervisor
                        technic.description = _description
                        technic.save()
                    except Technic.DoesNotExist:
                        return HttpResponseRedirect(ENDPOINTS.ERROR)
                return HttpResponseRedirect(ENDPOINTS.TECHNICS)
        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_technic(request):
    if request.user.is_authenticated:
        if is_administrator(request.user) or is_mechanic(request.user):
            technic_id = request.GET.get('tech_id')
            if technic_id:
                try:
                    technic = Technic.objects.get(pk=technic_id)
                    technic.delete()
                except Technic.DoesNotExist:
                    return HttpResponseRedirect(ENDPOINTS.ERROR)
    return HttpResponseRedirect(ENDPOINTS.TECHNICS)
#   --------------------------------------------------------------------------------------------------------------------


#   User----------------------------------------------------------------------------------------------------------------
def users_view(request):
    if request.user.is_authenticated:
        template = 'content/users/users.html'
        context = {
            'title': 'Все пользователи',
            'users_list': [],
            'user_post': ASSETS.USER_POSTS_dict
        }

        users_list = User.objects.filter(isArchive=False, is_staff=False).order_by('last_name')
        context['users_list'] = users_list
        return render(request, template, context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_user_view(request):
    if request.user.is_authenticated:
        template = 'content/users/edit_user.html'
        context = {'title': 'Добавить пользователя',
                   'posts': ASSETS.USER_POSTS_dict,
                   'foreman_list': User.objects.filter(post=ASSETS.FOREMAN)
                   }
        user_id = request.GET.get('user_id')
        if user_id is not None:
            _user = User.objects.get(pk=user_id)
            context['user_list'] = _user
            context['title'] = 'Изменить пользователя'

            if request.method == 'POST':
                data = request.POST
                _user = add_user(data, user_id=user_id)
                return HttpResponseRedirect(ENDPOINTS.USERS)
        else:
            if request.method == 'POST':
                data = request.POST
                _user = add_user(data)
                return HttpResponseRedirect(ENDPOINTS.USERS)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_user(request):
    if request.user.is_authenticated:
        if request.user.post == ASSETS.ADMINISTRATOR:
            user_id = request.GET.get('user_id')
            if user_id:
                try:
                    _user = User.objects.get(pk=user_id)
                    _user.delete()
                except User.DoesNotExist:
                    return HttpResponseRedirect(ENDPOINTS.ERROR)
    return HttpResponseRedirect(ENDPOINTS.USERS)
#   --------------------------------------------------------------------------------------------------------------------


def construction_site_view(request):
    if request.user.is_authenticated:
        template = 'content/construction_site/construction_sites.html'
        context = {
            'title': 'Строительные объекты',
            'construction_sites': ConstructionSite.objects.filter(isArchive=False)}
        hide_constr_site_id = request.GET.get('hide')
        constr_id = request.GET.get('delete')
        if hide_constr_site_id:
            constr_site = ConstructionSite.objects.get(id=hide_constr_site_id)
            constr_site.status = False if constr_site.status else True
            constr_site.save(update_fields=['status'])
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)
        elif constr_id:
            constr_site = ConstructionSite.objects.get(id=constr_id)
            constr_site.isArchive = False if constr_site.isArchive else True
            constr_site.save(update_fields=['isArchive'])
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
            _address = request.POST.get('address')
            _foreman = request.POST.get('foreman')
            foreman = User.objects.get(id=_foreman) if _foreman is not None and _foreman != '' else None
            if all([_id, _address]):
                constr_site = ConstructionSite.objects.get(id=_id)
                constr_site.address = _address
                constr_site.foreman = foreman
                constr_site.save()
                return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)
            elif _address is not None:
                ConstructionSite.objects.create(
                    address=_address,
                    foreman=foreman
                )
                return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        constr_site_id = request.GET.get('id')
        if constr_site_id:
            context['constr_site'] = ConstructionSite.objects.get(id=constr_site_id)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)
