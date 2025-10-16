import os
import datetime

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        from logger import getLogger
        from django.conf import settings

        log = getLogger(__name__)

        info_log_file = "info.log"
        info_target = f'info_{datetime.date.today()}:{datetime.datetime.now().time().strftime("%H-%M")}.log'
        error_log_file = "errors.log"
        error_target = f'error_{datetime.date.today()}:{datetime.datetime.now().time().strftime("%H-%M")}.log'

        path_log_dir = os.path.join(settings.BASE_DIR, 'logs')

        path_info_log_file = os.path.join(path_log_dir, info_log_file)
        path_info_target = os.path.join(path_log_dir, info_target)

        path_error_log_file = os.path.join(path_log_dir, error_log_file)
        path_error_target = os.path.join(path_log_dir, error_target)

        if not os.path.exists(path_log_dir):
            os.makedirs(path_log_dir)

        info_logfile_size = os.path.getsize(path_info_log_file)
        error_logfile_size = os.path.getsize(path_error_log_file)

        if info_logfile_size > 0:
            os.popen(f"cp {path_info_log_file} {path_info_target}")
            open(path_info_log_file, 'w').close()
            log.info(f"Moved {path_info_log_file} to {info_target}")
        if error_logfile_size > 0:
            os.popen(f"cp {path_error_log_file} {path_error_target}")
            open(path_error_log_file, 'w').close()
            log.info(f"Moved {path_error_log_file} to {error_target}")
