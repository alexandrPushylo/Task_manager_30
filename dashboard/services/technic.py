import enum

from django.core.handlers.wsgi import WSGIRequest  # type: ignore
from django.core.cache import cache

from config.settings import USE_CACHE
from dashboard.types import Any

from dashboard.models import Technic, User, TechnicSheet
from dashboard.models import TemplateDescForTechnic
import dashboard.assets as ASSETS
import dashboard.utilities as U
from django.db.models import QuerySet  # type: ignore
from dashboard.schemas.technic_schema import TechnicSchema, EditTechnicSchema

from logger import getLogger

log = getLogger(__name__)


class TechnicService:
    model = Technic
    schema = TechnicSchema
    CACHE_TTL = 10
    USE_CACHE = USE_CACHE

    class CacheKeys(enum.Enum):
        TECH_LIST_FOR_SUPPLY = "technic_list_for_supply"
        TECHNIC_TYPE_LIST = "technic_type_list"

    @classmethod
    def get_technic(cls, *args, **kwargs) -> Technic | None:
        try:
            technic = cls.model.objects.get(*args, **kwargs)
            return technic
        except cls.model.DoesNotExist:
            log.warning(f"get_technic({kwargs}): Technic.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_technic({kwargs}): ValueError")
            return None

    @classmethod
    def get_technics_queryset(cls, *args, **kwargs) -> QuerySet[Technic]:
        try:
            technic = cls.model.objects.filter(*args, **kwargs)
            return technic
        except ValueError:
            log.warning(f"get_technics_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def add_new_technic(cls, technic_data: EditTechnicSchema) -> Technic | None:
        validate_data = cls._prepare_technic_data(technic_data)
        if validate_data is None:
            return None
        new_technic = cls.model.objects.create(
            title=validate_data.title,
            type=validate_data.type,
            id_information=validate_data.id_information,
            description=validate_data.description,
            attached_driver_id=validate_data.attached_driver,
            supervisor_technic=validate_data.supervisor_technic
        )
        return new_technic

    @classmethod
    def edit_technic(cls, technic_id:int, technic_data: EditTechnicSchema) -> bool:
        validate_data = cls._prepare_technic_data(technic_data)
        if validate_data is None:
            return False
        technic = cls.get_technic(pk=technic_id)
        if technic:
            technic.title = validate_data.title
            technic.type = validate_data.type
            technic.attached_driver_id = validate_data.attached_driver
            technic.supervisor_technic = validate_data.supervisor_technic
            technic.id_information = validate_data.id_information
            technic.description = validate_data.description
            technic.save()
            log.info(f"Technic {validate_data.title} [{validate_data.id_information}] has been edit")
            return True
        return False

    @classmethod
    def delete_technic(cls, *args, **kwargs) -> bool:
        technic = cls.get_technic(*args, **kwargs)
        if technic:
            technic.isArchive = True
            technic.save(update_fields=["isArchive"])
            log.info(f"Technic {technic.title} [{technic.id_information}] был помещена в архив")
            return True
        return False

    @classmethod
    def get_supply_technic_list(cls, *args, **kwargs) -> list[TechnicSchema] | None:
        """
        USE CACHE
        Получить список техники для supply
        :return: list[TechnicSchema] | None
        """
        supply_technic_list_from_cache: list[TechnicSchema] | None = cache.get(cls.CacheKeys.TECH_LIST_FOR_SUPPLY)
        if supply_technic_list_from_cache is None:
            supply_technic_list: QuerySet[Technic] = cls.get_technics_queryset(
                isArchive=False,
                supervisor_technic=ASSETS.UserPosts.SUPPLY.title
            )
            supply_technic_list_data = [TechnicSchema(**technic.to_dict()) for technic in supply_technic_list]
            if cls.USE_CACHE:
                cache.set(cls.CacheKeys.TECH_LIST_FOR_SUPPLY, supply_technic_list_data, cls.CACHE_TTL)
            return supply_technic_list_data
        return supply_technic_list_from_cache

    @classmethod
    def get_technic_type_list(cls, *args, **kwargs) -> list[str]:
        """
        USE CACHE
        Получить список всех типов техники
        """
        technic_type_list_from_cache: list[str] = cache.get(cls.CacheKeys.TECHNIC_TYPE_LIST)
        if technic_type_list_from_cache is None:
            technic_type_list = sorted(
                set(
                    cls.model.objects.filter().values_list('type', flat=True)
                )
            )
            if cls.USE_CACHE:
                cache.set(cls.CacheKeys.TECHNIC_TYPE_LIST, technic_type_list, cls.CACHE_TTL)
            return technic_type_list
        return technic_type_list_from_cache

    @classmethod
    def _prepare_technic_data(cls, technic_data: EditTechnicSchema) -> EditTechnicSchema | None:
        out: dict[str, Any] = {}
        log.info("Check technic_data")

        title = technic_data.title
        technic_type = technic_data.type
        id_information = technic_data.id_information
        description = technic_data.description
        supervisor_technic = technic_data.supervisor_technic
        attached_driver = technic_data.attached_driver

        if supervisor_technic not in (ASSETS.UserPosts.MECHANIC.title, ASSETS.UserPosts.SUPPLY.title):
            out["supervisor"] = ASSETS.UserPosts.MECHANIC.title

        if attached_driver:
            try:
                # driver = User.objects.get(id=attached_driver) #TODO REF
                out['attached_driver'] = attached_driver
            except User.DoesNotExist:
                log.warning(f"Attached driver id={attached_driver} does not exist")
                out["attached_driver"] = None
        else:
            out["attached_driver"] = None

        if all((title, technic_type, id_information)):
            log.info(f"Data: (title, tech_type, id_information) is OK")
            out["title"] = title.strip()
            out["type"] = technic_type
            out["id_information"] = id_information
            out["description"] = description
            out["supervisor_technic"] = supervisor_technic
            return EditTechnicSchema(**out)
        else:
            return None


### -----------------------------------------------------------------------------------

# def create_new_technic(data: dict):  ####
#     technic = Technic.objects.create(
#         title=data['title'],
#         type=data['type'],
#         attached_driver=data['attached_driver'],
#         supervisor_technic=data['supervisor'],
#         id_information=data['id_information'],
#         description=data['description']
#     )
#     log.info(f'Technic: %s [%s] has been added' % (technic.title, technic.id_information))


# def edit_technic(technic_id, data: dict):####
#     try:
#         technic = Technic.objects.get(pk=technic_id)
#         technic.title = data['title']
#         technic.type = data['type']
#         technic.attached_driver = data['attached_driver']
#         technic.supervisor_technic = data['supervisor']
#         technic.id_information = data['id_information']
#         technic.description = data['description']
#         technic.save()
#         log.info('Technic %s [%s] has been edit' % (technic.title, technic.id_information))
#     except Technic.DoesNotExist:
#         log.warning('Technic id=%s does not exist' % technic_id)


# def check_technic_data(data: dict) -> dict | None:####
#     out: dict[str, Any] = {}
#     log.info('Check technic_data')
#     title = data.get('title')
#     tech_type = data.get('type')
#     id_information = data.get('id_information')
#     description = data.get('description')
#     attached_driver = data.get('attached_driver')
#     supervisor = data.get('supervisor')
#
#     if supervisor not in (ASSETS.UserPosts.MECHANIC.title, ASSETS.UserPosts.SUPPLY.title):
#         out['supervisor'] = ASSETS.UserPosts.MECHANIC.title
#
#     if attached_driver:
#         try:
#             driver = User.objects.get(pk=attached_driver)
#             out['attached_driver'] = driver
#         except User.DoesNotExist:
#             log.warning('Attached driver id=%s does not exist' % attached_driver)
#             out['attached_driver'] = None
#     else:
#         out['attached_driver'] = None
#
#     if all((title, tech_type, id_information)):
#         log.info(f'Data: (title, tech_type, id_information) is OK')
#         out['title'] = title.strip()
#         out['type'] = tech_type
#         out['id_information'] = id_information
#         out['description'] = description
#         out['supervisor'] = supervisor
#         return out
#     else:
#         log.warning('Error with the data: (title, tech_type, id_information) when checking')
#         return None


# def add_or_edit_technic(data: WSGIRequest.POST, technic_id=None):
#     prepare_data = check_technic_data(data)
#     if technic_id:
#         if prepare_data:
#             edit_technic(technic_id, prepare_data)
#         else:
#             log.error('Error with the "technic_data" data when edit technic')
#     else:
#         if prepare_data:
#             create_new_technic(prepare_data)
#         else:
#             log.error('Error with the "technic_data" data when creating technic')


# def delete_technic(technic_id):###
#     try:
#         technic = Technic.objects.get(pk=technic_id)
#         technic.isArchive = True
#         technic.save(update_fields=['isArchive'])
#         log.info('Technic %s [%s] был помещена в архив' % (technic.title, technic.id_information))
#         return technic
#     except Technic.DoesNotExist:
#         log.warning('Technic id=%s does not exist' % technic_id)
#         return None


def get_technics_queryset(###
        # select_related: tuple = (),
        #                   order_by: tuple = (),
                          *args,
                          **kwargs) -> list[TechnicSchema | None]:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """
    cache_key = U.validate_cache_name(f"get_technics_queryset:{args},{kwargs}")
    cache_timeout = 10

    cache_technics: list[TechnicSchema | None] = cache.get(cache_key)
    if cache_technics is None:
        technics_queryset = Technic.objects.filter(*args, **kwargs)
        # if select_related:
        #     technics_queryset = technics_queryset.select_related(*select_related)
        # if order_by:
        #     technics_queryset = technics_queryset.order_by(*order_by)

        technics_data_list = [TechnicSchema(**technic.to_dict()) for technic in technics_queryset]
        cache.set(cache_key, technics_data_list, cache_timeout) if USE_CACHE else None
        return technics_data_list
    return cache_technics
    # technics = Technic.objects.filter(*args, **kwargs)
    # if select_related:
    #     technics = technics.select_related(*select_related)
    # if order_by:
    #     technics = technics.order_by(*order_by)
    # return technics


# def get_technic(*args, **kwargs) -> TechnicSchema | None:###
#     cache_key = f'get_technic:{args},{kwargs}'
#     cache_timeout = 10
#     try:
#         cache_technic: TechnicSchema | None = cache.get(cache_key)
#         if cache_technic is None:
#             technic = Technic.objects.get(*args, **kwargs)
#             technic_data = TechnicSchema(**technic.to_dict())
#             cache.set(cache_key, technic_data, cache_timeout) if USE_CACHE else None
#             return technic_data
#         return cache_technic
#     except Technic.DoesNotExist:
#         log.warning(f"get_technic({kwargs}): Technic.DoesNotExist ")
#         return None
#     except ValueError:
#         log.warning(f"get_technic({kwargs}): ValueError")
#         return None


def get_supply_technic_list() -> QuerySet[Technic]:###
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
    distinct_technic_titles_list = get_distinct_technic_title(technic_sheets)
    out = []

    for title in distinct_technic_titles_list:
        out.append({
            'title': title,
            'short_title': get_short_title(title),
            'status_busies_list': list(technic_sheets.filter(
                technic__title=title
            ).values_list('count_application', flat=True))
        })
    return out


def get_short_title(title: str) -> str:
    """
    Получить short_title для technic title
    :param title:
    :return:
    """
    return title.replace(' ', '').replace('.', '')


def get_distinct_technic_title(technic_sheets: QuerySet[TechnicSheet]) -> list:
    """
    :param technic_sheets:
    :return: technic_sheets.values_list('technic__title', flat=True).distinct()
    """
    distinct_technic_titles_list = []
    technic_titles_list = technic_sheets.values_list('technic__title', flat=True)

    for item in technic_titles_list:
        if item not in distinct_technic_titles_list:
            distinct_technic_titles_list.append(item)
    return distinct_technic_titles_list


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
        log.warning(f"get_task_description({kwargs}): TemplateDescForTechnic.DoesNotExist ")
        return TemplateDescForTechnic.objects.none()
    except ValueError:
        log.error(f"get_task_description({kwargs}): ValueError")
        return TemplateDescForTechnic.objects.none()


def set_task_description(technic_id, type_mode: ASSETS.TaskDescriptionMode, description: str | None):
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
            log.warning(f'type_mode - ({type_mode}) is not valid set_task_description()')


def get_technic_type() -> list:###
    """
    Получить список всех типов техники
    :return:
    """
    technic_types = sorted(set(Technic.objects.all().values_list('type', flat=True)))
    return technic_types
