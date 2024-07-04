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
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from config.settings import TECH_SUPPORT_MODE
# from dashboard.views import dashboard, edit_application_view
# from dashboard.views import clear_application_today
from dashboard.views import conflicts_list_view, conflict_resolution_view
from dashboard.views import login_view, logout_view, register_view, restore_password_view
from dashboard.views import show_technic_application, show_material_application, material_application_supply_view

# from dashboard.views import workday_sheet_view, driver_sheet_view, technic_sheet_view

from dashboard.views import construction_site_view, edit_construction_sites
from dashboard.views import technic_view, edit_technic_view, delete_technic_view
from dashboard.views import users_view, edit_user_view, delete_user_view, profile_view

from dashboard.views import change_status_application_today, change_weekend_to_workday, validate_application_today_view
from dashboard.views import settings_view
from dashboard.views import maintenance_view
from dashboard.views import def_test

urlpatterns = [
                  path('', include('dashboard.urls')),
                  # path('dashboard/', dashboard, name='dashboard'),
                  # path('edit_application/', edit_application_view, name='edit_application'),
                  # path('clear_application/', clear_application_today, name='clear_application'),

                  path('conflicts_list/', conflicts_list_view, name='conflicts_list'),
                  path('conflict_resolution/', conflict_resolution_view, name='conflict_resolution'),

                  path('technic_application_list/', show_technic_application, name='technic_application_list'),
                  path('material_application_list/', show_material_application, name='material_application_list'),
                  path('material_application_supply/', material_application_supply_view,
                       name='material_application_supply'),

                  # path('work_days/', workday_sheet_view, name='work_days'),
                  # path('driver_sheet/', driver_sheet_view, name='driver_sheet'),
                  # path('technic_sheet/', technic_sheet_view, name='technic_sheet'),

                  path('users/', users_view, name='users'),
                  path('edit_user/', edit_user_view, name='edit_user'),
                  path('delete_user/', delete_user_view, name='delete_user'),
                  path('profile/', profile_view, name='profile'),

                  path('technics/', technic_view, name='technics'),
                  path('edit_technic/', edit_technic_view, name='edit_technic'),
                  path('delete_technic/', delete_technic_view, name='delete_technic'),

                  path('construction_site/', construction_site_view, name='construction_site'),
                  path('edit_construction_sites/', edit_construction_sites, name='edit_construction_sites'),

                  path('admin/', admin.site.urls),
                  path('login/', login_view, name='login'),
                  path('logout/', logout_view, name='logout'),
                  path('register/', register_view, name='register'),
                  path('restore_pwd/', restore_password_view, name='restore_password'),
                  path('settings/', settings_view, name='settings'),

                  path('change_app_status/', change_status_application_today, name='change_app_status'),
                  path('pr_wd_f_app/', change_weekend_to_workday, name='prepare_workday_for_app'),
                  # path('ck_app_stat/', check_application_status, name='check_application_status'),
                  path('validate_app_today', validate_application_today_view, name='validate_application_today'),
                  path('test/', def_test, name='test'),

                  # re_path(r'^.*', maintenance_view),
                  # re_path(r'^.*', dashboard)

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if TECH_SUPPORT_MODE:
    urlpatterns = [re_path(r'^.*', maintenance_view)] + urlpatterns
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
