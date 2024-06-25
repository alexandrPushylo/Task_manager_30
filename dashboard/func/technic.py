from dashboard.models import Technic, User
import dashboard.assets as ASSETS

from logger import getLogger
log = getLogger(__name__)


def create_new_technic(data: dict):
    technic = Technic.objects.create(
        title=data['title'],
        type=data['type'],
        attached_driver=data['attached_driver'],
        supervisor_technic=data['supervisor'],
        id_information=data['id_information'],
        description=data['description']
    )
    log.info(f'Техника {technic.title} [{technic.id_information}] была добавлена')


def edit_technic(technic_id, data: dict):
    try:
        technic = Technic.objects.get(pk=technic_id)
        technic.title = data['title']
        technic.type = data['type']
        technic.attached_driver = data['attached_driver']
        technic.supervisor_technic = data['supervisor']
        technic.id_information = data['id_information']
        technic.description = data['description']
        technic.save()
        log.info(f'Техника {technic.title} [{technic.id_information}] была изменена')
    except Technic.DoesNotExist:
        log.error(f'Техники с id={technic_id} не существует')


def check_technic_data(data: dict) -> dict | None:
    out = {}
    log.info('Проверка technic_data')
    title = data.get('title')
    tech_type = data.get('type')
    id_information = data.get('id_information')
    description = data.get('description')
    attached_driver = data.get('attached_driver')
    supervisor = data.get('supervisor')

    if supervisor not in (ASSETS.MECHANIC, ASSETS.SUPPLY):
        # data['supervisor'] = ASSETS.MECHANIC
        out['supervisor'] = ASSETS.MECHANIC

    if attached_driver:
        try:
            driver = User.objects.get(pk=attached_driver)
            # data['attached_driver'] = driver
            out['attached_driver'] = driver
        except User.DoesNotExist:
            log.error(f'Прикрепленного водителя с id={attached_driver} не существует')
            # data['attached_driver'] = None
            out['attached_driver'] = None
    else:
        out['attached_driver'] = None

    if all((title, tech_type, id_information)):
        log.info(f'Данные: (title, tech_type, id_information) в порядке')
        out['title'] = title
        out['type'] = tech_type
        out['id_information'] = id_information
        out['description'] = description
        out['supervisor'] = supervisor
        return out
    else:
        log.error('Ошибка с данными: (title, tech_type, id_information) при проверке')
        return None


def add_or_edit_technic(data, technic_id=None):
    prepare_data = check_technic_data(data)
    if technic_id:
        if prepare_data:
            edit_technic(technic_id, prepare_data)
        else:
            log.error('Ошибка с данными "user_data" при изменении техники')
    else:
        if prepare_data:
            create_new_technic(prepare_data)
        else:
            log.error('Ошибка с данными "user_data" при создании техники')


def delete_technic(technic_id):
    try:
        technic = Technic.objects.get(pk=technic_id)
        technic.is_deleted = True
        technic.save(update_fields=['isArchive'])
        log.info(f'Техника {technic.title} [{technic.id_information}] был помещена в архив')
        return technic
    except Technic.DoesNotExist:
        log.error(f'Техники с id={technic_id} не существует')
        return None
