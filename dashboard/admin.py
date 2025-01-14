from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from dashboard.models import User
from dashboard.models import Technic, TemplateDescForTechnic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": (
            "first_name",
            "last_name",
            "email",
            "telephone",
            "telegram_id_chat",
            "color_title",
            "font_size"
        )}),
        (_("Post"), {"fields": ("post", "supervisor_user_id")}),
        (_("Filter"), {"fields": ("is_show_panel",
                                  "is_show_saved_app",
                                  "is_show_absent_app",
                                  "is_show_technic_app",
                                  "is_show_material_app",
                                  "filter_construction_site",
                                  "filter_foreman",
                                  "filter_technic",
                                  "sort_by")}),
        (_("Permissions"), {"fields": (
            "isArchive",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        ),
        },
         ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("username", "last_name", "post", "isArchive")
    list_filter = ("post", "isArchive")


#   Technic ----------------------------------------------------------------
@admin.register(Technic)
class TechnicAdmin(admin.ModelAdmin):
    list_display = ("title", "id_information", "attached_driver", "isArchive")
    list_filter = ('type', 'isArchive')
    list_editable = ('attached_driver', 'isArchive')


#   TemplateDescForTechnic ----------------------------------------------------------------
@admin.register(TemplateDescForTechnic)
class TemplateDescForTechnicAdmin(admin.ModelAdmin):
    list_display = ('technic', 'description', 'is_auto_mode', 'is_default_mode', )

admin.site.register(ConstructionSite)



#   WorkDaySheet ----------------------------------------------------------------
@admin.action(description="Назначить выходным днем")
def set_weekend(modeladmin, request, queryset):
    queryset.update(status=False)
@admin.action(description="Назначить рабочим днем")
def set_workday(modeladmin, request, queryset):
    queryset.update(status=True)

@admin.register(WorkDaySheet)
class WorkDaySheetAdmin(admin.ModelAdmin):
    list_display = ("date", "status", "accept_mode")
    list_filter = ("date", "status", "accept_mode")
    list_editable = ("status",)
    list_per_page = 20
    actions = (set_workday, set_weekend)

#   DriverSheet ----------------------------------------------------------------
@admin.register(DriverSheet)
class DriverSheetAdmin(admin.ModelAdmin):
    driver_count = User.objects.filter(post='driver', isArchive=False).count()
    list_display = ("date", "driver", "status")
    list_per_page = driver_count
    list_editable = ("status","driver")
    list_filter = ("status", "isArchive")


#   TechnicSheet ----------------------------------------------------------------
@admin.register(TechnicSheet)
class TechnicSheetAdmin(admin.ModelAdmin):
    technic_count = Technic.objects.filter(isArchive=False).count()
    list_display = ("date", "technic", "status")
    list_per_page = technic_count
    list_filter = ("status", "isArchive")
    list_editable = ("status", "technic")



admin.site.register(ApplicationToday)
admin.site.register(ApplicationTechnic)
admin.site.register(ApplicationMaterial)

admin.site.register(Parameter)
# admin.site.register(Telebot)
