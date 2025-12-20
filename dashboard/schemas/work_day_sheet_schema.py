import datetime

from pydantic import BaseModel, Field


class WorkDaySchema(BaseModel):
    id: int
    date: datetime.date = Field(description="Дата")
    status: bool = Field(description="Рабочий день")
    accept_mode: str = Field(max_length=32, description="Режим приема заявок")
    isArchive: bool = Field(description="Архивирован?")
    is_all_application_send: bool = Field(description="Заявки отправлены?")


class WorkDaysWithWeekdaySchema(WorkDaySchema):
    weekday:str = Field(max_length=12)