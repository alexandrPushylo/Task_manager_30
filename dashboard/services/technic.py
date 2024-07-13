from dashboard.models import Technic, User, WorkDaySheet, TechnicSheet
import dashboard.assets as ASSETS
from django.db.models import QuerySet
import dashboard.services.user as USERS_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.dashboard as DASHBOARD_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE

from logger import getLogger

log = getLogger(__name__)


def create_new_technic(data: dict):
    technic = Technic.objects.create(
        title=data['title'],
        type=data['type'],
        attached_driver=data['attached_driver'],
        supervisor_technic=data['supervisor'],
        id_information=data['id_information'],
        description=data['description']
    )
    log.info(f'Техника {technic.title} [{technic.id_information}] была добавлена')


def edit_technic(technic_id, data: dict):
    try:
        technic = Technic.objects.get(pk=technic_id)
        technic.title = data['title']
        technic.type = data['type']
        technic.attached_driver = data['attached_driver']
        technic.supervisor_technic = data['supervisor']
        technic.id_information = data['id_information']
        technic.description = data['description']
        technic.save()
        log.info(f'Техника {technic.title} [{technic.id_information}] была изменена')
    except Technic.DoesNotExist:
        log.error(f'Техники с id={technic_id} не существует')


def check_technic_data(data: dict) -> dict | None:
    out = {}
    log.info('Проверка technic_data')
    title = data.get('title')
    tech_type = data.get('type')
    id_information = data.get('id_information')
    description = data.get('description')
    attached_driver = data.get('attached_driver')
    supervisor = data.get('supervisor')

    if supervisor not in (ASSETS.UserPosts.MECHANIC.title, ASSETS.UserPosts.SUPPLY.title):
        out['supervisor'] = ASSETS.UserPosts.MECHANIC.title

    if attached_driver:
        try:
            driver = User.objects.get(pk=attached_driver)
            out['attached_driver'] = driver
        except User.DoesNotExist:
            log.error(f'Прикрепленного водителя с id={attached_driver} не существует')
            out['attached_driver'] = None
    else:
        out['attached_driver'] = None

    if all((title, tech_type, id_information)):
        log.info(f'Данные: (title, tech_type, id_information) в порядке')
        out['title'] = title
        out['type'] = tech_type
        out['id_information'] = id_information
        out['description'] = description
        out['supervisor'] = supervisor
        return out
    else:
        log.error('Ошибка с данными: (title, tech_type, id_information) при проверке')
        return None


def add_or_edit_technic(data, technic_id=None):
    prepare_data = check_technic_data(data)
    if technic_id:
        if prepare_data:
            edit_technic(technic_id, prepare_data)
        else:
            log.error('Ошибка с данными "technic_data" при изменении техники')
    else:
        if prepare_data:
            create_new_technic(prepare_data)
        else:
            log.error('Ошибка с данными "technic_data" при создании техники')


def delete_technic(technic_id):
    try:
        technic = Technic.objects.get(pk=technic_id)
        technic.isArchive = True
        technic.save(update_fields=['isArchive'])
        log.info(f'Техника {technic.title} [{technic.id_information}] был помещена в архив')
        return technic
    except Technic.DoesNotExist:
        log.error(f'Техники с id={technic_id} не существует')
        return None


def get_technics_queryset(select_related: tuple = (),
                          order_by: tuple = (),
                          **kwargs) -> QuerySet[Technic]:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """
    technics = Technic.objects.filter(**kwargs)

    if select_related:
        technics = technics.select_related(*select_related)
    if order_by:
        technics = technics.order_by(*order_by)
    return technics


def get_technic(**kwargs) -> Technic:
    try:
        technic = Technic.objects.get(**kwargs)
        return technic
    except Technic.DoesNotExist:
        log.error("get_technic(): Technic.DoesNotExist ")
    except ValueError:
        log.error("get_technic(): ValueError")


def get_supply_technic_list() -> Technic.objects:
    """
    Получить список техники для supply
    :return: Technic.objects.filter()
    """
    technic_list = get_technics_queryset(isArchive=False, supervisor_technic=ASSETS.UserPosts.SUPPLY.title)
    return technic_list


def get_dict_short_technic_names(technic_sheets: TechnicSheet.objects) -> dict:
    technic_titles_list = technic_sheets.values_list('technic__title', flat=True).distinct()
    technic_titles_dict = {str(title).replace(' ', '').replace('.', ''): title
                           for title in technic_titles_list}
    return technic_titles_dict






