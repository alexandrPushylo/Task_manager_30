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
        info_target = f'info_{datetime.date.today()}.log'
        error_log_file = "errors.log"
        error_target = f'error_{datetime.date.today()}.log'

        path_log_dir = os.path.join(settings.BASE_DIR, 'logs')

        path_info_log_file = os.path.join(path_log_dir, info_log_file)
        path_info_target = os.path.join(path_log_dir, info_target)

        path_error_log_file = os.path.join(path_log_dir, error_log_file)
        path_error_target = os.path.join(path_log_dir, error_target)

        if not os.path.exists(path_log_dir):
            os.makedirs(path_log_dir)

        info_logfile_size = os.path.getsize(path_info_log_file)
        error_logfile_size = os.path.getsize(path_error_log_file)

        print(info_logfile_size)
        print(error_logfile_size)

        if info_logfile_size > 0:
            os.popen(f"cp {path_info_log_file} {path_info_target}")
        if error_logfile_size > 0:
            os.popen(f"cp {path_error_log_file} {path_error_target}")

        # print(os.path.getsize(path_log_dir + error_log_file))
        # with open(path_log_dir + info_log_file, "w") as info_log:
        #     print(os.path.getsize(path_log_dir + info_log_file))
        #     # print(len(info_log.read()))
        #
        # with open(path_log_dir + error_log_file, "w") as error_log:
        #     print(sys.getsizeof(error_log))





# name = 'db.sqlite3'
# out = r"backup"
#
# if not os.path.exists(out):
#     os.makedirs(out)
#
# target = f'{out}{os.sep}{datetime.date.today()}_{datetime.datetime.now().time().strftime("%H-%M")}.sqlite3'
#
# os.popen(f"cp {name} {target}")