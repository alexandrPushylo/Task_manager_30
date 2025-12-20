from django.urls import path, re_path, include
import dashboard.views as V

urlpatterns = [
    path('', V.routing, name='routing'),
    path('dashboard/', V.dashboard_view, name='dashboard'),
    path('edit_application/', V.edit_application_view, name='edit_application'),
    path('clear_or_restore_application/', V.clear_or_restore_application_today, name='clear_application'),

    path('work_days/', V.workday_sheet_view, name='work_days'),
    path('driver_sheet/', V.driver_sheet_view, name='driver_sheet'),
    path('technic_sheet/', V.technic_sheet_view, name='technic_sheet'),

    path('conflicts_list/', V.conflicts_list_view, name='conflicts_list'),
    path('conflict_resolution/', V.conflict_resolution_view, name='conflict_resolution'),

    path('technic_application_list/', V.show_technic_application, name='technic_application_list'),
    path('material_application_list/', V.show_material_application, name='material_application_list'),
    path('material_application_supply/', V.material_application_supply_view, name='material_application_supply'),
    path('application_for_driver/', V.application_for_driver_view, name='application_for_driver'),

    path('users/', V.users_view, name='users'),
    path('edit_user/', V.edit_user_view, name='edit_user'),
    path('delete_user/', V.delete_user_view, name='delete_user'),
    path('profile/', V.profile_view, name='profile'),

    path('technics/', V.technic_view, name='technics'),
    path('edit_technic/', V.edit_technic_view, name='edit_technic'),
    path('delete_technic/', V.delete_technic_view, name='delete_technic'),

    path('construction_site/', V.construction_site_view, name='construction_site'),
    path('archive_construction_site/', V.archive_construction_site_view, name='archive_construction_sites'),
    path('edit_construction_sites/', V.edit_construction_sites, name='edit_construction_sites'),

    path('spec_page/', V.spec_page_view, name='spec_page'),
    path('test/', V.test_page_view, name='test'),
]
