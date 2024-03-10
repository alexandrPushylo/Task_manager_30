from django.db import models
from django.contrib.auth.models import User


#   STAFF------------------------------------------------------------------
class Administrator(models.Model):
    title = 'administrator'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'
        ordering = ['user']


class Foreman(models.Model):
    title = 'foreman'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")


    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Прораб'
        verbose_name_plural = 'Прорабы'
        ordering = ['user']


class Master(models.Model):
    title = 'master'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    foreman = models.ForeignKey(Foreman, on_delete=models.SET_NULL, null=True, verbose_name='Прораб')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")


    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'
        ordering = ['user']


class Driver(models.Model):
    title = 'driver'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")


    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Водитель'
        verbose_name_plural = 'Водители'
        ordering = ['user']


class Mechanic(models.Model):
    title = 'mechanic'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Механик'
        verbose_name_plural = 'Механики'
        ordering = ['user']


class Supply(models.Model):
    title = 'supply'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Снабжение'
        verbose_name_plural = 'Снабжение'
        ordering = ['user']


class Employee(models.Model):
    title = 'employee'
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Сотрудник')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = 'Работник'
        verbose_name_plural = 'Работники'
        ordering = ['user']


#   STAFF-END-----------------------------------------------------------------


#   TECHNIC-------------------------------------------------------------------
class Technic(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False, verbose_name="Название техники")
    type = models.CharField(max_length=255, null=False, blank=False, verbose_name="Тип техники")
    id_information = models.CharField(max_length=256, null=False, blank=False,
                                      verbose_name="Идентификационная информация")
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    attached_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='Прикрепленный водитель')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='Руководитель')
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
    foreman = models.ForeignKey(Foreman, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Прораб")
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
        verbose_name_plural = 'Рабочие дени'
        ordering = ['-date']


class DriverSheet(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="Водитель")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.date} {self.driver} [{'Рабочий' if self.status else 'Выходной'}]"

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

    def __str__(self): return f"{self.date} {self.technic} [{'Рабочий' if self.status else 'Выходной'}]"

    class Meta:
        verbose_name = 'Отметка техники'
        verbose_name_plural = 'Табель | Техники'
        ordering = ['date', 'technic']


#   Timesheet-END-------------------------------------------------------------


#   Applications--------------------------------------------------------------
class ApplicationToday(models.Model):
    construction_site = models.OneToOneField(ConstructionSite, on_delete=models.CASCADE,
                                          verbose_name="Строительный объект")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    status = models.CharField(max_length=255, null=True, blank=True, verbose_name="Статус заявки")
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Примечание для объекта")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.construction_site} [{self.date}] - {self.status}"

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
class Parameter(models.Model):
    title = models.CharField(max_length=256, verbose_name='Название переменной')
    value = models.CharField(max_length=512, null=True, blank=True, verbose_name='Значение переменной')
    flag = models.BooleanField(default=False, verbose_name='Флаг переменной')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(
            self): return f'{self.title} - {self.value} - [{self.flag}] -- [{self.user}] == ({self.time}:{self.date})'

    class Meta:
        verbose_name = "Переменная"
        verbose_name_plural = "Переменные"
        ordering = ['title', 'user']


class Telebot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    id_chat = models.CharField(max_length=128, verbose_name='id chat')

    def __str__(self): return f"{self.user} - [{self.id_chat}]"

    class Meta:
        ordering = ['user']

#   Parameters-END------------------------------------------------------------

#   Archive-------------------------------------------------------------------
#   Archive-END---------------------------------------------------------------
