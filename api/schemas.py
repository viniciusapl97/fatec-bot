# api/schemas.py
#
# Modelos Pydantic de request/response da API. Espelham os models de
# bot/db/models.py, mas são um contrato próprio (não os mesmos objetos) —
# assim uma mudança de coluna não vaza sem querer pra fora da API.

from datetime import date, time
from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, Field

DayOfWeek = Literal["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
ActivityType = Literal["trabalho", "prova"]


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
    # Mesmos campos computados de AttendanceOut, embutidos aqui pra listagens
    # (ex.: banner de risco no dashboard) não precisarem de N chamadas extras
    # a GET /subjects/{id}/attendance — ficam em null/False se total_classes
    # não estiver definido, igual a semântica de AttendanceOut.
    percent: float | None = None
    remaining_allowed: int | None = None
    at_risk: bool = False
    failed: bool = False

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


class AttendanceOut(BaseModel):
    subject_id: int
    total_classes: int | None
    total_absences: int
    percent: float | None = None
    remaining_allowed: int | None = None
    at_risk: bool = False
    failed: bool = False


class SubjectGradesOut(BaseModel):
    subject_id: int
    subject_name: str
    grades: List[GradeOut]
    average: Decimal | None


class SubjectCreate(BaseModel):
    name: str
    professor: str | None = None
    day_of_week: DayOfWeek
    room: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    semestre: int | None = None
    total_classes: int | None = Field(default=None, gt=0)


class SubjectUpdate(BaseModel):
    name: str | None = None
    professor: str | None = None
    day_of_week: DayOfWeek | None = None
    room: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    semestre: int | None = None
    total_classes: int | None = Field(default=None, gt=0)


class ActivityCreate(BaseModel):
    subject_id: int
    activity_type: ActivityType
    name: str
    due_date: date
    notes: str | None = None


class ActivityUpdate(BaseModel):
    subject_id: int | None = None
    name: str | None = None
    due_date: date | None = None
    notes: str | None = None


class AbsenceCreate(BaseModel):
    subject_id: int
    absence_date: date
    quantity: int = Field(gt=0)
    notes: str | None = None


class AbsenceUpdate(BaseModel):
    quantity: int = Field(gt=0)


class GradeCreate(BaseModel):
    subject_id: int
    name: str
    value: Decimal = Field(ge=0)


class GradeUpdate(BaseModel):
    name: str
    value: Decimal = Field(ge=0)


class TelegramLoginPayload(BaseModel):
    """Payload que o Telegram Login Widget devolve pro frontend após o login — ver api/routers/auth.py."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
