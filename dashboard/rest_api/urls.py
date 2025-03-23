from django.urls import path, re_path, include
# from .api import get_users, get_user_details, get_user_posts, get_foreman, delete_user, edit_user

from .api import UsersApiView, UserPostsApiView, ForemanApiView, UserApiView
from .api import TechnicsApiView, TechnicApiView
from .api import ConstructionSitesApiView, ConstructionSiteApiView

from .api import WorkDaySheetsApiView, WorkDaySheetApiView
from .api import DriverSheetsApiView, DriverSheetApiView
from .api import TechnicSheetsApiView, TechnicSheetApiView

from .api import ApplicationTodayApiView
from .api import ApplicationTechnicApiView

from .api import DataBaseApiView
from .api import LoginApiView, LogoutApiView



urlpatterns = [
    path('user', UsersApiView.as_view(), name='users'),
    path('user/<int:pk>', UserApiView.as_view(), name='user_details'),
    path('user_posts', UserPostsApiView.as_view(), name='user_posts'),
    path('foreman', ForemanApiView.as_view(), name='foreman'),

    path('technic', TechnicsApiView.as_view(), name='technics'),
    path('technic/<int:pk>', TechnicApiView.as_view(), name='technic_details'),

    path('construction_site', ConstructionSitesApiView.as_view(), name='construction_sites'),
    path('construction_site/<int:pk>', ConstructionSiteApiView.as_view(), name='construction_site_details'),

    path('work_day_sheet', WorkDaySheetsApiView.as_view(), name='work_day_sheet'),
    path('work_day_sheet/<int:pk>', WorkDaySheetApiView.as_view(), name='work_day_sheet_details'),
    path('driver_sheet', DriverSheetsApiView.as_view(), name='driver_sheet'),
    path('driver_sheet/<int:pk>', DriverSheetApiView.as_view(), name='driver_sheet_details'),
    path('technic_sheet', TechnicSheetsApiView.as_view(), name='technic_sheet'),
    path('technic_sheet/<int:pk>', TechnicSheetApiView.as_view(), name='technic_sheet_details'),

    path('application_today', ApplicationTodayApiView.as_view(), name='application_today'),
    path('application_technic/<int:app_today_id>', ApplicationTechnicApiView.as_view(), name='application_technic'),

    path('get_data', DataBaseApiView.as_view(), name='get_data'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('logout/', LogoutApiView.as_view(), name='logout'),

]

