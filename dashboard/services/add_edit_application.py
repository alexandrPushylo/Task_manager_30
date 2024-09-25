import json

from dashboard.models import TechnicSheet
from logger import getLogger

log = getLogger(__name__)


def get_technic_driver_list(technic_titles: dict, technic_sheets: TechnicSheet.objects) -> list:
    """
    :param technic_titles: {technic.title_short: technic.title}
    :param technic_sheets: TechnicSheet.objects
    :return:
    """
    technic_driver_list = []
    for technic_title in technic_titles:
        technic_driver_list.append({
            'title_short': technic_title['short_title'],
            'title': technic_title['title'],
            'status_busies_list': technic_title['status_busies_list'],
            'technic_sheets': technic_sheets.filter(technic__title=technic_title['title']).order_by('driver_sheet__driver__last_name')
        })
    return technic_driver_list

def get_technic_driver_list_for_json(technic_titles: dict, technic_sheets: TechnicSheet.objects) -> list:
    """
    :param technic_titles: {technic.title_short: technic.title}
    :param technic_sheets: TechnicSheet.objects
    :return:
    """
    technic_driver_list = []
    for technic_title in technic_titles:
        technic_driver_list.append({
            'title_short': technic_title['short_title'],
            'title': technic_title['title'],
            'status_busies_list': technic_title['status_busies_list'],
            'technic_sheets': json.dumps(list(technic_sheets.filter(technic__title=technic_title['title']).values(
                'id',
                'driver_sheet__driver__last_name',
            )))
        })
    return technic_driver_list
