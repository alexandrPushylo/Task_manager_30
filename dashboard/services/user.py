import enum

from django.core.cache import cache
from django.db.utils import IntegrityError
from django.db.models import Q


from dashboard.models import User

import dashboard.assets as A
from django.db.models import QuerySet  # type: ignore

from dashboard.schemas.user_schema import UserSchema, EditUserSchema
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class UserService(BaseService):
    model = User
    schema = UserSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        CURRENT_USER = "current_user"
        ALL_USER_LIST = "all_user_list"

    @classmethod
    def get_object(cls, *args, **kwargs) -> User | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_user({kwargs}): User.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_user({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[User]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_users_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def get_current_user(cls, user_id) -> UserSchema | None:
        cache_key = f"{cls.CacheKeys.CURRENT_USER.value}:{user_id}"
        cache_ttl = 60 * 60

        current_user_from_cache: UserSchema | None = cache.get(cache_key)
        cache.touch(cache_key, cache_ttl)
        if current_user_from_cache is None:
            current_user = cls.get_object(id=user_id)
            current_user_data = UserSchema(**current_user.to_dict())
            if cls.USE_CACHE:
                cache.set(cache_key, current_user_data, cache_ttl)
            return current_user_data
        return current_user_from_cache

    @classmethod
    def create(cls, user_data: EditUserSchema) -> tuple[User | None, A.UserEditResult]:
        validated_user_data = cls._prepare_user_data(user_data)
        if validated_user_data is None:
            return None, A.UserEditResult.ERROR
        try:
            new_user = cls.model.objects.create(**validated_user_data.model_dump())
            cache.delete(cls.CacheKeys.ALL_USER_LIST.value)
            log.info(f"User {validated_user_data.last_name} has been added")
            return new_user, A.UserEditResult.OK
        except IntegrityError:
            log.error("create_new_user(): IntegrityError; | username= [{validated_user_data.username}]")
            return None, A.UserEditResult.EXISTS
        except Exception as e:
            log.error("create_new_user(): Unexpected error", e)
            return None, A.UserEditResult.ERROR

    @classmethod
    def edit(cls, user_id: int, user_data: EditUserSchema) -> tuple[User | None, A.UserEditResult]:
        validate_data = cls._prepare_user_data(user_data)
        if validate_data is None:
            return None, A.UserEditResult.ERROR
        user = cls.get_object(pk=user_id)
        if user:
            user.username = validate_data.username
            user.first_name = validate_data.first_name
            user.last_name = validate_data.last_name
            user.telephone = validate_data.telephone
            if validate_data.password != user.password:
                user.set_password(validate_data.password)
            user.post = validate_data.post
            user.supervisor_user_id = validate_data.supervisor_user_id
            user.save()
            cache.delete(cls.CacheKeys.ALL_USER_LIST.value)
            cache.delete(f"{cls.CacheKeys.CURRENT_USER.value}:{user_id}")
            log.info(f"User {user.last_name} {user.first_name} has been edit")
            return user, A.UserEditResult.OK
        return None, A.UserEditResult.ERROR

    @classmethod
    def delete(cls, *args, **kwargs) -> bool:
        user = cls.get_object(*args, **kwargs)
        if user:
            user.isArchive = True
            user.save(update_fields=["isArchive"])
            cache.delete(cls.CacheKeys.ALL_USER_LIST.value)
            cache.delete(f"{cls.CacheKeys.CURRENT_USER.value}:{user.pk}")
            log.info(f'User: ({user.last_name} {user.first_name}) has been archived')
            return True
        return False

    @classmethod
    def get_user_by_phone(cls, telephone: str) -> User | None:
        """
            Проверка существования пользователя с телефоном "telephone"
            :param telephone:
            :return:
            """
        validate_telephone = cls.validate_telephone(telephone, length=7, use_pref=False)
        if validate_telephone:
            user = cls.get_queryset(
                isArchive=False, telephone__contains=validate_telephone
            )
        else:
            user = cls.model.objects.none()
        if user.exists() and user.count() == 1:
            return user.first()
        else:
            return None

    @classmethod
    def _prepare_user_data(cls, user_data: EditUserSchema) -> EditUserSchema | None:
        log.info("Проверка user_data")
        username = user_data.username
        first_name = str(user_data.first_name).strip().capitalize()
        last_name = str(user_data.last_name).strip().capitalize()
        raw_telephone = user_data.telephone
        password = user_data.password
        post = user_data.post if user_data.post is not None else A.UserPosts.EMPLOYEE.title
        supervisor_user_id = int(user_data.supervisor_user_id) if user_data.supervisor_user_id is not None else None

        telephone = cls.validate_telephone(raw_telephone)

        if all((username, first_name, last_name, password)):
            log.info("Data: (username, first_name, last_name, password) is Ok")
            return EditUserSchema(
                username=username,
                first_name=first_name,
                last_name=last_name,
                telephone=telephone,
                password=password,
                post=post,
                supervisor_user_id=supervisor_user_id,
            )
        else:
            log.error("Error with data: (username, first_name, last_name, password) during verification")
            return None

    @classmethod
    def is_exists(cls, user_data: EditUserSchema) -> bool:
        user_is_exists = cls.get_queryset(
            Q(username=user_data.username)
            | Q(telephone__isnull=False, telephone=user_data.telephone)
            | Q(first_name=user_data.first_name, last_name=user_data.last_name)
        ).exists()
        return user_is_exists

    @classmethod
    def validate_telephone(cls, telephone: str, length=9, use_pref=True) -> str | None:
        """
        Валидация номера телефона
        :param use_pref:
        :param length:
        :param telephone:
        :return:
        """
        if telephone:
            pref = "+375"
            out = [sym for sym in telephone if sym in "0123456789"]
            out = "".join(out)

            if len(out) >= length:
                if use_pref:
                    return pref + out[-length:]
                else:
                    return out[-length:]
            else:
                return None
        return None

    @classmethod
    def get_driver_list(cls) -> list[UserSchema | None]:
        all_users_list = cls.get_all_users_list()
        if all_users_list:
            driver_list_data = [user for user in all_users_list if user.post == A.UserPosts.DRIVER.title]
            return driver_list_data
        return []

    @classmethod
    def get_foreman_list(cls) -> list[UserSchema | None]:
        all_users_list = cls.get_all_users_list()
        if all_users_list:
            foreman_list_data = [user for user in all_users_list if user.post == A.UserPosts.FOREMAN.title]
            return foreman_list_data
        return []

    @classmethod
    def get_all_users_list(cls) -> list[UserSchema | None]:
        cache_key = f"{cls.CacheKeys.ALL_USER_LIST.value}"
        cache_ttl = 60 * 60

        all_users_list_from_cache = cache.get(cache_key)
        if all_users_list_from_cache is None:
            all_users_list = cls.get_queryset(isArchive=False)
            all_users_list_data = [UserSchema(**user.to_dict()) for user in all_users_list]
            if cls.USE_CACHE:
                cache.set(cache_key, all_users_list_data, cache_ttl)
            return all_users_list_data
        else:
            cache.touch(cache_key, cache_ttl)
            return all_users_list_from_cache

    @classmethod
    def filter_user_by_id_from_data(cls, user_id: int, data: list[UserSchema]) -> UserSchema | None:
        for user in data:
            if user.id == user_id:
                return user
        return None
