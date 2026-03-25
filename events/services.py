import datetime

from django.core.exceptions import ValidationError

from .models import Event, EventDate, ParticipantVote, Vote


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
            parsed = datetime.date.fromisoformat(str(d))
        except Exception:
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


def normalize_date_value(value) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip()


def list_event_summaries() -> list[dict[str, int | str]]:
    return list(Event.objects.order_by("id").values("id", "name"))


def create_event(name: str, dates: list[str]) -> Event:
    validated = validate_event_dates(dates)
    event = Event.objects.create(name=name)
    # create EventDate rows in the same order
    for d in validated:
        try:
            parsed = datetime.date.fromisoformat(str(d))
        except Exception:
            continue
        EventDate.objects.get_or_create(event=event, date=parsed)
    return event


def aggregate_votes_by_date(event: Event) -> list[dict[str, list[str] | str]]:
    # Build mapping from each EventDate -> list of participant names
    event_dates_qs = EventDate.objects.filter(event=event).order_by("id")
    people_by_date: dict[str, list[str]] = {
        ed.date.isoformat(): [] for ed in event_dates_qs
    }

    votes_qs = (
        Vote.objects.filter(event_date__event=event)
        .select_related("participant", "event_date")
        .order_by("participant__name")
    )
    for v in votes_qs:
        d_iso = v.event_date.date.isoformat()
        if d_iso in people_by_date and v.participant.name not in people_by_date[d_iso]:
            people_by_date[d_iso].append(v.participant.name)

    aggregated: list[dict[str, list[str] | str]] = []
    for ed in event_dates_qs:
        people = people_by_date.get(ed.date.isoformat(), [])
        if people:
            aggregated.append({"date": ed.date.isoformat(), "people": people})

    return aggregated


def suitable_dates_for_all(event: Event) -> list[dict[str, list[str] | str]]:
    participants = list(ParticipantVote.objects.filter(event=event).order_by("name"))
    if not participants:
        return []

    participant_names = [p.name for p in participants]
    # Build set of participant names who voted for each EventDate
    event_dates_qs = list(EventDate.objects.filter(event=event).order_by("id"))
    people_by_date: dict[str, set[str]] = {
        ed.date.isoformat(): set() for ed in event_dates_qs
    }

    for v in Vote.objects.filter(event_date__event=event).select_related(
        "participant", "event_date"
    ):
        people_by_date[v.event_date.date.isoformat()].add(v.participant.name)

    suitable_dates: list[dict[str, list[str] | str]] = []
    for ed in event_dates_qs:
        d_iso = ed.date.isoformat()
        if people_by_date.get(d_iso) and all(
            p.name in people_by_date[d_iso] for p in participants
        ):
            suitable_dates.append({"date": d_iso, "people": participant_names})

    return suitable_dates


def get_invalid_vote_dates(event: Event, vote_dates: list[str]) -> list[str]:
    allowed_dates = {
        ed.date.isoformat() for ed in EventDate.objects.filter(event=event)
    }
    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    return [date for date in normalized_vote_dates if date not in allowed_dates]


def upsert_participant_vote(
    event: Event, participant_name: str, vote_dates: list[str]
) -> None:
    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    pv, _ = ParticipantVote.objects.get_or_create(event=event, name=participant_name)

    # find the EventDate rows for the provided dates
    parsed_dates = []
    for d in normalized_vote_dates:
        try:
            parsed_dates.append(datetime.date.fromisoformat(str(d)))
        except Exception:
            continue

    eds = list(EventDate.objects.filter(event=event, date__in=parsed_dates))
    desired_ids = {ed.id for ed in eds}

    # existing vote rows
    existing_ids = set(
        Vote.objects.filter(participant=pv).values_list("event_date_id", flat=True)
    )

    # create missing vote rows
    for ed in eds:
        if ed.id not in existing_ids:
            Vote.objects.create(participant=pv, event_date=ed)

    # remove votes that are no longer desired
    to_delete = existing_ids - desired_ids
    if to_delete:
        Vote.objects.filter(participant=pv, event_date_id__in=to_delete).delete()


def get_event_dates(event: Event) -> list[str]:
    return [
        ed.date.isoformat()
        for ed in EventDate.objects.filter(event=event).order_by("id")
    ]


def get_participant_votes(participant: ParticipantVote) -> list[str]:
    return [
        v.event_date.date.isoformat()
        for v in Vote.objects.filter(participant=participant)
        .select_related("event_date")
        .order_by("event_date__id")
    ]
