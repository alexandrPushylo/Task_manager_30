from datetime import datetime, timezone

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: int
    username: str = Field(max_length=150)
    first_name: str | None = Field(max_length=150)
    last_name: str | None = Field(max_length=150)
    is_staff: bool
    is_active: bool

    supervisor_user_id: int | None = Field(default=None, description='Ид руководителя')
    post: str = Field(max_length=20, description="Должность")
    telephone: str | None = Field(max_length=20, default=None, description="Телефон")
    telegram_id_chat: str | None = Field(max_length=128, default=None, description='Telegram id chat')

    isArchive: bool = Field(description="Архивирован?")

    is_show_panel: bool = Field(description="Показывать панель")
    is_show_saved_app: bool = Field(description="Показывать сохраненные заявки")
    is_show_absent_app: bool = Field(description="Показывать отсутствующие заявки")
    is_show_technic_app: bool = Field(description="Показывать заявки на технику")
    is_show_material_app: bool = Field(description="Показывать заявки на материалы")
    is_show_deleted_app: bool = Field(description="Показывать удаленные заявки")

    filter_construction_site: int = Field(default=0, description="Фильтр по строительному объекту")
    filter_foreman: int = Field(default=0, description="Фильтр по прорабу")
    filter_technic: str | None = Field(default=None, description="Фильтр по технике")
    sort_by: str | None = Field(default=None, description="Сортировать по:")

    color_title: str = Field(max_length=8, default="#000000", description='Цвет названия объекта')
    font_size: int = Field(default=10, description="Размер шрифта для описания заявки")
    last_login: datetime | None = Field(description="Последний вход")


class EditUserSchema(BaseModel):
    username: str = Field(max_length=150)
    first_name: str = Field(max_length=150)
    last_name: str = Field(max_length=150)
    password: str

    supervisor_user_id: int | None = Field(default=None)
    post: str | None = Field(default=None, max_length=20)
    telephone: str | None = Field(max_length=20, default=None)
