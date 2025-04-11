from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, GenericAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, \
    RetrieveUpdateAPIView, RetrieveAPIView
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
        user = USERS_SERVICE.get_user(pk=self.kwargs["pk"])
        user.isArchive = True
        user.save(update_fields=['isArchive'])
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


class ForemanApiView(ListAPIView):
    serializer_class = S.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = USERS_SERVICE.get_user_queryset().filter(post=A.UserPosts.FOREMAN.title).values()


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
            "today": U.TODAY,
            "current_weekday": U.get_weekday(U.TODAY),
            "prev_work_day": WORK_DAY_SERVICE.get_prev_workday(current_workday.date).date,
            "next_work_day": WORK_DAY_SERVICE.get_next_workday(current_workday.date).date,
            "weekday": U.get_weekday(current_workday.date),
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
        technic = TECHNIC_SERVICE.get_technic(pk=self.kwargs["pk"])
        technic.isArchive = True
        technic.save(update_fields=['isArchive'])
        return HttpResponse(status=204)


#   CONSTRUCTION_SITE--------------------------------------------------
class ConstructionSitesApiView(ListCreateAPIView):
    serializer_class = S.ConstructionSiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CONSTR_SITE_SERVICE.get_construction_site_queryset()


class ConstructionSiteApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = S.ConstructionSiteSerializer
    queryset = CONSTR_SITE_SERVICE.get_construction_site_queryset()

    def delete(self, request, *args, **kwargs):
        construction_site = CONSTR_SITE_SERVICE.get_construction_sites(pk=self.kwargs["pk"])
        construction_site.deleted_date = U.TODAY
        construction_site.isArchive = True
        construction_site.save(update_fields=['isArchive', 'deleted_date'])
        return HttpResponse(status=204)


#   WORK_DAY_SHEET--------------------------------------------------
class WorkDaySheetsApiView(ListAPIView):
    serializer_class = S.WorkDaySheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WORK_DAY_SERVICE.get_workday_queryset(
        date__gte=U.TODAY-timedelta(days=3),
        date__lte=U.TODAY+timedelta(days=7),
    )


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
class ApplicationTodayApiView(ListAPIView):
    serializer_class = S.ApplicationTodaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current_day = self.request.GET.get("current_day", U.TODAY)
        return APP_TODAY_SERVICE.get_apps_today_queryset(date__date=current_day)


#   APPLICATION TECHNIC--------------------------------------------------
class ApplicationTechnicApiView(ListAPIView):
    serializer_class = S.ApplicationTechnicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        app_today_id = self.kwargs["app_today_id"]
        return APP_TECHNIC_SERVICE.get_apps_technic_queryset(application_today = app_today_id)