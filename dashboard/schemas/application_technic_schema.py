from pydantic import BaseModel, Field


class ApplicationTechnicSchema(BaseModel):
    id: int
    application_today: int = Field(description="Заявка на объект id")
    technic_sheet: int | None = Field(description="Отметка техники id")
    description: str | None = Field(max_length=4096, description="Описание")
    isChecked: bool = Field(description='Проверенна?')
    is_cancelled: bool = Field(description='Отменена?')
    isArchive: bool = Field(description="Архивирован?")
    priority: int = Field(ge=0, description="Приоритет заявки")
    id_orig_app: int | None = Field(description="Ид ApplicationTechnic")


class EditApplicationTechnicSchema(BaseModel):
    application_today_id: int
    technic_sheet_id: int | None
    description: str | None


class ApplicationTechnicForMechanicSchema(BaseModel):
    technic_sheet__id: int
    application_today__construction_site__address: str
    application_today__construction_site__foreman__last_name: str | None
    description: str | None

