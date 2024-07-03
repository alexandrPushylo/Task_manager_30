from django.urls import path, re_path, include
import dashboard.views as V

urlpatterns = [
    path('', V.dashboard_view, name='dashboard'),
    path('dashboard/', V.dashboard_view, name='dashboard'),
    path('edit_application/', V.edit_application_view, name='edit_application'),
    path('clear_application/', V.clear_application_today, name='clear_application'),

    path('work_days/', V.workday_sheet_view, name='work_days'),
    path('driver_sheet/', V.driver_sheet_view, name='driver_sheet'),
    path('technic_sheet/', V.technic_sheet_view, name='technic_sheet'),
]
