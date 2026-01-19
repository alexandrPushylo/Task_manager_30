from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationMaterialSchema(BaseModel):
    id: int
    application_today: int = Field(description="Заявка на объект id")
    description: str = Field(max_length=4096, description="Описание")
    isChecked: bool = Field(description='Проверенна?')
    is_cancelled: bool = Field(description='Отменена?')
    isArchive: bool = Field(description="Архивирован?")


class EditApplicationMaterialSchema(BaseModel):
    application_today_id: int
    description: str
