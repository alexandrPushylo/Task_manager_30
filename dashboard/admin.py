from django.contrib import admin
from dashboard.models import Administrator, Foreman, Master, Driver, Mechanic, Supply, Employee
from dashboard.models import Technic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter, Telebot

admin.site.register(Administrator)
admin.site.register(Foreman)
admin.site.register(Master)
admin.site.register(Driver)
admin.site.register(Mechanic)
admin.site.register(Supply)
admin.site.register(Employee)

admin.site.register(Technic)

admin.site.register(ConstructionSite)

admin.site.register(WorkDaySheet)
admin.site.register(DriverSheet)
admin.site.register(TechnicSheet)

admin.site.register(ApplicationToday)
admin.site.register(ApplicationTechnic)
admin.site.register(ApplicationMaterial)

admin.site.register(Parameter)
admin.site.register(Telebot)
