from datetime import date

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class WeekDayValidator:
    def __init__(self, valid_weekdays: list):
        self.valid_weekdays = valid_weekdays

    def __call__(self, value: date):
        if value.weekday() not in self.valid_weekdays:
            raise ValidationError("Weekday is not valid!")
