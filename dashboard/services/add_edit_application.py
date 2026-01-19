import json

from django.core.cache import cache
from django.db.models import QuerySet

from dashboard.models import TechnicSheet, ApplicationToday
from dashboard.schemas.application_material_schema import EditApplicationMaterialSchema
from dashboard.schemas.application_technic_schema import EditApplicationTechnicSchema
from dashboard.schemas.technic_schema import ShortTechnicDataSchema
from dashboard.schemas.user_schema import UserSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.application_material import ApplicationMaterialService
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.utilities import Utilities
from logger import getLogger

log = getLogger(__name__)


class EditApplicationService:

    @classmethod
    def add_technic_to_application(
            cls,
            post_technic_title_shrt: str | None,
            post_technic_sheet_id: str | None,
            post_application_technic_description: str,
            technic_titles_dict: list[ShortTechnicDataSchema],
            current_user: UserSchema,
            current_day: WorkDaySchema,
            app_today_inst: ApplicationToday,
            technic_driver_list_json: list[dict]
    ) -> dict:
        data = {
            "status": "fail",
            "app_today_id": app_today_inst.id,
            "technic_driver_list": json.dumps(
                technic_driver_list_json, ensure_ascii=False
            ),
        }
        if Utilities.is_valid_str(post_technic_title_shrt):
            if not Utilities.is_valid_str(post_technic_sheet_id):
                technic_title_dict = [
                    *filter(
                        lambda item: item.short_title == post_technic_title_shrt,
                        technic_titles_dict
                    )
                ][0]
                technic_title = technic_title_dict.title
                some_technic_sheet = TechnicSheetService.get_some_technic_sheet(
                    technic_title=technic_title, workday_sheet_id=current_day.id
                )
            else:
                some_technic_sheet = TechnicSheetService.get_object(
                    id=post_technic_sheet_id
                )
            description = (
                post_application_technic_description
                if post_application_technic_description
                else ""
            )

            create_data = EditApplicationTechnicSchema(
                application_today_id=app_today_inst.id,
                technic_sheet_id=some_technic_sheet.id,
                description=description,
            )
            application_technic = ApplicationTechnicService.create(create_data)
            cache.delete(f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{current_day.date}")
            if some_technic_sheet:
                TechnicSheetService.increment_count_application(some_technic_sheet)
            default_status = Utilities.get_default_status_for_apps_today(current_user)
            ApplicationTodayService.make_edited(app_today_inst, default_status)

            data["status"] = "ok"
            data["technic_title_shrt"] = post_technic_title_shrt
            data["technic_title"] = some_technic_sheet.technic.title
            data["technic_sheet_id"] = some_technic_sheet.id
            data["app_technic_id"] = application_technic.id
            data["isChecked"] = application_technic.isChecked
            data["is_cancelled"] = application_technic.is_cancelled
            data["app_tech_desc"] = description
            data["font_size"] = current_user.font_size
        return data

    @classmethod
    def reject_application_technic(
        cls,
        post_application_technic_id: str,
        current_day: WorkDaySchema,
        current_user: UserSchema,
        app_today_inst: ApplicationToday,
    ):
        try:
            if Utilities.is_valid_str(post_application_technic_id):
                status = ApplicationTechnicService.reject_or_accept(
                    app_technic_id=int(post_application_technic_id),
                    workday_data=current_day,
                )
                default_status = Utilities.get_default_status_for_apps_today(
                    current_user
                )
                ApplicationTodayService.make_edited(app_today_inst, default_status)
                return status
        except Exception as e:
            log.error(
                f"ERROR: edit_application_view(): reject_application_technic | {e}"
            )
            return b"fail"

    @classmethod
    def delete_application_technic(
            cls,
            post_application_technic_id: str,
            app_today_inst: ApplicationToday,
            current_user: UserSchema
    ):
        if Utilities.is_valid_str(post_application_technic_id):
            status = ApplicationTechnicService.delete(id=post_application_technic_id)
            if status == "success":
                cache.delete(
                    f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{app_today_inst.date.date}"
                )
                default_status = Utilities.get_default_status_for_apps_today(
                    current_user
                )
                ApplicationTodayService.make_edited(app_today_inst, default_status)
                return b"success"
            else:
                return b"fail"
        return b"error"

    @classmethod
    def apply_changes_application_technic(
        cls,
        post_technic_title_shrt: str | None,
        post_technic_sheet_id: str | None,
        post_application_technic_id: str,
        post_application_technic_description: str,
        technic_titles_dict: list[ShortTechnicDataSchema],
        current_day: WorkDaySchema,
        current_user: UserSchema,
        app_today_inst: ApplicationToday,
    ):
        if Utilities.is_valid_str(post_technic_title_shrt):
            try:
                application_technic = ApplicationTechnicService.get_object(
                    id=post_application_technic_id
                )

                if not Utilities.is_valid_str(post_technic_sheet_id):
                    technic_title_dict = [
                        *filter(
                            lambda item: item["short_title"] == post_technic_title_shrt,
                            technic_titles_dict,
                        )
                    ][0]
                    technic_title = technic_title_dict.get("title")

                    some_technic_sheet = TechnicSheetService.get_some_technic_sheet(
                        technic_title=technic_title, workday_sheet_id=current_day.id
                    )
                else:
                    some_technic_sheet = TechnicSheetService.get_object(
                        id=post_technic_sheet_id
                    )
                description = (
                    post_application_technic_description
                    if post_application_technic_description
                    else ""
                )

                if some_technic_sheet:
                    if application_technic.technic_sheet != some_technic_sheet:
                        if application_technic.technic_sheet is not None:
                            TechnicSheetService.decrement_count_application(application_technic.technic_sheet)
                        application_technic.technic_sheet = some_technic_sheet
                        TechnicSheetService.increment_count_application(some_technic_sheet )
                else:
                    application_technic.technic_sheet = None
                application_technic.description = description
                application_technic.save(update_fields=["technic_sheet", "description"])
                cache.delete(
                    f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{current_day.date}"
                )
                default_status = Utilities.get_default_status_for_apps_today(current_user)
                ApplicationTodayService.make_edited(app_today_inst, default_status)
                return b"ok"
            except Exception as e:
                log.error(
                    f"ERROR: edit_application_view(): apply_changes_application_technic | {e}"
                )
                return b"fail"
        return b"fail"

    @classmethod
    def save_application_description(
        cls,
        post_application_today_description: str,
        app_today_inst: ApplicationToday,
    ):
        data = {
            "status": None,
            "app_today_id": app_today_inst.pk,
        }

        if Utilities.is_valid_str(post_application_today_description):
            post_application_today_description = (
                post_application_today_description.strip()
            )
            app_today_inst.description = post_application_today_description
        else:
            app_today_inst.description = ""
        app_today_inst.is_edited = True
        app_today_inst.save()
        cache.delete(f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{app_today_inst.date.date}")
        data["status"] = "ok"
        data["app_description"] = app_today_inst.description
        return data

    @classmethod
    def save_application_materials(
        cls,
        post_application_material_description: str,
        app_today_inst: ApplicationToday,
        current_user: UserSchema,
    ):
        app_material = ApplicationMaterialService.get_object(
            application_today=app_today_inst
        )

        data: dict[str, int | str | None] = {
            "status": None,
            "app_today_id": app_today_inst.id,
            "app_material_id": None,
        }

        if app_material and post_application_material_description == "":
            app_material.delete()
            cache.delete(
                f"{ApplicationMaterialService.CacheKeys.APP_MAT_FOR_DATE.value}:{app_today_inst.date.date}"
            )
            ApplicationTodayService.make_edited(app_today_inst)
            data["status"] = "deleted"

        elif not app_material and Utilities.is_valid_str(
            post_application_material_description
        ):
            create_data = EditApplicationMaterialSchema(
                application_today_id=app_today_inst.id,
                description=post_application_material_description,
            )
            application_material = ApplicationMaterialService.create(create_data)
            cache.delete(
                f"{ApplicationMaterialService.CacheKeys.APP_MAT_FOR_DATE.value}:{app_today_inst.date.date}"
            )
            ApplicationTodayService.make_edited(app_today_inst)
            data["status"] = "created"
            data["app_material_id"] = application_material.id

        elif app_material and Utilities.is_valid_str(
            post_application_material_description
        ):
            app_material.description = post_application_material_description
            app_material.isChecked = False
            app_material.save(update_fields=["description", "isChecked"])
            cache.delete(f"{ApplicationMaterialService.CacheKeys.APP_MAT_FOR_DATE.value}:{app_today_inst.date.date}")
            default_status = Utilities.get_default_status_for_apps_today(current_user)
            ApplicationTodayService.make_edited(app_today_inst, default_status)
            data["status"] = "updated"
            data["app_material_id"] = app_material.id
        return data

    @classmethod
    def get_technic_driver_list(
            cls,
            technic_titles: list[ShortTechnicDataSchema],
            technic_sheets_instance: QuerySet[TechnicSheet],
    ) -> list:
        """
        :param technic_titles: {technic.title_short: technic.title}
        :param technic_sheets_instance: TechnicSheet.objects
        :return:
        """

        technic_sheets_list = list(
            technic_sheets_instance.order_by("driver_sheet__driver__last_name").values(
                "id",
                "count_application",
                "driver_sheet__driver__last_name",
                "driver_sheet__status",
                "technic__title",
                "status"
            )
        )

        technic_driver_list = []
        for technic_title in technic_titles:
            t_s = [
                ts
                for ts in technic_sheets_list
                if ts["technic__title"] == technic_title.title
            ]
            technic_driver_list.append(
                {
                    "title_short": technic_title.short_title,
                    "title": technic_title.title,
                    "status_busies_list": technic_title.status_busies_list,
                    "technic_sheets": t_s,
                }
            )
        return technic_driver_list

    @classmethod
    def get_technic_driver_list_for_json(
            cls,
            technic_titles: list[ShortTechnicDataSchema],
            technic_sheets_instance: QuerySet[TechnicSheet],
    ) -> list:
        """
        :param technic_sheets_instance:
        :param technic_titles: {technic.title_short: technic.title}
        :return:
        """
        technic_driver_list = []
        for technic_title in technic_titles:
            technic_driver_list.append(
                {
                    "title_short": technic_title.short_title,
                    "title": technic_title.title,
                    "status_busies_list": technic_title.status_busies_list,
                    "technic_sheets": json.dumps(
                        list(
                            technic_sheets_instance.filter(
                                technic__title=technic_title.title
                            ).values(
                                "id",
                                "driver_sheet__driver__last_name",
                            )
                        )
                    ),
                }
            )
        return technic_driver_list
