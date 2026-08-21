from datetime import date, datetime, timedelta, timezone, time
from decimal import Decimal

from bot.services import subject_service, activity_service, absence_service, grade_service, reminder_service, export_service


def test_build_user_export_with_no_data(db, user):
    payload = export_service.build_user_export(db, user)

    assert payload["usuario"] == {"nome": "Ana", "username": "ana_tg"}
    assert payload["materias"] == []
    assert payload["lembretes_pendentes"] == []


def test_build_user_export_nests_activities_absences_and_grades_under_subject(db, user):
    subject = subject_service.create_subject(
        db, user, "Cálculo I", "Prof. Y", "Terça", "B2",
        time(19, 0), time(20, 40), 1, total_classes=40,
    )
    activity_service.create_activity(db, user, subject, "P1", date(2026, 9, 10), "trazer calculadora", "prova")
    absence_service.add_absence(db, user, subject, date(2026, 8, 5), 2, "atestado")
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    reminder_service.create_reminder(db, user, "Estudar pra P2", datetime.now(timezone.utc) + timedelta(days=2))

    payload = export_service.build_user_export(db, user)

    assert len(payload["materias"]) == 1
    subject_data = payload["materias"][0]
    assert subject_data["nome"] == "Cálculo I"
    assert subject_data["horario_inicio"] == "19:00"
    assert subject_data["horario_fim"] == "20:40"
    assert subject_data["total_aulas"] == 40
    assert subject_data["total_faltas"] == 2

    assert subject_data["atividades"] == [
        {"tipo": "prova", "nome": "P1", "data_entrega": "10/09/2026", "observacoes": "trazer calculadora"}
    ]
    assert subject_data["faltas"] == [
        {"data": "05/08/2026", "quantidade": 2, "observacoes": "atestado"}
    ]
    assert subject_data["notas"] == [{"nome": "P1", "valor": "7.50"}]

    assert len(payload["lembretes_pendentes"]) == 1
    assert payload["lembretes_pendentes"][0]["mensagem"] == "Estudar pra P2"


def test_build_user_export_only_includes_own_data(db, user):
    from bot.services import user_service
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    subject_service.create_subject(
        db, other_user, "Matéria de outra pessoa", "Prof. Z", "Segunda", "C1", None, None, 1
    )

    payload = export_service.build_user_export(db, user)
    assert payload["materias"] == []


def test_build_activities_ics_empty_list_is_still_valid_calendar():
    ics = export_service.build_activities_ics([])

    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")
    assert "VERSION:2.0" in ics
    assert "BEGIN:VEVENT" not in ics


def test_build_activities_ics_generates_one_vevent_per_activity(db, user):
    subject = subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1
    )
    activity_service.create_activity(db, user, subject, "P1", date(2026, 9, 10), None, "prova")
    activity_service.create_activity(db, user, subject, "Trabalho Final", date(2026, 9, 15), None, "trabalho")

    activities = activity_service.get_activities_by_user(db, user)
    ics = export_service.build_activities_ics(activities)

    assert ics.count("BEGIN:VEVENT") == 2
    assert ics.count("END:VEVENT") == 2
    assert "SUMMARY:Prova: P1 — Cálculo I" in ics
    assert "SUMMARY:Trabalho: Trabalho Final — Cálculo I" in ics
    assert "DTSTART;VALUE=DATE:20260910" in ics
    assert "DTEND;VALUE=DATE:20260911" in ics  # fim é exclusivo (RFC 5545): due_date + 1 dia


def test_build_activities_ics_escapes_special_characters(db, user):
    subject = subject_service.create_subject(
        db, user, "Cálculo I, com vírgula", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1
    )
    activity_service.create_activity(
        db, user, subject, "P1: Prova; especial", date(2026, 9, 10),
        "linha 1\nlinha 2, com vírgula; e ponto-e-vírgula", "prova"
    )

    activities = activity_service.get_activities_by_user(db, user)
    ics = export_service.build_activities_ics(activities)

    assert r"P1: Prova\; especial" in ics
    assert r"Cálculo I\, com vírgula" in ics
    assert r"linha 1\nlinha 2\, com vírgula\; e ponto-e-vírgula" in ics.replace("\r\n ", "")


def test_build_activities_ics_folds_long_lines():
    long_line = "x" * 200
    folded = export_service._fold_ics_line(long_line)

    # cada linha física (separada por CRLF) deve ter no máximo 75 octets
    for physical_line in folded.split('\r\n'):
        assert len(physical_line.encode('utf-8')) <= 75
    # remontando (removendo as quebras e o espaço de continuação) recupera o texto original
    assert folded.replace('\r\n ', '') == long_line
