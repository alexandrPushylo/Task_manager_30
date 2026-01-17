from datetime import date

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from logger import getLogger
        log = getLogger(__name__)

        from dashboard.services.work_day_sheet import WorkDayService
        from dashboard.utilities import Utilities
        today_ = date.today()
        workday = WorkDayService.get_current_date_data(today_)
        if workday and workday.status:
            Utilities.prepare_driver_sheet(workday)
            log.info('CRON: prepare_driver_sheet() - Done')
        else:
            log.info("CRON: prepare_driver_sheet() - Doesn't work today")

