from pydantic import BaseModel, Field


class TechnicSheetSchema(BaseModel):
    id: int
    technic: int = Field(description="Транспортное средство id")
    driver_sheet: int | None = Field(description="Табель водителя id")
    status: bool = Field(description="Статус техники")
    date: int = Field(description="Дата id")
    count_application: int = Field(description="Количество заявок (загруженость)")
    isArchive: bool = Field(description="Архивирован?")


class WorkloadTechnicSheetSchema(BaseModel):
    id: int
    technic__title: str
    driver_sheet_id: int
    count_application: int


class TechnicSheetWithTechnicSchema(BaseModel):
    id: int
    technic: int
    technic__title: str
    driver_sheet: int | None
    driver_sheet__status: bool
    status: bool
    date: int
    count_application: int
    isArchive: bool