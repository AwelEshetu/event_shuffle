"""Public service facade preserving stable imports for callers."""

from .event_service import (
    aggregate_votes_by_date,
    create_event,
    get_event_dates,
    list_event_summaries,
    suitable_dates_for_all,
)
from .exceptions import EventNotFoundError
from .queries import (
    event_date_queryset_for_event,
    get_event_or_404,
    normalize_date_value,
    participant_selected_dates_queryset,
)
from .validators import (
    resolve_participant_name,
    validate_event_dates,
    validate_vote_event_consistency,
)
from .vote_service import (
    get_invalid_vote_dates,
    get_participant_votes,
    sync_participant_vote_dates,
    upsert_participant_vote,
)

__all__ = [
    "aggregate_votes_by_date",
    "create_event",
    "EventNotFoundError",
    "event_date_queryset_for_event",
    "get_event_dates",
    "get_event_or_404",
    "get_invalid_vote_dates",
    "get_participant_votes",
    "list_event_summaries",
    "normalize_date_value",
    "participant_selected_dates_queryset",
    "resolve_participant_name",
    "suitable_dates_for_all",
    "sync_participant_vote_dates",
    "upsert_participant_vote",
    "validate_event_dates",
    "validate_vote_event_consistency",
]
