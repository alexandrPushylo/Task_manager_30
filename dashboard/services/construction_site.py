import enum

from django.core.cache import cache

from dashboard.models import ConstructionSite
from dashboard.schemas.construction_site_schema import ConstructionSiteSchema, EditConstructionSiteSchema
from django.db.models import QuerySet  # type: ignore

import dashboard.utilities as U
import dashboard.assets as A
from dashboard.services.base import BaseService

from logger import getLogger

log = getLogger(__name__)


class ConstructionSiteService(BaseService):
    model = ConstructionSite
    schema = ConstructionSiteSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        CS_ACTIVE_LIST = "cs_active_list"
        CS_DELETED_LIST = "cs_deleted_list"
        CS_FOR_SUPPLY = "cs_for_supply"

    @classmethod
    def get_object(cls, *args, **kwargs) -> ConstructionSite | None:
        try:
            obj = cls.model.objects.get(**kwargs)
            return obj
        except ConstructionSite.DoesNotExist:
            log.warning(f"get_construction_sites({kwargs}): DoesNotExist")
            return None
        except ValueError:
            log.error(f"get_construction_sites({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[ConstructionSite]:
        """
        :param kwargs:
        :return:
        """
        try:
            queryset = cls.model.objects.filter(**kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_construction_site_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def hide_or_show(cls, *args, **kwargs) -> bool:
        cs = cls.get_object(*args, **kwargs)
        if cs:
            if cs.status:
                cs.status = False
                log.info(f"The construction site (pk={cs.pk}) was hidden")
            else:
                cs.status = True
                log.info(f"The construction site (pk={cs.pk}) was displayed")
            cs.save(update_fields=["status"])
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.CS_ACTIVE_LIST.value)
            return True
        return False

    @classmethod
    def delete(cls, *args, **kwargs) -> ConstructionSite | None:
        cs = cls.get_object(*args, **kwargs)
        if cs:
            if cs.isArchive:
                cs.isArchive = False
                cs.deleted_date = None
                log.info(
                    f"The {cs.address} construction site (pk={cs.pk}) has been restored from the archive"
                )
            else:
                cs.isArchive = True
                cs.deleted_date = cls.TODAY
                log.info(
                    f"The {cs.address} construction site  (pk={cs.pk}) has been archived"
                )
            cs.save(update_fields=["isArchive", "deleted_date"])
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.CS_ACTIVE_LIST.value)
                cache.delete(cls.CacheKeys.CS_DELETED_LIST.value)
            return cs
        return None

    @classmethod
    def _check_data(cls, data: EditConstructionSiteSchema) -> EditConstructionSiteSchema | None:
        if data.address:
            return data
        else:
            return None

    @classmethod
    def create(cls, data: EditConstructionSiteSchema) -> bool:
        prepared_data = cls._check_data(data)
        if prepared_data:
            cls.model.objects.create(
                address=prepared_data.address,
                foreman_id=prepared_data.foreman
            )
            log.info("The %s CS has been created" % prepared_data.address)
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.CS_ACTIVE_LIST.value)
            return True
        else:
            return False

    @classmethod
    def edit(cls, constr_site_id: int, data: EditConstructionSiteSchema) -> bool:
        prepared_data = cls._check_data(data)
        if prepared_data:
            cs = cls.model.objects.get(id=constr_site_id)
            if cs:
                cs.address = prepared_data.address
                cs.foreman_id = prepared_data.foreman
                cs.save(update_fields=["address", "foreman"])
                log.info("The %s CS has been changed" % data.address)
                if cls.USE_CACHE:
                    cache.delete(cls.CacheKeys.CS_ACTIVE_LIST.value)
                return True
        return False

    @classmethod
    def restore_if_was_deleted(cls, data: EditConstructionSiteSchema) -> bool:
        """
        Восстановление объекта в рабочее состояние
        :param data:
        :return:
        """
        cs = cls.get_object(
            address=data.address,
            foreman_id=data.foreman,
        )
        if cs:
            cs.isArchive = False
            cs.status = True
            cs.deleted_date = None
            cs.save()
            log.info("The %s CS has been restored" % data.address)
            if cls.USE_CACHE:
                cache.delete(cls.CacheKeys.CS_ACTIVE_LIST.value)
                cache.delete(cls.CacheKeys.CS_DELETED_LIST.value)
            return True
        return False

    @classmethod
    def is_exist(cls, data: EditConstructionSiteSchema) -> bool:
        is_exist = cls.model.objects.filter(
            address=data.address,
            foreman=data.foreman,
        ).exists()
        return is_exist

    @classmethod
    def get_active_cs_list(cls) -> list[ConstructionSiteSchema]:
        cache_key = f"{cls.CacheKeys.CS_ACTIVE_LIST.value}"
        cache_ttl = 60 * 60
        cs_list_from_cache = cache.get(cache_key)
        if cs_list_from_cache is None:
            cs_list = cls.get_queryset(isArchive=False).order_by("address")
            cs_list_data = [ConstructionSiteSchema(**cs.to_dict()) for cs in cs_list]
            if cls.USE_CACHE:
                cache.set(cache_key, cs_list_data, cache_ttl)
            return cs_list_data
        else:
            cache.touch(cache_key, cache_ttl)
            return cs_list_from_cache


    @classmethod
    def get_showed_cs_list(cls) -> list[ConstructionSiteSchema]:
        return [cs for cs in cls.get_active_cs_list() if cs.status == True]


    @classmethod
    def get_hidden_cs_list(cls) -> list[ConstructionSiteSchema]:
        return [cs for cs in cls.get_active_cs_list() if cs.status == False]

    @classmethod
    def get_deleted_cs_list(cls) -> list[ConstructionSiteSchema]:
        cache_key = f"{cls.CacheKeys.CS_DELETED_LIST.value}"
        cache_ttl = 60 * 60
        cs_list_from_cache = cache.get(cache_key)
        if cs_list_from_cache is None:
            cs_list = cls.get_queryset(isArchive=True).order_by("address")
            cs_list_data = [ConstructionSiteSchema(**cs.to_dict()) for cs in cs_list]
            if cls.USE_CACHE:
                cache.set(cache_key, cs_list_data, cache_ttl)
            return cs_list_data
        else:
            cache.touch(cache_key, cache_ttl)
            return cs_list_from_cache

    @classmethod
    def get_spec_construction_site(cls) -> ConstructionSite | None:
        cs = cls.get_object(address=A.MessagesAssets.CS_SPEC_TITLE.value)
        if cs:
            return cs
        else:
            log.error("The SPEC construction site does not exist")
            return None


    @classmethod
    def get_construction_site_for_supply(cls) -> ConstructionSiteSchema:
        cache_key = f"{cls.CacheKeys.CS_FOR_SUPPLY.value}"
        cache_ttl = 60 * 60
        cs_from_cache = cache.get(cache_key)
        if cs_from_cache is None:
            cs = cls.get_object(address=A.MessagesAssets.CS_SUPPLY_TITLE.value)
            if not cs:
                log.error("The SPEC construction site does not exist")
            cs_data = cls.schema(**cs.to_dict())
            if cls.USE_CACHE:
                cache.set(cache_key, cs_data, cache_ttl)
            return cs_data
        else:
            cache.touch(cache_key, cache_ttl)
            return cs_from_cache