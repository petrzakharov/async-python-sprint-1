from pydantic import BaseModel
from typing import List


class DetailWeather(BaseModel):
    hour: str
    temp: int
    condition: str


class GeneralWeather(BaseModel):
    date: str
    hours: List[DetailWeather]


class Base(BaseModel):
    forecasts: List[GeneralWeather]
