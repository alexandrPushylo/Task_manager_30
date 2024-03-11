from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q

from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import Technic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter, Telebot

from dashboard.assets import USER_POSTS, ERROR_MESSAGES

from dashboard.utilities import TODAY, WEEKDAY
from dashboard.utilities import add_user, prepare_workday
from dashboard.utilities import isAdministrator, isForeman, isMaster, isMechanic, isSupply, isEmployee, isDriver


# Create your views here.


def dashboard(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/login/')

    context = {
        'post': request.user
    }

    if isAdministrator(request.user):
        return render(request, 'content/dashboard/admin_dashboard.html', context)
    elif isForeman(request.user):
        return render(request, 'content/dashboard/foreman_dashboard.html', context)
    elif isMaster(request.user):
        return render(request, 'content/dashboard/foreman_dashboard.html', context)
    elif isMechanic(request.user):
        return render(request, '', context)
    elif isSupply(request.user):
        return render(request, '', context)
    elif isEmployee(request.user):
        return render(request, '', context)
    elif isDriver(request.user):
        return render(request, '', context)
    else:
        return HttpResponse(status=404)


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/dashboard/')
    if request.method == 'GET':
        return render(request, 'content/login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/dashboard/')  # TODO: redirect to Home page
        else:
            return render(request, 'content/login.html', {'error': ERROR_MESSAGES['login']})
    return HttpResponse(status=403)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect('/login/')


def register_view(request):
    template = 'content/register.html'
    context = {
        'user_posts': USER_POSTS,
        'foreman_list': Foreman.objects.filter().values('id', 'user__last_name', 'user__first_name')
    }

    if request.method == 'GET':
        return render(request, template, context)
    if request.method == 'POST':
        data = request.POST
        new_user = add_user(data)
        if new_user is not None and request.user.is_anonymous:
            login(request, new_user)
            return HttpResponseRedirect('/dashboard/')  # TODO: redirect to Home page
        elif new_user is not None and request.user.is_authenticated:
            return HttpResponseRedirect('/')  # TODO redirect if create new user
        else:
            context['error'] = ERROR_MESSAGES['register']
            return render(request, template, context)

    return HttpResponse(status=403)


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
            day['weekday'] = WEEKDAY[day['date'].weekday()]

        context['workday'] = workday



            # status = request.POST.get('status')
            # print(id_day)
        return render(request, template, context)

    return HttpResponseRedirect('/login/')
