from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

# from dashboard.models import Administrator, Foreman, Master, Driver, Mechanic, Supply, Employee
# from dashboard.models import Supervisor
from dashboard.models import User
from dashboard.models import Technic, TemplateDescForTechnic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter


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


admin.site.register(User, CustomUserAdmin)

admin.site.register(Technic)
admin.site.register(TemplateDescForTechnic)

admin.site.register(ConstructionSite)

admin.site.register(WorkDaySheet)
admin.site.register(DriverSheet)
admin.site.register(TechnicSheet)

admin.site.register(ApplicationToday)
admin.site.register(ApplicationTechnic)
admin.site.register(ApplicationMaterial)

admin.site.register(Parameter)
# admin.site.register(Telebot)
