from pydantic import BaseModel

from dashboard.schemas.user_schema import UserSchema


class BusiestTechnicDataSchema(BaseModel):
    technic_title: str
    free_technic_sheet_count: int
    total_technic_sheet_count: int
    id_list: list[int]
    all_applications_count: int
    need_technics_count: int


class FilterDataSchema(BaseModel):
    filter_foreman_list: list
    filter_construction_site_list: list
    filter_technic_list: list[str]
    sort_by_list: dict[str, str]


class LoginDataSchema(BaseModel):
    username: str
    password: str
