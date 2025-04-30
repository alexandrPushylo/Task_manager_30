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
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            password=validated_data.get("password"),
            telephone=validated_data.get("telephone"),
            post=validated_data.get("post"),
            supervisor_user_id=validated_data.get("supervisor_user_id"),
        )
        user.save()
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

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
            "is_show_panel",
            "is_show_saved_app",
            "is_show_absent_app",
            "is_show_technic_app",
            "is_show_material_app",
            "filter_construction_site",
            "filter_foreman",
            "filter_technic",
            "sort_by",
            "color_title",
            "font_size"
        )
        sort_fields = ('last_name', "username")


class UserPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=50)
    description = serializers.CharField(max_length=50)


class DataBaseSerializer(serializers.Serializer):
    today = serializers.DateField(format="%Y-%m-%d")
    current_day = serializers.DateField(format="%Y-%m-%d")
    current_weekday = serializers.CharField(max_length=30)
    prev_work_day = serializers.DateField(format="%Y-%m-%d")
    next_work_day = serializers.DateField(format="%Y-%m-%d")
    weekday = serializers.CharField(max_length=30)
    view_mode = serializers.CharField(max_length=30)
    accept_mode = serializers.BooleanField()


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


class WorkDaysSheetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    date = serializers.DateField(format="%Y-%m-%d")
    status = serializers.BooleanField()
    isArchive = serializers.BooleanField()
    is_all_application_send = serializers.BooleanField()
    accept_mode = serializers.ChoiceField(choices=(
        (A.AcceptMode.AUTO.value, A.AcceptMode.AUTO.value),
        (A.AcceptMode.MANUAL.value, A.AcceptMode.MANUAL.value),
        (A.AcceptMode.OFF.value, A.AcceptMode.OFF.value)))
    weekday = serializers.CharField(max_length=30)


class WorkDaySheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = M.WorkDaySheet
        fields = "__all__"


class WorkDaysSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    date = serializers.DateField(format="%Y-%m-%d")
    day = serializers.IntegerField()
    month = serializers.IntegerField()
    status = serializers.BooleanField()
    weekday = serializers.CharField(max_length=30)


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
        fields = "__all__"


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

class AcceptModeSerializer(serializers.Serializer):
    accept_mode = serializers.ChoiceField(choices=(
        (A.AcceptMode.AUTO.value, A.AcceptMode.AUTO.value),
        (A.AcceptMode.MANUAL.value, A.AcceptMode.MANUAL.value),
        (A.AcceptMode.OFF.value, A.AcceptMode.OFF.value)))