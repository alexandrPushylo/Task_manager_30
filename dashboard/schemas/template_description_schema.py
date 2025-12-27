from pydantic import BaseModel, Field


class TemplateDescriptionSchema(BaseModel):
    id: int
    technic: int = Field(description="Техника id")
    description: str | None = Field(max_length=1024, description="Описание")
    is_auto_mode: bool = Field(description="Автоматический режим")
    is_default_mode: bool = Field(description="Режим по умолчанию")

