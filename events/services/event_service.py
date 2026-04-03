"""Event-centric business use cases and read aggregations."""

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from ..models import Event, EventDate, Vote
from .validators import parse_iso_date, validate_event_dates


def list_event_summaries() -> QuerySet[dict[str, Any]]:
    return Event.objects.order_by("id").values("id", "name")


@transaction.atomic
def create_event(name: str, dates: list[str]) -> Event:
    validated = validate_event_dates(dates)
    event = Event.objects.create(name=name)
    for d in validated:
        parsed = parse_iso_date(d)
        EventDate.objects.get_or_create(event=event, date=parsed)
    return event


def aggregate_votes_by_date(event: Event) -> list[dict[str, list[str] | str]]:
    event_dates_qs = EventDate.objects.filter(event=event).order_by("id")
    people_by_date: dict[str, list[str]] = {
        ed.date.isoformat(): [] for ed in event_dates_qs
    }
    seen_people_by_date: dict[str, set[str]] = {
        ed.date.isoformat(): set() for ed in event_dates_qs
    }

    votes_qs = (
        Vote.objects.filter(event_date__event=event)
        .select_related("participant", "participant__user", "event_date")
        .order_by("participant__user__username", "participant__name")
    )
    for vote in votes_qs:
        date_iso = vote.event_date.date.isoformat()
        participant_name = vote.participant.display_name
        if (
            date_iso in people_by_date
            and participant_name not in seen_people_by_date[date_iso]
        ):
            seen_people_by_date[date_iso].add(participant_name)
            people_by_date[date_iso].append(participant_name)

    aggregated: list[dict[str, list[str] | str]] = []
    for event_date in event_dates_qs:
        people = people_by_date.get(event_date.date.isoformat(), [])
        if people:
            aggregated.append({"date": event_date.date.isoformat(), "people": people})

    return aggregated


def suitable_dates_for_all(event: Event) -> list[dict[str, list[str] | str]]:
    event_dates = list(EventDate.objects.filter(event=event).order_by("id"))
    people_by_date: dict[str, set[str]] = {
        event_date.date.isoformat(): set() for event_date in event_dates
    }

    participant_names: list[str] = []
    seen_participants: set[str] = set()

    for vote in (
        Vote.objects.filter(event_date__event=event)
        .select_related("participant", "participant__user", "event_date")
        .order_by("participant__user__username", "participant__name", "event_date__id")
    ):
        participant_name = vote.participant.display_name
        if participant_name not in seen_participants:
            seen_participants.add(participant_name)
            participant_names.append(participant_name)

        people_by_date[vote.event_date.date.isoformat()].add(participant_name)

    if not participant_names:
        return []

    required_names = set(participant_names)

    suitable_dates: list[dict[str, list[str] | str]] = []
    for event_date in event_dates:
        date_iso = event_date.date.isoformat()
        if required_names.issubset(people_by_date.get(date_iso, set())):
            suitable_dates.append({"date": date_iso, "people": participant_names})

    return suitable_dates


def get_event_dates(event: Event) -> list[str]:
    return [
        event_date.date.isoformat()
        for event_date in EventDate.objects.filter(event=event).order_by("id")
    ]
