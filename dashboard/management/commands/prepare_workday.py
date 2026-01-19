from datetime import date

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from logger import getLogger

        log = getLogger(__name__)
        from dashboard.services.work_day_sheet import WorkDayService
        today_ = date.today()
        WorkDayService.prepare_workday_sheet(today_)
        log.info('CRON: prepare_workday()')




