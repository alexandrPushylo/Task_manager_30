from django.urls import path, re_path, include
# from .api import get_users, get_user_details, get_user_posts, get_foreman, delete_user, edit_user

from .api import UsersApiView, UserPostsApiView, UserApiView, GetUsersByPostApiView
from .api import TechnicsApiView, TechnicApiView, GetTechnicTypeApiView
from .api import ConstructionSitesApiView, ConstructionSiteApiView

from .api import WorkDaySheetsApiView, WorkDaySheetApiView
from .api import DriverSheetsApiView, DriverSheetApiView
from .api import TechnicSheetsApiView, TechnicSheetApiView

from .api import ApplicationTodayApiView
from .api import ApplicationTechnicApiView

from .api import DataBaseApiView, GetTokenApiView, IsAuthenticatedApiView, GetCurrentUserApiView
from .api import LoginApiView, LogoutApiView



urlpatterns = [
    path('users/', UsersApiView.as_view(), name='get_users'),
    path('user/<int:pk>/', UserApiView.as_view(), name='user_details'),
    path('get_user_posts/', UserPostsApiView.as_view(), name='get_user_posts'),
    path('get_users_by_post/<str:post>/', GetUsersByPostApiView.as_view(), name='get_users_by_post'),

    path('technics/', TechnicsApiView.as_view(), name='get_technics'),
    path('technic/<int:pk>/', TechnicApiView.as_view(), name='technic_details'),
    path('get_technic_type/', GetTechnicTypeApiView.as_view(), name='get_technic_type'),

    path('construction_sites/', ConstructionSitesApiView.as_view(), name='construction_sites'),
    path('construction_site/<int:pk>/', ConstructionSiteApiView.as_view(), name='construction_site_details'),

    path('work_day_sheet', WorkDaySheetsApiView.as_view(), name='get_work_day_sheet'),
    path('work_day_sheet/<int:pk>', WorkDaySheetApiView.as_view(), name='work_day_sheet_details'),
    path('driver_sheet', DriverSheetsApiView.as_view(), name='get_driver_sheet'),
    path('driver_sheet/<int:pk>', DriverSheetApiView.as_view(), name='driver_sheet_details'),
    path('technic_sheet', TechnicSheetsApiView.as_view(), name='get_technic_sheet'),
    path('technic_sheet/<int:pk>', TechnicSheetApiView.as_view(), name='technic_sheet_details'),

    path('application_today', ApplicationTodayApiView.as_view(), name='get_application_today'),
    path('application_technic/<int:app_today_id>', ApplicationTechnicApiView.as_view(), name='get_application_technic'),

    path('get_data', DataBaseApiView.as_view(), name='get_get_data'),
    path('get_token', GetTokenApiView.as_view(), name='get_token'),
    path('is_authenticated/', IsAuthenticatedApiView.as_view(), name='is_authenticated'),
    path('get_current_user/', GetCurrentUserApiView.as_view(), name='get_current_user'),
    path('login/', LoginApiView.as_view(), name='get_login'),
    path('logout/', LogoutApiView.as_view(), name='get_logout'),

]

