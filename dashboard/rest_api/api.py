from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, GenericAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, \
    RetrieveUpdateAPIView, RetrieveAPIView, UpdateAPIView
from django.http import HttpResponse, JsonResponse

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

import dashboard.rest_api.serializers as S
import dashboard.assets as A
import dashboard.utilities as U

#   SERVICE--------------------------------------------------
import dashboard.services.user as USERS_SERVICE
import dashboard.services.technic as TECHNIC_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.dashboard as DASHBOARD_SERVICE
import dashboard.services.application_today as APP_TODAY_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE
import dashboard.services.add_edit_application as ADD_EDIT_APP_SERVICE
import dashboard.services.parametr as PARAMETER_SERVICE
#   SERVICE--------------------------------------------------


#   USER------------------------------------------------------

class UserApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = USERS_SERVICE.get_user_queryset()

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs.get('pk')
        if U.is_valid_get_request(user_id):
            U.delete_user(user_id)
        return HttpResponse(status=204)


class UsersApiView(ListCreateAPIView):
    serializer_class = S.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = USERS_SERVICE.get_user_queryset()


class UserPostsApiView(ListAPIView):
    serializer_class = S.UserPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_row = A.UserPosts
        posts = []
        for post in post_row:
            posts.append({
                "title": post.title,
                "description": post.description,
            })
        return posts


class GetUsersByPostApiView(ListAPIView):
    serializer_class = S.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        is_valid_post = U.validate_post(self.kwargs['post'])
        if is_valid_post:
            return USERS_SERVICE.get_user_queryset().filter(
                post=self.kwargs['post'],
                isArchive=False
            ).values()
        return []

#   SPEC----------------------------------------
class DataBaseApiView(APIView):
    serializer_class = S.DataBaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.GET.get("current_day"):
            current_workday = WORK_DAY_SERVICE.get_workday(self.request.GET.get("current_day"))
        else:
            current_workday = WORK_DAY_SERVICE.get_workday(U.TODAY)

        queryset = {
            "today": {
                "date": U.TODAY,
                "weekday": U.get_weekday(U.TODAY),
                "day": U.TODAY.day,
                "month": U.TODAY.month,
                "year": U.TODAY.year,
                "month_name": A.MONTHS_T[U.TODAY.month-1],
            },
            "current_date": {
                "date": current_workday.date,
                "weekday": U.get_weekday(current_workday.date),
                "day": current_workday.date.day,
                "month": current_workday.date.month,
                "year": current_workday.date.year,
                "month_name": A.MONTHS_T[current_workday.date.month-1],
                "status": current_workday.status
            },
            "prev_work_day": WORK_DAY_SERVICE.get_prev_workday(current_workday.date).date,
            "next_work_day": WORK_DAY_SERVICE.get_next_workday(current_workday.date).date,
            "view_mode": U.get_view_mode(current_workday.date),
            "accept_mode": U.get_accept_mode(workday=current_workday),
        }
        return queryset

    def get(self, request):
        return JsonResponse(self.get_object(), status=status.HTTP_200_OK)


class IsAuthenticatedApiView(APIView):
    def get_object(self):
        queryset = {
            "is_authenticated": False,
            "user_id": None
        }
        if self.request.user.is_authenticated:
            queryset['is_authenticated'] = True
            queryset['user_id'] = self.request.user.id
        return queryset

    def get(self, request):
        return JsonResponse(self.get_object(), status=status.HTTP_200_OK)


class GetCurrentUserApiView(APIView):
    serializer_class = S.UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return S.UserSerializer(self.request.user).data

    def get(self, request):
        return JsonResponse(self.get_object(), status=status.HTTP_200_OK)


class GetTokenApiView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        if self.request.user.is_authenticated:
            return JsonResponse({"csrftoken": self.request.META.get('CSRF_COOKIE')}, status=status.HTTP_200_OK)
        return JsonResponse({"error": "Не авторизован"}, status=status.HTTP_401_UNAUTHORIZED)


class ChangeAcceptModeApiView(UpdateAPIView):
    serializer_class = S.AcceptModeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        current_day = self.request.GET.get("current_day", U.TODAY)
        workday = WORK_DAY_SERVICE.get_workday(current_day)
        print(workday)
        if U.is_valid_get_request('accept_mode'):
            accept_mode = U.get_AcceptMode(self.request.data.get('accept_mode'))
            U.set_accept_mode(workday, accept_mode)
            return JsonResponse({"message": "Успешно"}, status=status.HTTP_200_OK)
        return JsonResponse({"error": "Не верный параметр"}, status=status.HTTP_400_BAD_REQUEST)


    # def patch(self, request):
    #     current_day = self.request.GET.get("current_day", U.TODAY)
    #     workday = WORK_DAY_SERVICE.get_workday(current_day)
    #     if U.is_valid_get_request('accept_mode'):
    #         U.set_accept_mode(workday, request.data.get('accept_mode'))
    #         return JsonResponse({"message": "Успешно"}, status=status.HTTP_200_OK)
    #     return JsonResponse({"error": "Не верный параметр"}, status=status.HTTP_400_BAD_REQUEST)


class LoginApiView(APIView):
    serializer_class = S.LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        username = self.request.data.get("username")
        password = self.request.data.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            csrftoken = self.request.META.get('CSRF_COOKIE')
            return JsonResponse({"message": "Успешно", "csrftoken": csrftoken}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"error": "Не верный логин или пароль"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if self.request.user.is_authenticated:
            logout(request)
            return JsonResponse({"message": "Успешно"}, status=status.HTTP_200_OK)


#   TECHNIC--------------------------------------------------
class TechnicsApiView(ListCreateAPIView):
    serializer_class = S.TechnicSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TECHNIC_SERVICE.get_technics_queryset()


class TechnicApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.TechnicSerializer
    queryset = TECHNIC_SERVICE.get_technics_queryset()

    def delete(self, request, *args, **kwargs):
        technic_id = self.kwargs.get('pk')
        if U.is_valid_get_request(technic_id):
            U.delete_technic(technic_id)
        return HttpResponse(status=204)


class GetTechnicTypeApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return {"technic_types": TECHNIC_SERVICE.get_technic_type()}

    def get(self, request):
        return JsonResponse(self.get_object(), status=status.HTTP_200_OK)


#   CONSTRUCTION_SITE--------------------------------------------------
class ConstructionSitesApiView(ListCreateAPIView):
    serializer_class = S.ConstructionSiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CONSTR_SITE_SERVICE.get_construction_site_queryset()


class ConstructionSiteApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.ConstructionSiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CONSTR_SITE_SERVICE.get_construction_site_queryset()

    def delete(self, request, *args, **kwargs):
        construction_site = CONSTR_SITE_SERVICE.get_construction_sites(pk=self.kwargs["pk"])
        construction_site.deleted_date = U.TODAY
        construction_site.isArchive = True
        construction_site.save(update_fields=['isArchive', 'deleted_date'])
        return HttpResponse(status=204)


#   WORK_DAY_SHEET--------------------------------------------------
class WorkDaySheetsApiView(ListAPIView):
    serializer_class = S.WorkDaysSheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset_raw = WORK_DAY_SERVICE.get_workday_queryset(
            date__gte=U.TODAY - timedelta(days=3),
            date__lte=U.TODAY + timedelta(days=7),
        )

        queryset = [{
            "id": item.id,
            "date": item.date,
            "status": item.status,
            "isArchive": item.isArchive,
            "is_all_application_send": item.is_all_application_send,
            "accept_mode": item.accept_mode,
            "weekday": U.get_weekday(item.date),
        } for item in queryset_raw]
        return queryset


class GetPrevOrNextWorkDayApiView(APIView):
    serializer_class = S.WorkDaysSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        side = self.request.GET.get("side")
        if side == "prev":
            queryset_raw = WORK_DAY_SERVICE.get_prev_workday(current_day)
        elif side == "next":
            queryset_raw = WORK_DAY_SERVICE.get_next_workday(current_day)
        else:
            queryset_raw = WORK_DAY_SERVICE.get_workday(current_day)

        return {
            "id": queryset_raw.id,
            "date": queryset_raw.date,
            "status": queryset_raw.status,
            "accept_mode": queryset_raw.accept_mode,
            "weekday": U.get_weekday(queryset_raw.date)
        }
    def get(self, request):
        return JsonResponse(self.get_object(), status=status.HTTP_200_OK)



class GetWorkDayApiView(ListAPIView):
    serializer_class = S.WorkDaysSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset_raw = WORK_DAY_SERVICE.get_workday_queryset(
            date__gte=U.TODAY - timedelta(days=1),
            date__lte=U.TODAY + timedelta(days=3),
        ).reverse()

        queryset = [{
            "id": item.id,
            "date": item.date,
            "day": item.date.day,
            "month": item.date.month,
            "status": item.status,
            "weekday": U.get_weekday(item.date)[:3],
        } for item in queryset_raw]
        return queryset

class WorkDaySheetApiView(RetrieveUpdateAPIView):
    serializer_class = S.WorkDaySheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WORK_DAY_SERVICE.get_workday_queryset()

#   DRIVER_SHEET--------------------------------------------------
class DriverSheetsApiView(ListAPIView):
    serializer_class = S.DriverSheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        date = self.request.GET.get("current_day", U.TODAY)
        return DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(date__date=date)


class DriverSheetApiView(RetrieveUpdateAPIView):
    serializer_class = S.DriverSheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DRIVER_SHEET_SERVICE.get_driver_sheet_queryset()


#   TECHNIC_SHEET--------------------------------------------------
class TechnicSheetsApiView(ListAPIView):
    serializer_class = S.TechnicSheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        date = self.request.GET.get("current_day", U.TODAY)
        return TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(date__date=date)


class TechnicSheetApiView(RetrieveUpdateAPIView):
    serializer_class = S.TechnicSheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset()


#   APPLICATION TODAY--------------------------------------------------
class ApplicationsTodayApiView(ListCreateAPIView):
    serializer_class = S.ApplicationTodaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        return APP_TODAY_SERVICE.get_apps_today_queryset(date__date=current_day)


class ApplicationTodayApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.ApplicationTodaySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = APP_TODAY_SERVICE.get_apps_today_queryset()


#   APPLICATION TECHNIC--------------------------------------------------
class ApplicationsTechnicApiView(ListCreateAPIView):
    serializer_class = S.ApplicationTechnicSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        return APP_TECHNIC_SERVICE.get_apps_technic_queryset(application_today__date__date=current_day)


class ApplicationTechnicByATApiView(ListAPIView):
    serializer_class = S.ApplicationTechnicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.kwargs["app_today_id"]:
            app_today_id = self.kwargs["app_today_id"]
            return APP_TECHNIC_SERVICE.get_apps_technic_queryset(application_today = app_today_id)
        else:
            return []
        # app_today_id = self.kwargs["app_today_id"]
        # return APP_TECHNIC_SERVICE.get_apps_technic_queryset(application_today = app_today_id)


class ApplicationTechnicApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.ApplicationTechnicSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = APP_TECHNIC_SERVICE.get_apps_technic_queryset()

#   APPLICATION MATERIAL--------------------------------------------------

class ApplicationsMaterialApiView(ListCreateAPIView):
    serializer_class = S.ApplicationMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        return APP_MATERIAL_SERVICE.get_apps_material_queryset(application_today__date__date=current_day)


class ApplicationMaterialByATApiView(ListAPIView):
    serializer_class = S.ApplicationMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.kwargs["app_today_id"]:
            app_today_id = self.kwargs["app_today_id"]
            return APP_MATERIAL_SERVICE.get_apps_material_queryset(application_today = app_today_id)
        else:
            return []


class ApplicationMaterialApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.ApplicationMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = APP_MATERIAL_SERVICE.get_apps_material_queryset()


#   Services--------------------------------------------------------------

class GetPriorityIdList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        workday = WORK_DAY_SERVICE.get_workday(current_day)
        technic_sheet_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            date=workday, driver_sheet__isnull=False, status=True, isArchive=False
        )
        priority_id_list = U.get_priority_id_list(technic_sheet=technic_sheet_list)
        return {"priority_id_list": list(priority_id_list)}

    def get(self, request):
        return JsonResponse(self.get_queryset(), status=status.HTTP_200_OK)


class GetConflictTechnicSheetIdList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        workday = WORK_DAY_SERVICE.get_workday(current_day)
        technic_sheet_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            date=workday, driver_sheet__isnull=False, status=True, isArchive=False
        )
        priority_id_list = U.get_priority_id_list(technic_sheet=technic_sheet_list)
        busiest_technic_title_list = U.get_busiest_technic_title(technic_sheet_list)
        conflict_technic_sheet = U.get_conflict_list_of_technic_sheet(
            busiest_technic_title=busiest_technic_title_list,
            priority_id_list=priority_id_list,
            get_only_id_list=True,
        )
        return {"conflict_technic_sheet": conflict_technic_sheet}

    def get(self, request):
        return JsonResponse(self.get_queryset(), status=status.HTTP_200_OK)


class GetStatusListAppToday(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        workday = WORK_DAY_SERVICE.get_workday(current_day)

        applications_today = APP_TODAY_SERVICE.get_apps_today_queryset(
            order_by=("status",),
            isArchive=False,
            date=workday,
            # construction_site__in=construction_sites,
        )
        status_list_application_today = U.get_status_lists_of_apps_today(
                applications_today=applications_today
            )
        return {"status_list_application_today": status_list_application_today}

    def get(self, request):
        return JsonResponse(self.get_queryset(), status=status.HTTP_200_OK)
