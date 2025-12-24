from datetime import datetime

from pydantic import BaseModel, Field


class ConstructionSiteSchema(BaseModel):
    id: int
    address: str = Field(max_length=512, description="Адрес")
    foreman: int | None = Field(description="Прораб")
    deleted_date: datetime | None = Field(description="Дата удаления")
    status: bool = Field(description="Статус объекта")
    isArchive: bool = Field(description="Архивирован?")


class EditConstructionSiteSchema(BaseModel):
    address: str = Field(max_length=512)
    foreman: int | None = Field(description="Прораб")
