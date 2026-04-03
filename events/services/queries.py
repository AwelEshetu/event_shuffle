"""Lookup and query helper functions with no orchestration logic."""

import logging
from typing import Any

from django.db.models import QuerySet

from ..models import Event, EventDate, ParticipantVote
from .exceptions import EventNotFoundError


logger = logging.getLogger(__name__)


def normalize_date_value(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip()


def get_event_or_404(event_id: int) -> Event:
    try:
        return Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.warning("Event not found for id=%s", event_id)
        raise EventNotFoundError(f"Event not found for id={event_id}")


def event_date_queryset_for_event(event_id: int) -> QuerySet[EventDate]:
    return EventDate.objects.filter(event_id=event_id).order_by("date")


def participant_selected_dates_queryset(
    participant: ParticipantVote,
) -> QuerySet[EventDate]:
    return EventDate.objects.filter(votes__participant=participant).order_by("date")
