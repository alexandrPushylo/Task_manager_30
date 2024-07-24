from enum import Enum
from typing import NamedTuple, Any


class TitleDescriptionType(NamedTuple):
    """Простой тип 'название.описание'"""
    title: str
    description: str

    def get_dict(self) -> dict[str, str]:
        return {self.title: self.description}

    def __str__(self) -> str:
        return f"Title: {self.title}, Description: {self.description}"


class UserPostType(NamedTuple):
    """Тип для user.post"""
    ADMINISTRATOR: TitleDescriptionType
    FOREMAN: TitleDescriptionType
    MASTER: TitleDescriptionType
    DRIVER: TitleDescriptionType
    MECHANIC: TitleDescriptionType
    SUPPLY: TitleDescriptionType
    EMPLOYEE: TitleDescriptionType

    def get_dict(self) -> dict[str, str]:
        return {item.title: item.description
                for item in
                (self.ADMINISTRATOR, self.FOREMAN, self.MASTER, self.DRIVER, self.MECHANIC, self.SUPPLY, self.EMPLOYEE)}


class ApplicationTodayType(NamedTuple):
    """Тип для application_today.status"""
    ABSENT: TitleDescriptionType
    SAVED: TitleDescriptionType
    SUBMITTED: TitleDescriptionType
    APPROVED: TitleDescriptionType
    SEND: TitleDescriptionType

    def get_dict(self) -> dict[str, str]:
        return {item.title: item.description
                for item in (self.ABSENT, self.SAVED, self.SUBMITTED, self.APPROVED, self.SEND)}

    def get_set(self) -> set[str]:
        return set(self.get_dict().values())



