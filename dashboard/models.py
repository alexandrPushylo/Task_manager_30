from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from .assets import UserPosts, AcceptMode


class User(AbstractUser):
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    telegram_id_chat = models.CharField(max_length=128, null=True, blank=True, verbose_name='Telegram id chat')
    post = models.CharField(max_length=50, null=False, blank=False, verbose_name="Должность",
                            default=UserPosts.EMPLOYEE.title)
    supervisor_user_id = models.IntegerField(null=True, blank=True, verbose_name='Ид руководителя', default=None)
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    is_show_panel = models.BooleanField(default=False, verbose_name="Показывать панель")

    is_show_saved_app = models.BooleanField(default=True, verbose_name="Показывать сохраненные заявки")
    is_show_absent_app = models.BooleanField(default=True, verbose_name="Показывать отсутствующие заявки")
    is_show_technic_app = models.BooleanField(default=True, verbose_name="Показывать заявки на технику")
    is_show_material_app = models.BooleanField(default=True, verbose_name="Показывать заявки на материалы")

    filter_construction_site = models.IntegerField(default=0, verbose_name="Фильтр по строительному объекту")
    filter_foreman = models.IntegerField(default=0, verbose_name="Фильтр по прорабу")
    filter_technic = models.CharField(max_length=100, null=True, blank=True, verbose_name='Фильтр по технике')
    sort_by = models.CharField(max_length=100, null=True, blank=True, verbose_name='Сортировать по:')

    color_title = models.CharField(max_length=8, null=False, default='#000000', verbose_name='Цвет названия объекта')
    font_size = models.IntegerField(default=10, verbose_name='Размер шрифта для описания заявки')

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['last_name']


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
    supervisor_technic = models.CharField(max_length=100, verbose_name='Руководитель',
                                          default=UserPosts.MECHANIC.title)
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self):
        return f"{self.title} ({self.attached_driver}) [{self.id_information}]"

    class Meta:
        verbose_name = "Единица техники"
        verbose_name_plural = "Техника"
        ordering = ['title', 'attached_driver']


class TemplateDescForTechnic(models.Model):
    technic = models.OneToOneField(Technic, on_delete=models.CASCADE, null=False, blank=False, verbose_name='Техника')
    description = models.TextField(max_length=1024, null=True, blank=True, default='', verbose_name="Описание")

    is_auto_mode = models.BooleanField(default=True, verbose_name='Автоматический режим')
    is_default_mode = models.BooleanField(default=False, verbose_name='Режим по умолчанию')

    def __str__(self):
        return f"[{'auto' if self.is_auto_mode else 'default' if self.is_default_mode else 'manual'}] {self.technic} ({self.description}) "

    class Meta:
        verbose_name = "Templates для техники"
        verbose_name_plural = "Template для техники"
        ordering = ['technic',]

#   TECHNIC-END---------------------------------------------------------------


#   Construction Site---------------------------------------------------------
class ConstructionSite(models.Model):
    address = models.CharField(max_length=512, verbose_name="Адрес", null=False)
    foreman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Прораб")
    deleted_date = models.DateField(null=True, blank=True, verbose_name="Дата удаления")
    status = models.BooleanField(default=True, verbose_name="Статус объекта")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.address} ({self.foreman})"

    class Meta:
        verbose_name = "Строительный объект"
        verbose_name_plural = "Строительные объекты"
        ordering = ['address', 'foreman']


#   Construction Site-END-----------------------------------------------------


#   Timesheet-----------------------------------------------------------------
class WorkDaySheet(models.Model):
    date = models.DateField(verbose_name="Дата", null=False, blank=False)
    status = models.BooleanField(default=True, verbose_name="Рабочий день")
    accept_mode = models.CharField(default=AcceptMode.AUTO.value, max_length=32, verbose_name="Режим приема заявок")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")
    is_all_application_send = models.BooleanField(default=False, verbose_name="Заявки отправлены?")

    def send_all_application(self):
        self.is_all_application_send = True
        self.save(update_fields=['is_all_application_send'])

    def __str__(self):
        return f"{self.date}"

    class Meta:
        verbose_name = 'Рабочий день'
        verbose_name_plural = 'Рабочие дни'
        ordering = ['-date']


class DriverSheet(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Водитель")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def __str__(self): return f"{self.driver} [{'Работает' if self.status else 'Не работает'}]"

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
    count_application = models.IntegerField(default=0, verbose_name='Количество заявок (загруженость)')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")

    def increment_count_application(self):
        self.count_application = self.count_application + 1
        self.save(update_fields=['count_application'])

    def decrement_count_application(self):
        if self.count_application > 0:
            self.count_application = self.count_application - 1
            self.save(update_fields=['count_application'])

    def __str__(self): return f"{self.technic}"

    class Meta:
        verbose_name = 'Отметка техники'
        verbose_name_plural = 'Табель | Техники'
        ordering = ['date', 'technic']


#   Timesheet-END-------------------------------------------------------------


#   Applications--------------------------------------------------------------
class ApplicationToday(models.Model):
    ABSENT = 'absent'
    SAVED = 'saved'
    SUBMITTED = 'submitted'
    APPROVED = 'approved'
    SEND = 'send'

    construction_site = models.ForeignKey(ConstructionSite, on_delete=models.CASCADE,
                                          verbose_name="Строительный объект")
    date = models.ForeignKey(WorkDaySheet, on_delete=models.CASCADE, verbose_name="Дата")
    status = models.CharField(max_length=255, null=True, blank=True, verbose_name="Статус заявки", default=ABSENT)
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Примечание для объекта")
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")
    is_application_send = models.BooleanField(default=False, verbose_name="Заявка отправлена?")
    is_edited = models.BooleanField(default=False, verbose_name="Был отредактирован?")

    def send_application(self):
        self.is_application_send = True
        self.save(update_fields=['is_application_send'])

    def set_next_status(self):
        if self.status == self.ABSENT:
            self.status = self.SAVED
        elif self.status == self.SAVED:
            self.status = self.SUBMITTED
        elif self.status == self.SUBMITTED:
            self.status = self.APPROVED
        elif self.status == self.APPROVED:
            self.status = self.SEND
            # self.is_application_send = True
        self.save(update_fields=['status'])

    def make_edited(self):
        self.is_edited = True
        self.save(update_fields=['is_edited'])


    def __str__(self): return f"{self.construction_site} [{self.date.date}] - {self.status}"

    class Meta:
        verbose_name = "Заявка на объект"
        verbose_name_plural = "Заявки на объект"
        ordering = ['date', 'construction_site']


class ApplicationTechnic(models.Model):
    application_today = models.ForeignKey(ApplicationToday, on_delete=models.CASCADE, verbose_name="Заявка на объект")
    technic_sheet = models.ForeignKey(TechnicSheet, on_delete=models.SET_NULL, null=True,
                                      verbose_name='Отметка техники')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.IntegerField(default=1, verbose_name='Приоритет заявки')
    isChecked = models.BooleanField(default=False, verbose_name='Проверена?')
    id_orig_app = models.IntegerField(null=True, blank=True, verbose_name='Ид ApplicationTechnic')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")
    is_cancelled = models.BooleanField(default=False, verbose_name='Отменена?')

    def __str__(self): return f"{self.application_today} {self.technic_sheet}"

    class Meta:
        verbose_name = "Заявка на технику"
        verbose_name_plural = "Заявки на технику"
        ordering = ['application_today', 'technic_sheet']


class ApplicationMaterial(models.Model):
    application_today = models.OneToOneField(ApplicationToday, on_delete=models.CASCADE,
                                             verbose_name="Заявка на объект")
    description = models.TextField(max_length=4096, verbose_name="Описание")
    isChecked = models.BooleanField(default=False, verbose_name='Проверенна?')
    isArchive = models.BooleanField(default=False, verbose_name="Архивирован?")
    is_cancelled = models.BooleanField(default=False, verbose_name='Отменена?')

    def __str__(self): return f"{self.application_today} - {self.description}"

    class Meta:
        verbose_name = 'Заявка на материал'
        verbose_name_plural = 'Заявка на материалы'
        ordering = ['application_today',]

#   Applications-END----------------------------------------------------------


#   Parameters----------------------------------------------------------------
class Parameter(models.Model):
    title = models.CharField(max_length=256, verbose_name='Название переменной', null=True, blank=True)
    name = models.CharField(max_length=256, verbose_name='Имя переменной')
    value = models.CharField(max_length=512, null=True, blank=True, verbose_name='Значение переменной')
    flag = models.BooleanField(default=False, verbose_name='Флаг переменной')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    permissions = models.CharField(max_length=32, verbose_name='Разрешения', blank=True, null=True)

    def __str__(
            self): return f'{self.title}  {self.name} - {self.value} - [{self.flag}] -- ({self.time}:{self.date})'

    class Meta:
        verbose_name = "Переменная"
        verbose_name_plural = "Переменные"
        ordering = ['title',]

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
