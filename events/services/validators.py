"""Domain validation and normalization rules for event scheduling flows."""

import datetime
from typing import Any

from django.core.exceptions import ValidationError

from ..models import EventDate, ParticipantVote


def parse_iso_date(value: Any) -> datetime.date:
    try:
        if isinstance(value, datetime.date):
            return value
        return datetime.date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Invalid date format: {value}") from exc


def validate_event_dates(dates: list[str]) -> list[str]:
    if not isinstance(dates, (list, tuple)):
        raise ValidationError("Event dates must be a list of YYYY-MM-DD strings.")

    if not dates:
        raise ValidationError({"dates": "Event must have at least one candidate date."})

    seen = set()
    normalized: list[str] = []
    invalid_dates: list[str] = []
    past_dates: list[str] = []
    today = datetime.date.today()

    for d in dates:
        try:
            parsed = parse_iso_date(d)
        except ValidationError:
            invalid_dates.append(str(d))
            continue

        if parsed.isoformat() in seen:
            raise ValidationError("Event dates must be unique.")
        seen.add(parsed.isoformat())

        if parsed < today:
            past_dates.append(parsed.isoformat())

        normalized.append(parsed.isoformat())

    if invalid_dates:
        raise ValidationError({"dates": f"Invalid date format(s): {invalid_dates}"})
    if past_dates:
        raise ValidationError(
            {"dates": f"Event dates must not be in the past: {past_dates}"}
        )

    return normalized


def resolve_participant_name(user, name: str) -> str:
    if user:
        return user.get_username()

    normalized_name = (name or "").strip()
    if not normalized_name:
        raise ValidationError("Provide a name or select a user.")
    return normalized_name


def validate_vote_event_consistency(participant_id: int, event_date_id: int) -> None:
    if not participant_id or not event_date_id:
        return

    participant_event_id = ParticipantVote.objects.values_list(
        "event_id", flat=True
    ).get(pk=participant_id)
    date_event_id = EventDate.objects.values_list("event_id", flat=True).get(
        pk=event_date_id
    )
    if participant_event_id != date_event_id:
        raise ValidationError(
            "The selected date does not belong to the participant's event."
        )
