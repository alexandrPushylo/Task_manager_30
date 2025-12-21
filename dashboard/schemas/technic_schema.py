from pydantic import BaseModel, Field


class TechnicSchema(BaseModel):
    id: int
    title: str = Field(max_length=255, description="Название техники")
    type: str = Field(max_length=255, description="Тип техники")
    id_information: str = Field(max_length=256, description="Идентификационная информация")
    description: str | None = Field(max_length=1024, description="Описание")
    attached_driver: int | None = Field(description="Прикрепленный водитель")
    supervisor_technic: str = Field(max_length=100, description="Руководитель")
    isArchive: bool = Field(description="Архивирован?")


class EditTechnicSchema(BaseModel):
    title: str = Field(max_length=255)
    type: str = Field(max_length=255)
    id_information: str = Field(max_length=256)
    description: str | None = Field(max_length=1024)
    attached_driver: int | None = Field()
    supervisor_technic: str = Field(max_length=100)
