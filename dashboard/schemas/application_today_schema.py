from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ApplicationTodaySchema(BaseModel):
    id: int
    construction_site: int = Field(description="Строительный объект id")
    description: str | None = Field(max_length=1024, description="Примечание для объекта")
    isArchive: bool = Field(description="Архивирован?")
    is_edited: bool = Field(description="Был отредактирован?")
    date: int = Field(description="Дата id")
    is_application_send: bool = Field(description="Заявка отправлена?")
    status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"]


class EditApplicationTodaySchema(BaseModel):
    construction_site: int
    description: str | None
    isArchive: bool
    is_edited: bool
    date: int
    is_application_send: bool
    status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"]


class CreateApplicationTodaySchema(BaseModel):
    construction_site_id: int
    date_id: int

