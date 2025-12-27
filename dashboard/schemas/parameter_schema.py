from datetime import date, time

from pydantic import BaseModel, Field


class ParameterSchema(BaseModel):
    id: int
    title: str | None = Field(max_length=256, description="Название переменной")
    name: str = Field(max_length=256, description="Имя переменной")
    value: str | None = Field(max_length=512, description="Значение переменной")
    flag: bool = Field(description="Флаг переменной")
    description: str | None = Field(max_length=1024, description="Описание")
    time: time | None
    date: date | None
    permissions: str | None = Field(max_length=32, description="Разрешения")


class CreateParameterSchema(BaseModel):
    title: str | None
    name: str
    value: str | None
    flag: bool
    description: str | None
    time: time | None
    date: date | None
    permissions: str | None

class SetParameterSchema(BaseModel):
    name: str
    value: str | None
    flag: bool
    description: str | None
    time: time | None
    date: date | None
