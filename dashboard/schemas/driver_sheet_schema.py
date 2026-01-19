from datetime import datetime

from pydantic import BaseModel, Field


class DriverSheetSchema(BaseModel):
    id: int
    driver: int = Field(description="Водитель id")
    status: bool = Field(description="Статус водителя")
    date: int = Field(description="Дата id")
    isArchive: bool = Field(description="Архивирован?")


class EditDriverSheetSchema(BaseModel):
    driver: int = Field()
    status: bool = Field()
    date: int = Field()
    isArchive: bool = Field()
