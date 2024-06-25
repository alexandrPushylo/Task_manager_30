from dashboard.models import ConstructionSite, User
import dashboard.assets as ASSETS

from logger import getLogger
log = getLogger(__name__)


def hide_construction_site(constr_site_id):
    try:
        constr_site = ConstructionSite.objects.get(pk=constr_site_id)
        if constr_site.status:
            constr_site.status = False
            log.info(f'Объект {constr_site.address} был скрыт')
        else:
            constr_site.status = True
            log.info(f'Объект {constr_site.address} был отображен')
        constr_site.save(update_fields=['status'])
    except ConstructionSite.DoesNotExist:
        log.error(f'Объекта с id {constr_site_id} не существует')


def delete_construction_site(constr_site_id):
    try:
        constr_site = ConstructionSite.objects.get(pk=constr_site_id)
        if constr_site.isArchive:
            constr_site.isArchive = False
            log.info(f'Объект {constr_site.address} был восстановлен из архива')
        else:
            constr_site.isArchive = True
            log.info(f'Объект {constr_site.address} был помешен в архив')
        constr_site.save(update_fields=['isArchive'])
    except ConstructionSite.DoesNotExist:
        log.error(f'Объекта с id {constr_site_id} не существует')


def check_data(data: dict):
    out = {}
    cs_address = data.get('address')
    cs_foreman = data.get('foreman')

    if cs_foreman:
        try:
            foreman = User.objects.get(pk=cs_foreman)
            out['foreman'] = foreman
        except User.DoesNotExist:
            out['foreman'] = None
            log.error(f'Прораба с id {cs_foreman} не существует')
    else:
        out['foreman'] = None

    if cs_address:
        out['address'] = cs_address
        log.info(f'Данные: (cs_address) в порядке')
        return out
    else:
        log.error('Ошибка с данными: (cs_address) при проверке')
        return None


def create_construction_site(data: dict):
    ConstructionSite.objects.create(
        address=data['address'],
        foreman=data['foreman'],
    )
    log.info(f'Объект {data["address"]} был создан')


def edit_construction_site(constr_site_id, data: dict):
    try:
        constr_site = ConstructionSite.objects.get(pk=constr_site_id)
        constr_site.address = data['address']
        constr_site.foreman = data['foreman']
        constr_site.save(update_fields=['address', 'foreman'])
        log.info(f'Объект {data["address"]} был изменен')
    except ConstructionSite.DoesNotExist:
        log.error(f'Объекта с id {constr_site_id} не существует')


def create_or_edit_construction_site(data: dict, constr_site_id=None):
    prepare_data = check_data(data)
    if prepare_data:
        if constr_site_id:
            edit_construction_site(constr_site_id, prepare_data)
        else:
            create_construction_site(prepare_data)
    else:
        log.error('Ошибка с данными')
