from datetime import date

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from logger import getLogger

        log = getLogger(__name__)
        from dashboard.services.work_day_sheet import prepare_workday
        today_ = date.today()
        prepare_workday(today_)
        log.info('CRON: prepare_workday()')




