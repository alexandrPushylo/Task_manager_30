from datetime import date

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from logger import getLogger
        log = getLogger(__name__)

        from dashboard.services.work_day_sheet import get_workday
        from dashboard.services.driver_sheet import prepare_driver_sheet
        today_ = date.today()
        workday = get_workday(today_)
        if workday and workday.status:
            prepare_driver_sheet(workday)
            log.info('CRON: prepare_driver_sheet()')
