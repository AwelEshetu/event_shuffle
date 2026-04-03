"""Vote-specific business use cases, including upsert and sync operations."""

from collections.abc import Iterable
from typing import Protocol

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Event, EventDate, ParticipantVote, Vote
from .queries import normalize_date_value
from .validators import parse_iso_date


class AuthenticatedUser(Protocol):
    is_authenticated: bool

    def get_username(self) -> str: ...


def sync_participant_vote_dates(
    participant: ParticipantVote,
    selected_dates: Iterable[EventDate],
) -> None:
    selected_ids = {event_date.id for event_date in (selected_dates or [])}

    Vote.objects.filter(participant=participant).exclude(
        event_date_id__in=selected_ids
    ).delete()

    existing_ids = set(
        Vote.objects.filter(participant=participant).values_list(
            "event_date_id", flat=True
        )
    )
    Vote.objects.bulk_create(
        [
            Vote(participant=participant, event_date_id=event_date_id)
            for event_date_id in selected_ids - existing_ids
        ]
    )


def get_invalid_vote_dates(event: Event, vote_dates: list[str]) -> list[str]:
    allowed_dates = {
        event_date.date.isoformat()
        for event_date in EventDate.objects.filter(event=event)
    }
    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    return [date for date in normalized_vote_dates if date not in allowed_dates]


@transaction.atomic
def upsert_participant_vote(
    event: Event,
    user: AuthenticatedUser,
    vote_dates: list[str],
) -> None:
    if user is None or not getattr(user, "is_authenticated", False):
        raise ValidationError("Authenticated user is required for voting.")

    normalized_vote_dates = [normalize_date_value(date) for date in vote_dates]
    participant_vote, _ = ParticipantVote.objects.get_or_create(
        event=event,
        user=user,
        defaults={"name": user.get_username()},
    )
    participant_vote = ParticipantVote.objects.select_for_update().get(
        pk=participant_vote.pk
    )

    if participant_vote.name != user.get_username():
        participant_vote.name = user.get_username()
        participant_vote.save(update_fields=["name"])

    parsed_dates = []
    for date_str in normalized_vote_dates:
        try:
            parsed_dates.append(parse_iso_date(date_str))
        except ValidationError:
            continue

    event_dates = list(EventDate.objects.filter(event=event, date__in=parsed_dates))
    desired_ids = {event_date.id for event_date in event_dates}

    existing_ids = set(
        Vote.objects.filter(participant=participant_vote).values_list(
            "event_date_id", flat=True
        )
    )

    Vote.objects.bulk_create(
        [
            Vote(participant=participant_vote, event_date_id=event_date.id)
            for event_date in event_dates
            if event_date.id not in existing_ids
        ]
    )

    to_delete = existing_ids - desired_ids
    if to_delete:
        Vote.objects.filter(
            participant=participant_vote,
            event_date_id__in=to_delete,
        ).delete()


def get_participant_votes(participant: ParticipantVote) -> list[str]:
    return [
        vote.event_date.date.isoformat()
        for vote in Vote.objects.filter(participant=participant)
        .select_related("event_date")
        .order_by("event_date__id")
    ]
