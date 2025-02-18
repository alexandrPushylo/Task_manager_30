from datetime import date

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from dashboard.services.work_day_sheet import get_workday
        from dashboard.services.technic_sheet import prepare_technic_sheets
        today_ = date.today()
        workday = get_workday(today_)
        if workday and workday.status:
            prepare_technic_sheets(workday)
