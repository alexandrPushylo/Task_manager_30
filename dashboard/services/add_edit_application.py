from dashboard.models import TechnicSheet, ConstructionSite, ApplicationToday, ApplicationTechnic, ApplicationMaterial
from logger import getLogger

log = getLogger(__name__)


def get_technic_driver_list(technic_titles: dict, technic_sheets: TechnicSheet.objects) -> list:
    """
    :param technic_titles: {technic.title_short: technic.title}
    :param technic_sheets: TechnicSheet.objects
    :return:
    """
    technic_driver_list = []
    for title_short, title in technic_titles.items():
        technic_driver_list.append({
            'title_short': title_short,
            'title': title,
            'technic_sheets': technic_sheets.filter(technic__title=title).order_by('driver_sheet__driver__last_name')
        })
    return technic_driver_list
