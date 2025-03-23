from rest_framework import serializers
import dashboard.models as M
import json

import dashboard.assets as A

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


class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = M.User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            telephone=validated_data["telephone"],
            post=validated_data["post"],
            supervisor_user_id=validated_data["supervisor_user_id"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = M.User
        fields = (
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "telephone",
            "telegram_id_chat",
            "post",
            "supervisor_user_id",
            "isArchive",
        )


class UserPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=50)
    description = serializers.CharField(max_length=50)


class DataBaseSerializer(serializers.Serializer):
    current_user = UserSerializer()
    today = serializers.DateField(format="%Y-%m-%d")
    current_weekday = serializers.CharField(max_length=30)
    prev_work_day = serializers.DateField(format="%Y-%m-%d")
    next_work_day = serializers.DateField(format="%Y-%m-%d")
    weekday = serializers.CharField(max_length=30)
    view_mode = serializers.CharField(max_length=30)
    accept_mode = serializers.BooleanField()
    is_authenticated = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)


class TechnicSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.Technic
        fields = "__all__"


class ConstructionSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.ConstructionSite
        fields = "__all__"


class WorkDaySheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.WorkDaySheet
        fields = "__all__"


class DateSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.WorkDaySheet
        fields = ("id", "date")


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.User
        fields = ("id", "last_name", "first_name", "telephone")

class DriverSheetSerializer(serializers.ModelSerializer):
    # driver = DriverSerializer()
    # date = DateSerializer()
    class Meta:
        model = M.DriverSheet
        fields = (
            "id",
            "driver",
            "date"
        )


class TechnicSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.TechnicSheet
        fields = "__all__"


class ApplicationMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.ApplicationMaterial
        fields = "__all__"


class ApplicationTechnicSerializer(serializers.ModelSerializer):
    # technic_sheet = TechnicSheetSerializer()
    class Meta:
        model = M.ApplicationTechnic
        fields = (
            "id",
            "application_today",
            "technic_sheet",
            "priority",
            "is_cancelled",
            "isChecked",
            "isArchive",
            "description"
        )


class ApplicationTodaySerializer(serializers.ModelSerializer):
    # date = WorkDaySheetSerializer()
    # construction_site = ConstructionSiteSerializer()

    class Meta:
        model = M.ApplicationToday
        fields = (
            "id",
            "construction_site",
            "status",
            "description",
            "date",
            "isArchive",
        )