from dashboard.models import ConstructionSite, User
from dashboard.services.user import get_user
from django.db.models import QuerySet  # type: ignore

import dashboard.utilities as U

from logger import getLogger

log = getLogger(__name__)


def get_construction_sites(**kwargs) -> ConstructionSite:
    try:
        construction_sites = ConstructionSite.objects.get(**kwargs)
        return construction_sites
    except ConstructionSite.DoesNotExist:
        log.error('get_construction_sites(): DoesNotExist')
        return ConstructionSite.objects.none()
    except ValueError:
        log.error('get_construction_sites(): ValueError')
        return ConstructionSite.objects.none()


def get_construction_site_queryset(select_related: tuple = (),
                                   order_by: tuple = (),
                                   **kwargs) -> QuerySet[ConstructionSite]:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """
    constr_sites = ConstructionSite.objects.filter(**kwargs)

    if select_related:
        constr_sites = constr_sites.select_related(*select_related)
    if order_by:
        constr_sites = constr_sites.order_by(*order_by)
    return constr_sites


def hide_construction_site(constr_site_id):
    constr_site = get_construction_sites(pk=constr_site_id)
    if constr_site:
        if constr_site.status:
            constr_site.status = False
            log.info('Объект был скрыт')
        else:
            constr_site.status = True
            log.info('Объект был отображен')
        constr_site.save(update_fields=['status'])


def delete_construction_site(constr_site_id) -> ConstructionSite | None:
    constr_site = get_construction_sites(pk=constr_site_id)
    if constr_site:
        if constr_site.isArchive:
            constr_site.isArchive = False
            constr_site.deleted_date = None
            log.info('Объект %s был восстановлен из архива' % constr_site.address)
        else:
            constr_site.isArchive = True
            constr_site.deleted_date = U.TODAY
            log.info('Объект %s был помешен в архив' % constr_site.address)

        constr_site.save(update_fields=['isArchive', 'deleted_date'])
        return constr_site
    return None


def check_data(data: dict) -> dict | None:
    out: dict[str, User | None] = {}

    cs_address = data.get('address')
    cs_foreman = data.get('foreman')

    if cs_foreman:
        foreman = get_user(pk=cs_foreman)
        if foreman:
            out['foreman'] = foreman
        else:
            out['foreman'] = None
            log.error('Прораба с id %s не существует' % cs_foreman)
    else:
        out['foreman'] = None

    if cs_address:
        out['address'] = cs_address
        log.info('Данные: (cs_address) в порядке')
        return out
    else:
        log.error('Ошибка с данными: (cs_address) при проверке')
        return None


def create_construction_site(data: dict):
    ConstructionSite.objects.create(
        address=data['address'],
        foreman=data['foreman'],
    )
    log.info('Объект %s был создан' % data["address"])


def edit_construction_site(constr_site_id, data: dict):
    constr_site = get_construction_sites(pk=constr_site_id)
    if constr_site:
        constr_site.address = data['address']
        constr_site.foreman = data['foreman']
        constr_site.save(update_fields=['address', 'foreman'])
        log.info('Объект %s был изменен' % data["address"])


def create_or_edit_construction_site(data: dict, constr_site_id=None):
    prepare_data = check_data(data)
    if prepare_data:
        is_cs_was_del = is_construction_site_already_exists(prepare_data['address'], prepare_data['foreman'])
        if is_cs_was_del:
            restore_construction_site(prepare_data)
        else:
            if constr_site_id:
                edit_construction_site(constr_site_id, prepare_data)
            else:
                create_construction_site(prepare_data)
    else:
        log.error('Ошибка с данными')


def is_construction_site_already_exists(constr_site_title: str, foreman: User) -> bool:
    """
    Существует ли объект с данными параметрами
    :param constr_site_title:
    :param foreman:
    :return:
    """
    if constr_site_title is None or constr_site_title == '':
        return False
    cs = get_construction_site_queryset(
        address=constr_site_title,
        foreman=foreman,
    )
    return True if cs.exists() else False


def restore_construction_site(data: dict[str, User | None]):
    """
    Восстановление объекта в рабочее состояние
    :param data:
    :return:
    """
    cs = get_construction_sites(
        address=data['address'],
        foreman=data['foreman'],
    )
    if cs:
        cs.isArchive = False
        cs.status = True
        cs.deleted_date = None
        cs.save()
        log.info('Объект %s был восстановлен' % data["address"])