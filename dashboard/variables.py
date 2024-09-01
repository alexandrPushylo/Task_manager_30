# template = {'title': '', 'name': ''}
import datetime

#   ===========================================================================================================

VAR_DEFAULT_PASSWORD = {
    'title': 'Пароль по умолчанию',
    'name': 'default_password',
    'value': '1234',
}
VAR_TIME_RECEPTION_OF_TECHNICS = {
    'title': 'Время приема заявок на технику',
    'name': 'time_reception_of_technics',
    # 'time': datetime.now().time().replace(hour=16, minute=0, second=0, microsecond=0),
    'time': datetime.time(hour=16, minute=0),
    'flag': True,
}
VAR_TIME_RECEPTION_OF_MATERIALS = {
    'title': 'Время приема заявок на материалы',
    'name': 'time_reception_of_materials',
    # 'time': datetime.now().time().replace(hour=16, minute=0, second=0, microsecond=0),
    'time': datetime.time(hour=16, minute=0),
    'flag': True,
}
VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE = {
    'title': 'Задание по умолчанию для "спец. объекта"',
    'name': 'default_task_desc_for_spec_site',
    'value': 'Дробить бетон и асфальт',
}


#   ===========================================================================================================

# Для prepare_variables() - automatic creation of variables
VARIABLES_LIST = (
    VAR_DEFAULT_PASSWORD,
    VAR_TIME_RECEPTION_OF_TECHNICS,
    VAR_TIME_RECEPTION_OF_MATERIALS,
    VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE
)

