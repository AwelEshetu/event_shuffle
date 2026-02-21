import datetime

from django.core.exceptions import ValidationError

from .models import Event, ParticipantVote


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
    return Event.objects.create(name=name, dates=validated)


def aggregate_votes_by_date(event: Event) -> list[dict[str, list[str] | str]]:
    event_dates = [normalize_date_value(date) for date in event.dates]
    people_by_date: dict[str, list[str]] = {date: [] for date in event_dates}

    participant_votes = (
        ParticipantVote.objects.filter(event=event)
        .select_related("event")
        .order_by("name")
    )
    for vote in participant_votes:
        for date in vote.votes:
            normalized_date = normalize_date_value(date)
            if (
                normalized_date in people_by_date
                and vote.name not in people_by_date[normalized_date]
            ):
                people_by_date[normalized_date].append(vote.name)

    aggregated: list[dict[str, list[str] | str]] = []
    for date in event_dates:
        people = people_by_date.get(date, [])
        if people:
            aggregated.append({"date": date, "people": people})

    return aggregated


def suitable_dates_for_all(event: Event) -> list[dict[str, list[str] | str]]:
    participants = list(
        ParticipantVote.objects.filter(event=event)
        .select_related("event")
        .order_by("name")
    )
    if not participants:
        return []

    participant_names = [participant.name for participant in participants]
    participant_vote_sets = [
        {normalize_date_value(date) for date in participant.votes}
        for participant in participants
    ]
    suitable_dates: list[dict[str, list[str] | str]] = []

    for date in [normalize_date_value(date) for date in event.dates]:
        if all(date in vote_set for vote_set in participant_vote_sets):
            suitable_dates.append({"date": date, "people": participant_names})

    return suitable_dates


def get_invalid_vote_dates(event: Event, vote_dates: list[str]) -> list[str]:
    allowed_dates = {normalize_date_value(date) for date in event.dates}
    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    return [date for date in normalized_vote_dates if date not in allowed_dates]


def upsert_participant_vote(
    event: Event, participant_name: str, vote_dates: list[str]
) -> None:
    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    event.participant_votes.update_or_create(
        event=event,
        name=participant_name,
        defaults={"votes": normalized_vote_dates},
    )
