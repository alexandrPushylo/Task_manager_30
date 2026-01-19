import enum

from django.core.cache import cache

from dashboard.models import ApplicationMaterial
from django.db.models import QuerySet  # type: ignore

from dashboard.schemas.application_material_schema import (
    ApplicationMaterialSchema,
    EditApplicationMaterialSchema,
)
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class ApplicationMaterialService(BaseService):
    model = ApplicationMaterial
    schema = ApplicationMaterialSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        APP_MAT_FOR_DATE = "app_mat_for_date"

    @classmethod
    def get_object(cls, *args, **kwargs) -> ApplicationMaterial | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_object({kwargs}): ApplicationMaterial.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_object({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[ApplicationMaterial]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def create(
            cls,
            app_material_data: EditApplicationMaterialSchema
    ) -> ApplicationMaterial | None:
        try:
            am = cls.model.objects.create(**app_material_data.model_dump())
            return am
        except ValueError:
            log.warning(f"create_application_material(): ValueError")
            return None

    @classmethod
    def is_exist(cls, *args, **kwargs) -> bool:
        am = cls.get_queryset(*args, **kwargs)
        return am.exists()

    @classmethod
    def get_app_mat_for_date(
        cls, workday_data: WorkDaySchema
    ) -> list[ApplicationMaterialSchema]:
        cache_key = f"{cls.CacheKeys.APP_MAT_FOR_DATE.value}:{workday_data.date}"
        cache_ttl = 60 * 60

        app_mat_for_cache = cache.get(cache_key) if cls.USE_CACHE else None
        if app_mat_for_cache is None:
            app_mat = cls.get_queryset(
                application_today__date_id=workday_data.id, isArchive=False
            )
            app_mat_data = [cls.schema(**am.to_dict()) for am in app_mat]
            if cls.USE_CACHE:
                cache.set(cache_key, app_mat_for_cache, cache_ttl)
            return app_mat_data
        else:
            cache.touch(cache_key, cache_ttl)
            return app_mat_for_cache

    @classmethod
    def get_app_mat_by_at_id_from_data(
        cls, app_today_id: int, data: list[ApplicationMaterialSchema]
    ) -> ApplicationMaterialSchema | None:
        for am in data:
            if am.application_today == app_today_id:
                return am
        return None
