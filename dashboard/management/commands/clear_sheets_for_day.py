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

        log.info("CRON: starting... clear_sheets_for_day")
        ds, ts = Utilities.clear_sheets_for_day(workday, lt=0, gt=7)
        log.info(f"CRON: {ds} driver_sheets has been deleted\n\tCRON: {ts} technic_sheets has been deleted")


