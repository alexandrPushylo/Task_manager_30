"""
URL configuration for Task_manager_30 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import dashboard
from dashboard.views import login_view, logout_view, register_view

from dashboard.views import workday_sheet_view, driver_sheet_view, technic_sheet_view

from dashboard.views import technic_view, edit_technic_view, delete_technic
from dashboard.views import users_view, edit_user_view, delete_user

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),

    path('work_day/', workday_sheet_view, name='work_day'),
    path('driver_sheet/', driver_sheet_view, name='driver_sheet'),
    path('technic_sheet/', technic_sheet_view, name='technic_sheet'),

    path('users/', users_view, name='users'),
    path('edit_user/', edit_user_view, name='edit_user'),
    path('delete_user/', delete_user, name='delete_user'),

    path('technics/', technic_view, name='technics'),
    path('edit_technic/', edit_technic_view, name='edit_technic'),
    path('delete_technic/', delete_technic, name='delete_technic'),

    path('construction_site/', construction_site_view, name='construction_site'),
    path('edit_construction_sites/', edit_construction_sites, name='edit_construction_sites'),

    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
