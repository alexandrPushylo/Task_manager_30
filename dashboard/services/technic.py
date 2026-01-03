import enum

from django.core.handlers.wsgi import WSGIRequest  # type: ignore
from django.core.cache import cache

from config.settings import USE_CACHE
from dashboard.schemas.template_description_schema import TemplateDescriptionSchema
from dashboard.services.base import BaseService
from dashboard.types import Any

from dashboard.models import Technic, User, TechnicSheet
from dashboard.models import TemplateDescForTechnic
import dashboard.assets as ASSETS
from django.db.models import QuerySet  # type: ignore
from dashboard.schemas.technic_schema import (
    TechnicSchema,
    EditTechnicSchema,
    ShortTechnicDataSchema,
)

from logger import getLogger

log = getLogger(__name__)


class TechnicService(BaseService):
    model = Technic
    schema = TechnicSchema
    CACHE_TTL = 10
    USE_CACHE = USE_CACHE

    class CacheKeys(enum.Enum):
        TECHNIC_TYPE_LIST = "technic_type_list"
        ALL_TECHNIC_LIST = "all_technic_list"
        DISTINCT_TECH_TITLE = "distinct_tech_title"

    @classmethod
    def get_object(cls, *args, **kwargs) -> Technic | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_technic({kwargs}): Technic.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_technic({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[Technic]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_technics_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def create(cls, technic_data: EditTechnicSchema) -> Technic | None:
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
        if cls.USE_CACHE:
            cache.delete(cls.CacheKeys.ALL_TECHNIC_LIST.value)
            cache.delete(cls.CacheKeys.DISTINCT_TECH_TITLE.value)
            cache.delete(cls.CacheKeys.TECHNIC_TYPE_LIST.value)
        return new_technic

    @classmethod
    def edit(cls, technic_id:int, technic_data: EditTechnicSchema) -> bool:
        validate_data = cls._prepare_technic_data(technic_data)
        if validate_data is None:
            return False
        technic = cls.get_object(pk=technic_id)
        if technic:
            technic.title = validate_data.title
            technic.type = validate_data.type
            technic.attached_driver_id = validate_data.attached_driver
            technic.supervisor_technic = validate_data.supervisor_technic
            technic.id_information = validate_data.id_information
            technic.description = validate_data.description
            technic.save()
            log.info(f"Technic {validate_data.title} [{validate_data.id_information}] has been edit")
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.ALL_TECHNIC_LIST.value)
                cache.delete(cls.CacheKeys.DISTINCT_TECH_TITLE.value)
                cache.delete(cls.CacheKeys.TECHNIC_TYPE_LIST.value)
            return True
        return False

    @classmethod
    def delete(cls, *args, **kwargs) -> Technic | bool:
        technic = cls.get_object(*args, **kwargs)
        if technic:
            technic.isArchive = True
            technic.save(update_fields=["isArchive"])
            log.info(f"Technic {technic.title} [{technic.id_information}] был помещена в архив")
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.ALL_TECHNIC_LIST.value)
                cache.delete(cls.CacheKeys.DISTINCT_TECH_TITLE.value)
                cache.delete(cls.CacheKeys.TECHNIC_TYPE_LIST.value)
            return technic
        return False

    @classmethod
    def get_supply_technic_list(cls) -> list[TechnicSchema] | None:
        """
        ////Получить список техники для supply
        :return: list[TechnicSchema] | None
        """
        all_technic_data = cls.get_all_technic_data()
        if all_technic_data:
            supply_technic_list_data = [
                technic
                for technic in all_technic_data
                if technic.supervisor_technic == ASSETS.UserPosts.SUPPLY.title
            ]
            return supply_technic_list_data
        return None

    @classmethod
    def get_technic_type_list(cls) -> list[str]:
        """
        USE CACHE
        Получить список всех типов техники
        """
        cache_keys = f"{cls.CacheKeys.TECHNIC_TYPE_LIST.value}"
        cache_ttl = 60 * 60
        technic_type_list_from_cache: list[str] = cache.get(cache_keys)
        if technic_type_list_from_cache is None:
            technic_type_list = sorted(
                set(
                    cls.model.objects.filter().values_list('type', flat=True)
                )
            )
            if cls.USE_CACHE:
                cache.set(cache_keys, technic_type_list, cache_ttl)
            return technic_type_list
        else:
            cache.touch(cache_keys, cache_ttl)
            return technic_type_list_from_cache

    @classmethod
    def get_short_title(cls, title: str) -> str:
        """
        Получить short_title для technic title
        :param title:
        :return:
        """
        return title.replace(" ", "").replace(".", "")

    @classmethod
    def get_distinct_tech_title_from_ts(cls, technic_sheets_instance: QuerySet[TechnicSheet]) -> set:
        """
        :param technic_sheets_instance:
        :return: technic_sheets.values_list('technic__title', flat=True).distinct()
        """
        # distinct_technic_titles_list = []
        technic_titles_list = technic_sheets_instance.values_list("technic__title", flat=True)
        return set(technic_titles_list)

        # for item in technic_titles_list:
        #     if item not in distinct_technic_titles_list:
        #         distinct_technic_titles_list.append(item)
        # return distinct_technic_titles_list

    @classmethod
    def get_dict_short_technic_names(
            cls,
            technic_sheets_instance: QuerySet[TechnicSheet]
    ) -> list[ShortTechnicDataSchema]:
        """
        Получить dict {короткое название техники: название техники}
        :param technic_sheets_instance:
        :return:
        """
        distinct_technic_titles_list = cls.get_distinct_tech_title_from_ts(technic_sheets_instance)
        out: list[ShortTechnicDataSchema] = []

        for title in distinct_technic_titles_list:
            out.append(
                ShortTechnicDataSchema(
                    title=title,
                    short_title=cls.get_short_title(title),
                    status_busies_list=list(
                        technic_sheets_instance.filter(
                            technic__title=title).values_list("count_application", flat=True
                        )
                    )
                )
            )
        return out

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

    @classmethod
    def get_all_technic_data(cls) -> list[TechnicSchema | None]:
        cache_key = f"{cls.CacheKeys.ALL_TECHNIC_LIST.value}"
        cache_ttl = 60 * 60
        technic_list_from_cache: list[TechnicSchema | None] = cache.get(cache_key)
        if technic_list_from_cache is None:
            technic_list = cls.get_queryset(isArchive=False)
            technic_list_data = [TechnicSchema(**t.to_dict()) for t in technic_list]
            if cls.USE_CACHE:
                cache.set(cache_key, technic_list_data, cache_ttl)
            return technic_list_data
        else:
            cache.touch(cache_key, cache_ttl)
            return technic_list_from_cache

    @classmethod
    def get_distinct_technic_title(cls) -> list[str]:
        cache_key = f"{cls.CacheKeys.DISTINCT_TECH_TITLE.value}"
        cache_ttl = 60 * 60
        tech_list_from_cache = cache.get(cache_key)
        if tech_list_from_cache is None:
            tech_list = cls.get_queryset(isArchive=False).values_list('title', flat=True)
            tech_list_data = sorted(set(tech_list))
            if cls.USE_CACHE:
                cache.set(cache_key, tech_list_data, cache_ttl)
            return tech_list_data
        else:
            cache.touch(cache_key, cache_ttl)
            return tech_list_from_cache

    @classmethod
    def filter_technic_by_id(
        cls, technic_id: int, technic_list: list[TechnicSchema]
    ) -> TechnicSchema | None:
        for technic in technic_list:
            if technic.id == technic_id:
                return technic
        return None


class TemplateDescService(BaseService):
    model = TemplateDescForTechnic
    schema = TemplateDescriptionSchema

    class CacheKeys(enum.Enum):
        pass

    @classmethod
    def get_object(cls, *args, **kwargs) -> TemplateDescForTechnic | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_object({kwargs}): TemplateDescForTechnic.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_object({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[TemplateDescForTechnic]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def set_task_description(
            cls,
            technic_id: int,
            type_mode: ASSETS.TaskDescriptionMode,
            description: str | None
    ):
        """
        Установить шаблон задания для "спец объекта" с помощью technic_id.
        :param technic_id:
        :param type_mode:
        :param description:
        :return:
        """
        task_description = cls.get_object(technic=technic_id)
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
                task_description.description = (
                    description if description is not None else ""
                )
                task_description.save()
            case _:
                log.warning(
                    f"type_mode - ({type_mode}) is not valid set_task_description()"
                )

    @classmethod
    def get_description_mode_for_spec_app(
            cls,
            technic_id: int,
    ) -> str | ASSETS.TaskDescriptionMode:
        """
        Получить шаблон описания для "спец объекта" с помощью technic_id.
        :param technic_id:
        :return:
        """

        templ_desc = cls.get_object(technic__id=technic_id)
        if templ_desc:
            if templ_desc.is_default_mode:
                return ASSETS.TaskDescriptionMode.DEFAULT
            elif templ_desc.is_auto_mode:
                return ASSETS.TaskDescriptionMode.AUTO
            elif all((not templ_desc.is_auto_mode, not templ_desc.is_default_mode)):
                return ASSETS.TaskDescriptionMode.MANUAL
            else:
                return ""
        return ""
