from typing import Callable, Any
import enum

from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest

import dashboard.assets as assets
from dashboard.schemas.application_technic_schema import ApplicationTechnicForMechanicSchema
from dashboard.schemas.application_today_schema import CreateApplicationTodaySchema
from dashboard.schemas.user_schema import UserSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.application_material import ApplicationMaterialService
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.construction_site import ConstructionSiteService
from dashboard.services.driver_sheet import DriverSheetService
from dashboard.services.technic import TechnicService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.services.user import UserService
from dashboard.services.common import CommonService
from dashboard.utilities import Utilities as Utils
from logger import getLogger

log = getLogger(__name__)


class DashboardService:

    class TemplateDashboardFor(enum.Enum):
        ADMIN = 'content/dashboard/admin_dashboard.html'
        MASTER = 'content/dashboard/foreman_dashboard.html'
        FOREMAN = 'content/dashboard/foreman_dashboard.html'
        MECHANIC = 'content/dashboard/mechanic_dashboard.html'
        SUPPLY = 'content/dashboard/supply_dashboard.html'
        EMPLOYEE = 'content/dashboard/employee_dashboard.html'
        DRIVER = 'content/dashboard/driver_dashboard.html'
        INFO_ABOUT_DRIVER = 'content/spec/info_about_drivers_dashboard.html'

    @classmethod
    def get_dashboard(
            cls,
            user_data: UserSchema
    ) -> tuple[Callable[[ WSGIRequest | Any, WorkDaySchema, dict], dict], str] :
        match user_data.post:
            case assets.UserPosts.ADMINISTRATOR.title:
                return cls.get_dashboard_for_admin, cls.TemplateDashboardFor.ADMIN.value
            case assets.UserPosts.MASTER.title:
                return cls.get_dashboard_for_foreman_or_master, cls.TemplateDashboardFor.MASTER.value
            case assets.UserPosts.FOREMAN.title:
                return cls.get_dashboard_for_foreman_or_master, cls.TemplateDashboardFor.FOREMAN.value
            case assets.UserPosts.MECHANIC.title:
                return cls.get_dashboard_for_mechanic, cls.TemplateDashboardFor.MECHANIC.value
            case assets.UserPosts.SUPPLY.title:
                return cls.get_dashboard_for_supply, cls.TemplateDashboardFor.SUPPLY.value
            case assets.UserPosts.EMPLOYEE.title:
                return cls.get_dashboard_for_employee, cls.TemplateDashboardFor.EMPLOYEE.value
            case assets.UserPosts.DRIVER.title:
                return cls.get_dashboard_for_driver, cls.TemplateDashboardFor.DRIVER.value
            case _:
                return cls.get_dashboard_for_employee, cls.TemplateDashboardFor.EMPLOYEE.value

    @classmethod
    def get_dashboard_for_admin(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:
        view_mode_ = context.get("VIEW_MODE")
        current_user = UserService.get_current_user(request.user.id)

        if request.POST.get("operation") == "set_spec_task":
            technic_sheet_id = request.POST.get("technic_sheet_id")
            if technic_sheet_id:
                CommonService.set_spec_task(technic_sheet_id)

        if request.POST.get("operation") == "change_read_only_mode":
            if request.POST.get("read_only") == "0":
                CommonService.set_accept_mode(current_day, assets.AcceptMode.OPEN)
            if request.POST.get("read_only") == "1":
                CommonService.set_accept_mode(current_day, assets.AcceptMode.CLOSE)

        if request.POST.get("operation") == "toggle_panel":
            _hide_panel = "change"
            if _hide_panel:
                _user = UserService.get_object(id=request.user.id)
                _user.is_show_panel = False if _user.is_show_panel else True
                _user.save(update_fields=["is_show_panel"])
                cache.delete(f"{UserService.CacheKeys.CURRENT_USER.value}:{_user.pk}")

        app_today_for_date = ApplicationTodayService.get_app_today_for_date(current_day)
        app_tech_for_date = ApplicationTechnicService.get_app_tech_for_date(current_day)
        app_mat_for_date = ApplicationMaterialService.get_app_mat_for_date(current_day)
        driver_sheet_for_date = DriverSheetService.get_driver_sheet_for_date(current_day)
        tech_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
        technic_list = TechnicService.get_all_technic_data()
        user_list = UserService.get_all_users_list()
        cs_active = ConstructionSiteService.get_showed_cs_list()

        if view_mode_ == assets.ViewMode.ARCHIVE.value:
            app_today_for_date_ids = [at.construction_site for at in app_today_for_date]
            construction_sites = [cs for cs in cs_active if cs.id in app_today_for_date_ids]
        else:
            construction_sites = cs_active

        if not current_user.is_show_absent_app:
            app_today_for_date_ids = [
                at.construction_site
                for at in app_today_for_date
                if at.status != assets.ApplicationTodayStatus.ABSENT.title
            ]

            if not current_user.is_show_deleted_app:
                app_today_for_date_ids = [
                    at.construction_site
                    for at in app_today_for_date
                    if at.status != assets.ApplicationTodayStatus.DELETED.title
                ]
            construction_sites = [
                cs for cs in construction_sites if cs.id in app_today_for_date_ids
            ]

        if not current_user.is_show_saved_app:
            app_today_for_date_ids = [
                at.construction_site
                for at in app_today_for_date
                if at.status != assets.ApplicationTodayStatus.SAVED.title
            ]
            construction_sites = [
                cs for cs in construction_sites if cs.id in app_today_for_date_ids
            ]

        construction_sites_ids = [cs.id for cs in construction_sites]
        applications_today = [at for at in app_today_for_date if at.construction_site in construction_sites_ids]

        if not current_user.is_show_deleted_app:
            applications_today = [at for at in applications_today if not at.isArchive]

        status_list_application_today = CommonService.get_status_lists_of_app_today(
            applications_today=applications_today
        )
        context["status_list_application_today"] = status_list_application_today

        app_today_ids = [at.id for at in applications_today]
        if current_user.is_show_technic_app:
            applications_technic = [at for at in app_tech_for_date if at.application_today in app_today_ids]
        else:
            applications_technic = []

        if current_user.is_show_material_app:
            application_material = [am for am in app_mat_for_date if am.application_today in app_today_ids]
        else:
            application_material = []

        context["table_working_technic_sheet"] = (
            CommonService.get_table_working_technic_sheet(current_day)
        )

        applications_today_list = [at.model_dump() for at in applications_today]
        for at in applications_today_list:
            cs = [cs.model_dump() for cs in construction_sites if cs.id == at["construction_site"]]
            if cs:
                cs = cs.pop()
                foreman = UserService.filter_user_by_id_from_data(cs['foreman'], user_list)
                cs['foreman'] = foreman.model_dump() if foreman else None
                at["construction_site"] = cs
        context["applications_today_list"] = applications_today_list

        construction_sites = [cs.model_dump() for cs in construction_sites]

        for cs in construction_sites:
            foreman = UserService.filter_user_by_id_from_data(cs['foreman'], user_list)
            cs['foreman'] = foreman.model_dump() if cs['foreman'] else None
            app_today = ApplicationTodayService.get_app_today_by_cs_id_from_data(cs['id'], applications_today)
            cs['application_today'] = app_today.model_dump() if app_today else None

            if cs['application_today']:
                am = ApplicationMaterialService.get_app_mat_by_at_id_from_data(
                    app_today_id=cs['application_today']['id'],
                    data=application_material
                )
                cs['application_today']["application_material"] = am.model_dump() if am else None

                application_technic_list = [
                    at.model_dump()
                    for at in ApplicationTechnicService.filter_app_tech_by_at_id_from_data(
                        app_today_id=cs['application_today']['id'],
                        data=applications_technic
                    ) if at
                ]
                cs['application_today']["application_technic"] = application_technic_list

                for app_tech_item in application_technic_list:
                    if app_tech_item:
                        tech_sheet_schema = TechnicSheetService.filter_tech_sheet_by_id(
                            tech_sheet_id=app_tech_item['technic_sheet'],
                            tech_sheet_list=tech_sheet_for_date
                        )
                        app_tech_item['technic_sheet'] = tech_sheet_schema.model_dump() if tech_sheet_schema else None

                        driver_sheet_schema = DriverSheetService.filter_driver_sheet_by_id(
                            driver_sheet_id=tech_sheet_schema.driver_sheet,
                            driver_sheet_list=driver_sheet_for_date
                        ) if tech_sheet_schema else None

                        if tech_sheet_schema:
                            app_tech_item["technic_sheet"]["driver_sheet"] = driver_sheet_schema.model_dump() if driver_sheet_schema else None
                            technic_schema = TechnicService.filter_technic_by_id(
                                technic_id=tech_sheet_schema.technic,
                                technic_list=technic_list
                            )
                            app_tech_item["technic_sheet"]["technic"] = technic_schema.model_dump() if technic_schema else None

                            if driver_sheet_schema:
                                driver = UserService.filter_user_by_id_from_data(
                                    user_id=driver_sheet_schema.driver,
                                    data=user_list
                                ) if driver_sheet_schema else None
                                app_tech_item["technic_sheet"]["driver_sheet"]["driver"] = (driver.model_dump() if driver else None)
        context["construction_sites"] = construction_sites

        context["construction_sites"] = sorted(
            context["construction_sites"], key=Utils.sort_applications_by_status
        )

        priority_id_list = CommonService.get_priority_ids_list(current_day)
        context["priority_id_list"] = priority_id_list

        busiest_technic_title_list = CommonService.get_busiest_technic_title(current_day)

        conflict_technic_sheet = CommonService.get_conflict_list_of_technic_sheet(
            busiest_technic_title=busiest_technic_title_list,
            priority_id_list=priority_id_list,
            get_only_id_list=True,
        )
        context["conflict_technic_sheet"] = conflict_technic_sheet
        return context

    @classmethod
    def get_dashboard_for_foreman_or_master(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:
        view_mode_ = context.get("VIEW_MODE")
        current_user = UserService.get_current_user(request.user.id)
        current_foreman_id = current_user.id if Utils.is_foreman(current_user) else current_user.supervisor_user_id

        cs_active = ConstructionSiteService.get_showed_cs_list()
        app_today_for_date = ApplicationTodayService.get_app_today_for_date(current_day)
        app_tech_for_date = ApplicationTechnicService.get_app_tech_for_date(current_day)
        app_mat_for_date = ApplicationMaterialService.get_app_mat_for_date(current_day)
        driver_sheet_for_date = DriverSheetService.get_driver_sheet_for_date(current_day)
        tech_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
        technic_list = TechnicService.get_all_technic_data()
        user_list = UserService.get_all_users_list()

        if view_mode_ == assets.ViewMode.ARCHIVE.value:
            app_today_for_date_ids = [at.construction_site for at in app_today_for_date if at.date == current_day.id]
            construction_sites = [
                cs for cs in cs_active
                if cs.foreman == current_foreman_id
                   and cs.id in app_today_for_date_ids
            ]
        else:
            construction_sites = [
                cs for cs in cs_active
                if cs.foreman == current_foreman_id
                   and cs.status
            ]

        if not current_user.is_show_absent_app:
            app_today_for_date_ids = [
                at.construction_site
                for at in app_today_for_date
                if at.status != assets.ApplicationTodayStatus.ABSENT.title
            ]
            if not current_user.is_show_deleted_app:
                app_today_for_date_ids = [
                    at.construction_site
                    for at in app_today_for_date
                    if at.status != assets.ApplicationTodayStatus.DELETED.title
                ]
            construction_sites = [
                cs for cs in construction_sites if cs.id in app_today_for_date_ids
            ]

        if not current_user.is_show_saved_app:
            app_today_for_date_ids = [
                at.construction_site
                for at in app_today_for_date
                if at.status != assets.ApplicationTodayStatus.SAVED.title
            ]
            construction_sites = [
                cs for cs in construction_sites if cs.id in app_today_for_date_ids
            ]

        construction_sites_ids = [cs.id for cs in construction_sites]
        applications_today = [
            at
            for at in app_today_for_date
            if at.construction_site in construction_sites_ids
        ]

        if not current_user.is_show_deleted_app:
            applications_today = [at for at in applications_today if not at.isArchive]

        status_list_application_today = CommonService.get_status_lists_of_app_today(
            applications_today=applications_today
        )
        context["status_list_application_today"] = status_list_application_today

        app_today_ids = [at.id for at in applications_today]

        if current_user.is_show_technic_app:
            applications_technic = [at for at in app_tech_for_date if at.application_today in app_today_ids]
        else:
            applications_technic = []

        if current_user.is_show_material_app:
            application_material = [am for am in app_mat_for_date if am.application_today in app_today_ids]
        else:
            application_material = []

        applications_today_list = [at.model_dump() for at in applications_today]
        for at in applications_today_list:
            cs = [
                cs.model_dump()
                for cs in construction_sites
                if cs.id == at["construction_site"]
            ]
            if cs:
                cs = cs.pop()
                foreman = UserService.filter_user_by_id_from_data(
                    current_foreman_id, user_list
                )
                cs["foreman"] = foreman.model_dump() if foreman else None
                at["construction_site"] = cs
        context["applications_today_list"] = applications_today_list

        construction_sites = [cs.model_dump() for cs in construction_sites]

        for cs in construction_sites:
            cs['foreman'] = UserService.get_current_user(user_id=current_foreman_id)
            app_today = ApplicationTodayService.get_app_today_by_cs_id_from_data(
                constr_site_id=cs["id"],
                data=applications_today
            )
            cs["application_today"] = app_today.model_dump() if app_today else None

            if cs['application_today']:
                am = ApplicationMaterialService.get_app_mat_by_at_id_from_data(
                    app_today_id=cs['application_today']['id'],
                    data=application_material
                )
                cs['application_today']["application_material"] = am.model_dump() if am else None

                application_technic_list = [
                    at.model_dump()
                    for at in ApplicationTechnicService.filter_app_tech_by_at_id_from_data(
                        app_today_id=cs['application_today']['id'],
                        data=applications_technic
                    )
                ]
                cs['application_today']["application_technic"] = application_technic_list

                for app_tech_item in application_technic_list:
                    if app_tech_item:
                        tech_sheet_schema = TechnicSheetService.filter_tech_sheet_by_id(
                            tech_sheet_id=app_tech_item['technic_sheet'],
                            tech_sheet_list=tech_sheet_for_date
                        )
                        app_tech_item['technic_sheet'] = tech_sheet_schema.model_dump() if tech_sheet_schema else None
                        driver_sheet_schema = DriverSheetService.filter_driver_sheet_by_id(
                            driver_sheet_id=tech_sheet_schema.driver_sheet,
                            driver_sheet_list=driver_sheet_for_date
                        ) if tech_sheet_schema else None

                        if tech_sheet_schema:
                            app_tech_item["technic_sheet"]["driver_sheet"] = driver_sheet_schema.model_dump() if driver_sheet_schema else None
                            technic_schema = TechnicService.filter_technic_by_id(
                                technic_id=tech_sheet_schema.technic,
                                technic_list=technic_list
                            )
                            app_tech_item["technic_sheet"]["technic"] = technic_schema.model_dump() if technic_schema else None

                            if driver_sheet_schema:
                                driver = UserService.filter_user_by_id_from_data(
                                    user_id=driver_sheet_schema.driver,
                                    data=user_list
                                ) if driver_sheet_schema else None
                                app_tech_item["technic_sheet"]["driver_sheet"]["driver"] = (driver.model_dump() if driver else None)

        context["construction_sites"] = construction_sites
        context["construction_sites"] = sorted(
            context["construction_sites"], key=Utils.sort_applications_by_status
        )
        return context

    @classmethod
    def get_dashboard_for_mechanic(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:

        technic_sheet_list = TechnicSheetService.get_queryset(
            date_id=current_day.id,
            isArchive=False,
        ).select_related("technic__attached_driver", "driver_sheet__driver")

        if not technic_sheet_list.exists():
            CommonService.prepare_sheets(current_day)
        context["technic_sheet_list"] = technic_sheet_list

        application_technic_list = (
            ApplicationTechnicService.get_queryset(
                application_today__date_id=current_day.id,
                application_today__status__in=assets.SHOW_APPLICATIONS_FOR_MECHANIC_WITH_STATUSES,
                isArchive=False,
                is_cancelled=False,
            )
            .select_related("application_today__construction_site__foreman")
            .values(
                "technic_sheet__id",
                "application_today__construction_site__address",
                "application_today__construction_site__foreman__last_name",
                "description",
            ).order_by("priority")
        )
        application_technic_data = [
            ApplicationTechnicForMechanicSchema(**at)
            for at in application_technic_list
        ]

        applications_technic = []
        for technic_sheet in technic_sheet_list:
            applications_technic.append(
                {
                    "technic_sheet_id": technic_sheet.id,
                    "applications": [at for at in application_technic_data if at.technic_sheet__id == technic_sheet.id],
                }
            )
        context["applications_technic"] = applications_technic
        return context

    @classmethod
    def get_dashboard_for_supply(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:
        construction_site = ConstructionSiteService.get_construction_site_for_supply()
        app_today_for_date = ApplicationTodayService.get_app_today_for_date(current_day)
        app_mat_for_date = ApplicationMaterialService.get_app_mat_for_date(current_day)
        driver_list = UserService.get_driver_list()
        application_today = ApplicationTodayService.get_app_today_by_cs_id_from_data(construction_site.id, app_today_for_date)

        if not request.user.is_show_deleted_app:
            application_today = application_today if application_today and not application_today.isArchive else None

        if application_today:
            status_list_application_today = CommonService.get_status_lists_of_app_today(
                applications_today=[application_today]
            )
            context["status_list_application_today"] = status_list_application_today

        applications_technic = (ApplicationTechnicService.model.objects.filter(
                application_today_id=application_today.id,
                isArchive=False
            )
            .values(
                "id",
                "description",
                "priority",
                "isChecked",
                "isArchive",
                "is_cancelled",
                "technic_sheet_id",
                "technic_sheet__technic__title",
                "technic_sheet__status",
                "technic_sheet__driver_sheet_id",
                "technic_sheet__driver_sheet__driver__last_name",
                "technic_sheet__driver_sheet__status",
                "technic_sheet__count_application"
            )) if application_today else None

        if application_today:
            applications_material = ApplicationMaterialService.get_app_mat_by_at_id_from_data(
                app_today_id=application_today.id,
                data=app_mat_for_date
            )
            context["applications_material"] = applications_material

        if request.method == "POST":
            application_technic_id = request.POST.get("applicationTechnicId")
            operation = request.POST.get("operation")
            application_today_id = request.POST.get("application_today_id")

            #   Отвергнуть заявку
            if application_technic_id and operation == "reject":
                ApplicationTechnicService.reject_or_accept(
                    app_technic_id=application_technic_id,
                    workday_data=current_day,
                )

            elif application_technic_id and operation == "accept":
                if not application_today_id:
                    create_data = CreateApplicationTodaySchema(
                        construction_site_id=construction_site.id,
                        date_id=current_day.id,
                    )
                    _application_today = ApplicationTodayService.get_or_create_by_data(
                        create_data
                    )
                    _application_today.status = (
                        assets.ApplicationTodayStatus.SAVED.title
                    )
                    _application_today.save(update_fields=["status"])
                    cache.delete(
                        f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{current_day.date}"
                    )
                    application_today_id = _application_today.id

                CommonService.accept_app_tech_to_supply(
                    application_technic_id, application_today_id
                )

        count_not_checked_app_mater = ApplicationMaterialService.get_queryset(
            application_today__status__in=assets.SHOW_APPLICATIONS_FOR_SUPPLY_WITH_STATUSES,
            isArchive=False,
            application_today__date_id=current_day.id,
            isChecked=False,
        ).count()
        if count_not_checked_app_mater > 0:
            context["count_not_checked_app_mater"] = count_not_checked_app_mater

        technic_list = TechnicService.get_all_technic_data()
        supply_technic_list = [
            t.model_dump() for t in technic_list
            if t.supervisor_technic == assets.UserPosts.SUPPLY.title and not t.isArchive
        ]
        for technic in supply_technic_list:
            driver = UserService.filter_user_by_id_from_data(
                technic["attached_driver"], driver_list)
            technic["attached_driver"] = driver.model_dump()

        applications_technic_for_supply = []

        _app_tech = (
            ApplicationTechnicService.get_queryset(
                application_today__date_id=current_day.id,
                isArchive=False,
                application_today__isArchive=False
            )
            .select_related("application_today__construction_site")
            .exclude(application_today__construction_site=construction_site.id)
        )
        _app_tech = _app_tech.exclude(
            application_today__status=assets.ApplicationTodayStatus.SAVED.title
        )

        for _technic in supply_technic_list:
            _application_technic = _app_tech.filter(technic_sheet__technic=_technic['id'])
            applications_technic_for_supply.append(
                {"technic": _technic, "application_technic": _application_technic}
            )
            if _application_technic.exists():
                context["a_m_exists"] = True

        context["application_today"] = application_today#.first()
        context["construction_site"] = construction_site
        context["applications_technic"] = applications_technic
        # context["applications_material"] = applications_material
        context["applications_technic_for_supply"] = applications_technic_for_supply

        return context

    @classmethod
    def get_dashboard_for_employee(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:

        current_user = UserService.get_current_user(request.user.id)

        app_today_for_date = ApplicationTodayService.get_app_today_for_date(current_day)
        app_tech_for_date = ApplicationTechnicService.get_app_tech_for_date(current_day)
        app_mat_for_date = ApplicationMaterialService.get_app_mat_for_date(current_day)
        driver_sheet_for_date = DriverSheetService.get_driver_sheet_for_date(current_day)
        tech_sheet_for_date = TechnicSheetService.get_tech_sheet_for_date(current_day)
        technic_list = TechnicService.get_all_technic_data()
        user_list = UserService.get_all_users_list()
        cs_active = ConstructionSiteService.get_showed_cs_list()
        applications_today = [
            at for at in app_today_for_date
            if not at.isArchive
               and at.status in assets.SHOW_APPLICATIONS_WITH_STATUSES
        ]
        app_today_ids = [at.id for at in applications_today]

        construction_sites_ids = [at.construction_site for at in applications_today]
        construction_sites = [
            cs for cs in cs_active
            if cs.id in construction_sites_ids
               and not cs.isArchive
               and cs.status
        ]

        if current_user.filter_foreman != 0:
            construction_sites = [
                cs for cs in construction_sites
                if cs.foreman==current_user.filter_foreman
            ]

        if current_user.filter_construction_site != 0:
            construction_sites = [
                cs for cs in construction_sites
                if cs.id == current_user.filter_construction_site
            ]

        applications_technic = [
            at
            for at in app_tech_for_date
            if at.application_today in app_today_ids
            and not at.isArchive
            and not at.is_cancelled
            and not at.isChecked
        ]

        if current_user.filter_technic:
            technic_ids = [t.id for t in technic_list if t.title == current_user.filter_technic]
            tech_sheet_ids = [ts.id for ts in tech_sheet_for_date if ts.technic in technic_ids]
            applications_technic = [at for at in applications_technic if at.technic_sheet in tech_sheet_ids]
            app_today_ids = [at.application_today for at in applications_technic]
            applications_today = [at for at in applications_today if at.id in app_today_ids]
            construction_sites_ids = [at.construction_site for at in applications_today]
            construction_sites = [
                cs for cs in construction_sites
                if cs.id in construction_sites_ids
            ]

        if not current_user.is_show_technic_app:
            applications_technic = []

        if current_user.is_show_material_app:
            application_material = [
                am for am in app_mat_for_date
                if am.application_today in app_today_ids
                   and not am.isArchive
            ]
        else:
            application_material = []

        context["applications_today_list"] = applications_today
        construction_sites = [cs.model_dump() for cs in construction_sites]
        for cs in construction_sites:
            foreman = UserService.filter_user_by_id_from_data(cs['foreman'], user_list)
            cs['foreman'] = foreman.model_dump() if cs['foreman'] else None
            app_today = ApplicationTodayService.get_app_today_by_cs_id_from_data(cs['id'], applications_today)
            cs['application_today'] = app_today.model_dump() if app_today else None

            if cs['application_today']:
                am = ApplicationMaterialService.get_app_mat_by_at_id_from_data(cs['application_today']['id'], application_material)
                cs['application_today']["application_material"] = am.model_dump() if am else None

                application_technic_list = [
                    at.model_dump()
                    for at in ApplicationTechnicService.filter_app_tech_by_at_id_from_data(
                        app_today_id=cs['application_today']['id'],
                        data=applications_technic
                    ) if at
                ]
                cs['application_today']["application_technic"] = application_technic_list

                for app_tech_item in application_technic_list:
                    if app_tech_item:
                        tech_sheet_schema = TechnicSheetService.filter_tech_sheet_by_id(
                            tech_sheet_id=app_tech_item['technic_sheet'],
                            tech_sheet_list=tech_sheet_for_date
                        )
                        app_tech_item['technic_sheet'] = tech_sheet_schema.model_dump() if tech_sheet_schema else None

                        driver_sheet_schema = DriverSheetService.filter_driver_sheet_by_id(
                            driver_sheet_id=tech_sheet_schema.driver_sheet,
                            driver_sheet_list=driver_sheet_for_date
                        ) if tech_sheet_schema else None

                        if tech_sheet_schema:
                            app_tech_item["technic_sheet"]["driver_sheet"] = driver_sheet_schema.model_dump() if driver_sheet_schema else None
                            technic_schema = TechnicService.filter_technic_by_id(
                                technic_id=tech_sheet_schema.technic,
                                technic_list=technic_list
                            )
                            app_tech_item["technic_sheet"]["technic"] = technic_schema.model_dump() if technic_schema else None

                            if driver_sheet_schema:
                                driver = UserService.filter_user_by_id_from_data(
                                    user_id=driver_sheet_schema.driver,
                                    data=user_list
                                )
                                app_tech_item["technic_sheet"]["driver_sheet"]["driver"] = (driver.model_dump() if driver else None)
        context["construction_sites"] = construction_sites

        context["construction_sites"] = sorted(
            context["construction_sites"], key=Utils.sort_applications_by_status
        )
        return context

    @classmethod
    def get_dashboard_for_driver(
            cls,
            request,
            current_day: WorkDaySchema,
            context: dict
    ) -> dict:
        if Utils.is_valid_str(request.GET.get("driver_id")):
            current_driver = UserService.get_current_user(request.GET.get("driver_id"))
        else:
            current_driver = UserService.get_current_user(request.user.id)
        context["current_driver"] = current_driver

        current_technic_sheet = TechnicSheetService.get_queryset(
            driver_sheet__driver=current_driver.id,
            isArchive=False,
            date_id=current_day.id,
        ).select_related("driver_sheet__driver", "technic")

        supply_technic_list = TechnicService.get_supply_technic_list()

        current_technic_sheet_id_list = list(
            current_technic_sheet.values_list("technic__id", flat=True)
        )
        supply_technic_list_id_list = [s_tl.id for s_tl in supply_technic_list]

        is_supply_driver = Utils.is_supply_driver(
            current_technic_sheet_id_list, supply_technic_list_id_list
        )

        applications_technic = ApplicationTechnicService.get_queryset(
            isArchive=False,
            isChecked=False,
            is_cancelled=False,
            application_today__date_id=current_day.id,
            application_today__status__in=assets.SHOW_APPLICATIONS_WITH_STATUSES,
        ).select_related("application_today__construction_site__foreman")

        technic_application_list = []
        for tech_sheet in current_technic_sheet:
            technic_application_list.append(
                {
                    "technic_sheet": tech_sheet,
                    "applications_technic": applications_technic.filter(
                        technic_sheet=tech_sheet
                    ).order_by("priority"),
                }
            )
        context["technic_application_list"] = technic_application_list

        if is_supply_driver:
            application_today_id_list = ApplicationTodayService.get_queryset(
                date_id=current_day.id,
                isArchive=False,
                status__in=assets.SHOW_APPLICATIONS_WITH_STATUSES,
            ).values_list("id", flat=True)
        else:
            application_today_id_list = applications_technic.filter(
                technic_sheet__in=current_technic_sheet
            ).values_list("application_today", flat=True)

        applications_today = ApplicationTodayService.get_queryset(
            id__in=application_today_id_list,
            status__in=assets.SHOW_APPLICATIONS_WITH_STATUSES,
        ).values(
            "id",
            "construction_site__address",
            "construction_site__foreman__last_name",
            "construction_site__foreman__first_name",
            "description",
        )
        for application in applications_today:
            if is_supply_driver:
                application["application_material"] = (
                    ApplicationMaterialService.get_queryset(
                        application_today__id=application["id"],
                        isChecked=True,
                    ).values("description")
                )
            else:
                application[
                    "application_technic"
                ] = ApplicationTechnicService.get_queryset(
                    application_today__id=application["id"],
                ).values(
                    "is_cancelled",
                    "technic_sheet__technic__title",
                    "technic_sheet__driver_sheet__status",
                    "technic_sheet__driver_sheet__driver__last_name",
                    "technic_sheet__driver_sheet__driver__id",
                    "priority",
                    "technic_sheet__count_application",
                    "description",
                )

        context["applications_today"] = applications_today

        return context
