# api/schemas.py
#
# Modelos Pydantic de request/response da API. Espelham os models de
# bot/db/models.py, mas são um contrato próprio (não os mesmos objetos) —
# assim uma mudança de coluna não vaza sem querer pra fora da API.

from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel


class UserOut(BaseModel):
    user_id: int
    first_name: str
    username: str | None = None
    notifications_enabled: bool
    notification_hour: int

    model_config = {"from_attributes": True}


class SubjectOut(BaseModel):
    id: int
    name: str
    professor: str | None = None
    day_of_week: str
    room: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    semestre: int | None = None
    total_classes: int | None = None
    total_absences: int

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: int
    activity_type: str
    name: str
    due_date: date
    notes: str | None = None
    subject_id: int
    subject_name: str


class AbsenceOut(BaseModel):
    id: int
    absence_date: date
    quantity: int
    notes: str | None = None
    subject_id: int
    subject_name: str


class GradeOut(BaseModel):
    id: int
    name: str
    value: Decimal
    subject_id: int
    subject_name: str
