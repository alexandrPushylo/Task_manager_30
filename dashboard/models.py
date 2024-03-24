from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from dashboard.assets import EMPLOYEE, ADMINISTRATOR, MECHANIC


class User(AbstractUser):
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    telegram_id_chat = models.CharField(max_length=128, null=True, blank=True, verbose_name='Telegram id chat')
    post = models.CharField(max_length=50, null=False, blank=False, verbose_name="Должность", default=EMPLOYEE)
    supervisor_user_id = models.IntegerField(null=True, blank=True, verbose_name='Ид руководителя', default=None)
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")


#   TECHNIC-------------------------------------------------------------------
class Technic(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False, verbose_name="Название техники")
    type = models.CharField(max_length=255, null=False, blank=False, verbose_name="Тип техники")
    id_information = models.CharField(max_length=256, null=False, blank=False,
                                      verbose_name="Идентификационная информация")
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    attached_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='attached_driver',
                                        verbose_name='Прикрепленный водитель')
    supervisor_technic = models.CharField(max_length=100, verbose_name='Руководитель', default=MECHANIC)
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.title} ({self.attached_driver}) [{self.id_information}]"

    class Meta:
        verbose_name = "Единица техники"
        verbose_name_plural = "Техника"
        ordering = ['title']


#   TECHNIC-END---------------------------------------------------------------


#   Construction Site---------------------------------------------------------
class ConstructionSite(models.Model):
    address = models.CharField(max_length=512, verbose_name="Адрес", null=False)
    foreman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Прораб")
    deleted_date = models.DateField(null=True, blank=True, verbose_name="Дата удаления")
    status = models.BooleanField(default=True, verbose_name="Статус объекта")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.address} ({self.foreman}) - {'Открыт' if self.status else 'Закрыт'}"

    class Meta:
        verbose_name = "Строительный объект"
        verbose_name_plural = "Строительные объекты"
        ordering = ['address', 'foreman']


#   Construction Site-END-----------------------------------------------------


#   Timesheet-----------------------------------------------------------------
class WorkDaySheet(models.Model):
    date = models.DateField(verbose_name="Дата", null=False, blank=False)
    status = models.BooleanField(default=True, verbose_name="Рабочий день")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.date} - {'Рабочий' if self.status else 'Выходной'}"

    class Meta:
        verbose_name = 'Рабочий день'
        verbose_name_plural = 'Рабочие дни'
        ordering = ['-date']


class DriverSheet(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Водитель")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.date.date} {self.driver} [{'Работает' if self.status else 'Не работает'}]"

    class Meta:
        verbose_name = 'Отметка водителя'
        verbose_name_plural = 'Табель | Водители'
        ordering = ['date', 'driver']


class TechnicSheet(models.Model):
    technic = models.ForeignKey(Technic, on_delete=models.CASCADE, verbose_name='Транспортное средство')
    driver_sheet = models.ForeignKey(DriverSheet, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="Табель водителя")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    status = models.BooleanField(default=True, verbose_name="Статус техники")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.date.date} {self.technic} [{'Рабочий' if self.status else 'Выходной'}]"

    class Meta:
        verbose_name = 'Отметка техники'
        verbose_name_plural = 'Табель | Техники'
        ordering = ['date', 'technic']


#   Timesheet-END-------------------------------------------------------------


#   Applications--------------------------------------------------------------
class ApplicationToday(models.Model):
    construction_site = models.OneToOneField(ConstructionSite, on_delete=models.CASCADE,
                                             verbose_name="Строительный объект")
    date = models.OneToOneField(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата",
                                related_name="application_today")
    status = models.CharField(max_length=255, null=True, blank=True, verbose_name="Статус заявки")
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Примечание для объекта")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.construction_site} [{self.date.date}] - {self.status}"

    class Meta:
        verbose_name = "Заявка на объект"
        verbose_name_plural = "Заявки на объект"
        ordering = ['-date', 'construction_site']


class ApplicationTechnic(models.Model):
    application_today = models.ForeignKey(ApplicationToday, on_delete=models.CASCADE, verbose_name="Заявка на объект")
    technic_sheet = models.ForeignKey(TechnicSheet, on_delete=models.SET_NULL, null=True,
                                      verbose_name='Отметка техники')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.IntegerField(default=1, verbose_name='Приоритет заявки')
    isChecked = models.BooleanField(default=False, verbose_name='Проверена?')
    id_orig_app = models.IntegerField(null=True, blank=True, verbose_name='Ид ApplicationTechnic')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.application_today} {self.technic_sheet}"

    class Meta:
        verbose_name = "Заявка на технику"
        verbose_name_plural = "Заявки на технику"


class ApplicationMaterial(models.Model):
    application_today = models.OneToOneField(ApplicationToday, on_delete=models.CASCADE,
                                             verbose_name="Заявка на объект")
    description = models.TextField(max_length=2048, verbose_name="Описание")
    isChecked = models.BooleanField(default=False, verbose_name='Проверенна?')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.application_today} - {self.description}"

    class Meta:
        verbose_name = 'Заявка на материал'
        verbose_name_plural = 'Заявка на материалы'

#   Applications-END----------------------------------------------------------


#   Parameters----------------------------------------------------------------
# class Parameter(models.Model):
#     title = models.CharField(max_length=256, verbose_name='Название переменной')
#     value = models.CharField(max_length=512, null=True, blank=True, verbose_name='Значение переменной')
#     flag = models.BooleanField(default=False, verbose_name='Флаг переменной')
#     description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
#     time = models.TimeField(null=True, blank=True)
#     date = models.DateField(null=True, blank=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#
#     def __str__(
#             self): return f'{self.title} - {self.value} - [{self.flag}] -- [{self.user}] == ({self.time}:{self.date})'
#
#     class Meta:
#         verbose_name = "Переменная"
#         verbose_name_plural = "Переменные"
#         ordering = ['title', 'user']

# class Telebot(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
#     id_chat = models.CharField(max_length=128, verbose_name='id chat')
#
#     def __str__(self): return f"{self.user} - [{self.id_chat}]"
#
#     class Meta:
#         ordering = ['user']

#   Parameters-END------------------------------------------------------------

#   Archive-------------------------------------------------------------------
#   Archive-END---------------------------------------------------------------
