from django.core.handlers.wsgi import WSGIRequest  # type: ignore

from dashboard.types import Any

from dashboard.models import Technic, User, WorkDaySheet, TechnicSheet
from dashboard.models import TemplateDescForTechnic
import dashboard.assets as ASSETS
from django.db.models import QuerySet  # type: ignore
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
    out: dict[str, Any] = {}
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


def add_or_edit_technic(data: WSGIRequest.POST, technic_id=None):
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
        return Technic.objects.none()
    except ValueError:
        log.error("get_technic(): ValueError")
        return Technic.objects.none()


def get_supply_technic_list() -> QuerySet[Technic]:
    """
    Получить список техники для supply
    :return: Technic.objects.filter()
    """
    technic_list = get_technics_queryset(isArchive=False, supervisor_technic=ASSETS.UserPosts.SUPPLY.title)
    return technic_list


def get_dict_short_technic_names(technic_sheets: QuerySet[TechnicSheet]):
    """
        Получить dict {короткое название техники: название техники}
        :param technic_sheets:
        :return:
        """
    technic_titles_list = technic_sheets.values_list('technic__title', flat=True).distinct()
    out = []
    for title in technic_titles_list:
        out.append({
            'title': title,
            'short_title': str(title).replace(' ', '').replace('.', ''),
            'status_busies_list': list(technic_sheets.filter(technic__title=title).values_list('count_application', flat=True))
        })
    return out



def get_description_mode_for_spec_app(technic_id) -> str | ASSETS.TaskDescriptionMode:
    """
    Получить шаблон описания для "спец объекта" с помощью technic_id.
    :param technic_id:
    :return:
    """
    if technic_id:
        try:
            template_description = TemplateDescForTechnic.objects.get(technic__id=technic_id)
            if template_description.is_default_mode:
                return ASSETS.TaskDescriptionMode.DEFAULT
            elif template_description.is_auto_mode:
                return ASSETS.TaskDescriptionMode.AUTO
            elif all((not template_description.is_auto_mode, not template_description.is_default_mode)):
                return ASSETS.TaskDescriptionMode.MANUAL
            else:
                return ''
        except TemplateDescForTechnic.DoesNotExist:
            log.warning('TemplateDescForTechnic.DoesNotExist')


def get_task_description_queryset(select_related: tuple = (),
                          order_by: tuple = (),
                          **kwargs) -> QuerySet[TemplateDescForTechnic]:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """
    description = TemplateDescForTechnic.objects.filter(**kwargs)

    if select_related:
        description = description.select_related(*select_related)
    if order_by:
        description = description.order_by(*order_by)
    return description


def get_task_description(**kwargs) -> TemplateDescForTechnic:
    try:
        description = TemplateDescForTechnic.objects.get(**kwargs)
        return description
    except TemplateDescForTechnic.DoesNotExist:
        log.error("get_task_description(): TemplateDescForTechnic.DoesNotExist ")
        return TemplateDescForTechnic.objects.none()
    except ValueError:
        log.error("get_task_description(): ValueError")
        return TemplateDescForTechnic.objects.none()


def set_task_description(technic_id, type_mode: ASSETS.TaskDescriptionMode, description: str|None):
    """
    Установить шаблон задания для "спец объекта" с помощью technic_id.
    :param technic_id:
    :param type_mode:
    :param description:
    :return:
    """
    task_description = get_task_description(technic=technic_id)
    if not task_description:
        task_description = TemplateDescForTechnic()
        task_description.technic_id = technic_id
    match type_mode:
        case ASSETS.TaskDescriptionMode.AUTO.value:
            task_description.is_auto_mode = True
            task_description.is_default_mode = False
            task_description.save()
        case ASSETS.TaskDescriptionMode.DEFAULT.value:
            task_description.is_auto_mode = False
            task_description.is_default_mode = True
            task_description.save()
        case ASSETS.TaskDescriptionMode.MANUAL.value:
            task_description.is_auto_mode = False
            task_description.is_default_mode = False
            task_description.description = description if description is not None else ''
            task_description.save()
        case _:
            log.warning('type_mode не валиден set_task_description')



