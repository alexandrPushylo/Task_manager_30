from django.urls import path, re_path, include
# from .api import get_users, get_user_details, get_user_posts, get_foreman, delete_user, edit_user

from .api import UsersApiView, UserPostsApiView, UserApiView, GetUsersByPostApiView
from .api import TechnicsApiView, TechnicApiView, GetTechnicTypeApiView
from .api import ConstructionSitesApiView, ConstructionSiteApiView

from .api import WorkDaySheetsApiView, WorkDaySheetApiView, GetWorkDayApiView, GetPrevOrNextWorkDayApiView
from .api import DriverSheetsApiView, DriverSheetApiView
from .api import TechnicSheetsApiView, TechnicSheetApiView

from .api import ApplicationsTodayApiView, ApplicationTodayApiView
from .api import ApplicationTechnicByATApiView, ApplicationsTechnicApiView, ApplicationTechnicApiView
from .api import ApplicationMaterialByATApiView, ApplicationsMaterialApiView, ApplicationMaterialApiView

from .api import DataBaseApiView, GetTokenApiView, IsAuthenticatedApiView, GetCurrentUserApiView
from .api import LoginApiView, LogoutApiView

from .api import GetPriorityIdList, GetConflictTechnicSheetIdList, GetStatusListAppToday
from .api import ChangeAcceptModeApiView


urlpatterns = [
    path('users/', UsersApiView.as_view(), name='get_users'),
    path('user/<int:pk>/', UserApiView.as_view(), name='user_details'),
    path('get_user_posts/', UserPostsApiView.as_view(), name='get_user_posts'),
    path('get_users_by_post/<str:post>/', GetUsersByPostApiView.as_view(), name='get_users_by_post'),

    path('get_priority_id_list/', GetPriorityIdList.as_view(), name='get_priority_id_list'),
    path('get_conflict_id_list/', GetConflictTechnicSheetIdList.as_view(), name='get_conflict_id_list'),
    path('get_status_list_app_today/', GetStatusListAppToday.as_view(), name='get_status_list_app_today'),

    path('technics/', TechnicsApiView.as_view(), name='get_technics'),
    path('technic/<int:pk>/', TechnicApiView.as_view(), name='technic_details'),
    path('get_technic_type/', GetTechnicTypeApiView.as_view(), name='get_technic_type'),

    path('construction_sites/', ConstructionSitesApiView.as_view(), name='construction_sites'),
    path('construction_site/<int:pk>/', ConstructionSiteApiView.as_view(), name='construction_site_details'),

    path('get_work_day/', GetWorkDayApiView.as_view(), name='get_work_day'),
    path('get_prev_next_work_day/', GetPrevOrNextWorkDayApiView.as_view(), name='next_work_day'),


    path('work_day_sheet/', WorkDaySheetsApiView.as_view(), name='get_work_day_sheet'),
    path('work_day_sheet/<int:pk>/', WorkDaySheetApiView.as_view(), name='work_day_sheet_details'),
    path('driver_sheet/', DriverSheetsApiView.as_view(), name='get_driver_sheet'),
    path('driver_sheet/<int:pk>/', DriverSheetApiView.as_view(), name='driver_sheet_details'),
    path('technic_sheet/', TechnicSheetsApiView.as_view(), name='get_technic_sheet'),
    path('technic_sheet/<int:pk>/', TechnicSheetApiView.as_view(), name='technic_sheet_details'),

    path('applications_today/', ApplicationsTodayApiView.as_view(), name='get_applications_today'),
    path('application_today/<int:pk>/', ApplicationTodayApiView.as_view(), name='get_application_today'),

    path('applications_technic/', ApplicationsTechnicApiView.as_view(), name='get_applications_technic'),
    path('application_technic/<int:pk>/', ApplicationTechnicApiView.as_view(), name='get_application_technic'),
    path('application_technic/by_application_today/<int:app_today_id>/', ApplicationTechnicByATApiView.as_view(), name='get_application_technicByAT'),

    path('applications_material/', ApplicationsMaterialApiView.as_view(), name='get_applications_material'),
    path('application_material/<int:pk>/', ApplicationMaterialApiView.as_view(), name='get_application_material'),
    path('application_material/by_application_today/<int:app_today_id>/', ApplicationMaterialByATApiView.as_view(), name='get_application_materialByAT'),

    path('spec/change_accept_mode/', ChangeAcceptModeApiView.as_view(), name='change_accept_mode'),

    path('get_data/', DataBaseApiView.as_view(), name='get_data'),
    path('get_token', GetTokenApiView.as_view(), name='get_token'),
    path('is_authenticated/', IsAuthenticatedApiView.as_view(), name='is_authenticated'),
    path('get_current_user/', GetCurrentUserApiView.as_view(), name='get_current_user'),
    path('login/', LoginApiView.as_view(), name='get_login'),
    path('logout/', LogoutApiView.as_view(), name='get_logout'),

]

