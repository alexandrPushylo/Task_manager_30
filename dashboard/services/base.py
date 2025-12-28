from datetime import date, datetime

from django.db import models
from pydantic import BaseModel

from config.settings import USE_CACHE
from logger import getLogger

log = getLogger(__name__)


class BaseService:
    model: models.Model
    schema: BaseModel
    CACHE_TTL = 10
    USE_CACHE = USE_CACHE

    TODAY: date = date.today()
    NOW = lambda: datetime.now().time()
