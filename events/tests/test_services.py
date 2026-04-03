import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from events.models import Event, EventDate, ParticipantVote, Vote
from events.services import (
    EventNotFoundError,
    aggregate_votes_by_date,
    create_event,
    get_event_or_404,
    get_participant_votes,
    suitable_dates_for_all,
    upsert_participant_vote,
    validate_event_dates,
    validate_vote_event_consistency,
)


@pytest.mark.django_db
def test_validate_event_dates_rejects_past_dates():
    past = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        validate_event_dates([past])


@pytest.mark.django_db
def test_create_event_creates_eventdate_rows():
    today = datetime.date.today()
    dates = [
        (today + datetime.timedelta(days=1)).isoformat(),
        (today + datetime.timedelta(days=2)).isoformat(),
    ]
    event = create_event(name="Party", dates=dates)

    eds = EventDate.objects.filter(event=event).order_by("date")
    assert eds.count() == 2
    assert eds[0].date.isoformat() == dates[0]


@pytest.mark.django_db
def test_upsert_participant_vote_creates_and_removes_votes(sample_data):
    # create event and dates
    event = sample_data.create_event()
    user = get_user_model().objects.create_user(
        username="john", email="john@example.com", password="test-pass-123"
    )
    # add initial vote for John
    upsert_participant_vote(event, user, [sample_data.event_dates[0]])

    pv = ParticipantVote.objects.get(event=event, user=user)
    votes = get_participant_votes(pv)
    assert len(votes) == 1

    # update votes to a different date
    upsert_participant_vote(event, user, [sample_data.event_dates[1]])
    pv.refresh_from_db()
    votes = get_participant_votes(pv)
    assert len(votes) == 1
    assert votes[0] == sample_data.event_dates[1]


@pytest.mark.django_db
def test_validate_vote_event_consistency_raises_for_cross_event_date(sample_data):
    event_a = sample_data.create_event()
    event_b = sample_data.create_event()

    participant = ParticipantVote.objects.create(event=event_a, name="Alice")
    date_for_event_b = EventDate.objects.filter(event=event_b).first()

    with pytest.raises(
        ValidationError,
        match="does not belong to the participant's event",
    ):
        validate_vote_event_consistency(participant.id, date_for_event_b.id)


@pytest.mark.django_db
def test_validate_vote_event_consistency_passes_for_same_event(sample_data):
    event = sample_data.create_event()
    participant = ParticipantVote.objects.create(event=event, name="Alice")
    date = EventDate.objects.filter(event=event).first()

    validate_vote_event_consistency(participant.id, date.id)


@pytest.mark.django_db
def test_get_event_or_404_raises_domain_error_for_missing_event():
    with pytest.raises(EventNotFoundError):
        get_event_or_404(999999)


@pytest.mark.django_db
def test_upsert_participant_vote_is_idempotent(sample_data):
    event = sample_data.create_event()
    user = get_user_model().objects.create_user(
        username="idempotent-user",
        email="idempotent@example.com",
        password="test-pass-123",
    )
    dates = [sample_data.event_dates[0], sample_data.event_dates[1]]

    upsert_participant_vote(event, user, dates)
    upsert_participant_vote(event, user, dates)

    participant = ParticipantVote.objects.get(event=event, user=user)
    votes = Vote.objects.filter(participant=participant)
    assert votes.count() == 2
    assert set(v.event_date.date.isoformat() for v in votes) == set(dates)


@pytest.mark.django_db
def test_create_event_rolls_back_on_partial_failure():
    today = datetime.date.today()
    dates = [
        (today + datetime.timedelta(days=1)).isoformat(),
        (today + datetime.timedelta(days=2)).isoformat(),
    ]

    with patch(
        "events.services.event_service.EventDate.objects.get_or_create",
        side_effect=[(None, True), RuntimeError("boom")],
    ):
        with pytest.raises(RuntimeError, match="boom"):
            create_event(name="Rollback Event", dates=dates)

    assert not Event.objects.filter(name="Rollback Event").exists()


@pytest.mark.django_db
def test_upsert_participant_vote_rolls_back_on_vote_write_failure(sample_data):
    event = sample_data.create_event()
    user = get_user_model().objects.create_user(
        username="rollback-user",
        email="rollback@example.com",
        password="test-pass-123",
    )

    with patch(
        "events.services.vote_service.Vote.objects.bulk_create",
        side_effect=RuntimeError("write failed"),
    ):
        with pytest.raises(RuntimeError, match="write failed"):
            upsert_participant_vote(event, user, [sample_data.event_dates[0]])

    assert not ParticipantVote.objects.filter(event=event, user=user).exists()
    assert not Vote.objects.exists()


@pytest.mark.django_db
def test_aggregate_votes_by_date_query_count_is_bounded(sample_data):
    event = sample_data.create_event()
    sample_data.add_votes(
        event,
        {
            "Alice": [sample_data.event_dates[0], sample_data.event_dates[1]],
            "Bob": [sample_data.event_dates[0]],
            "Charlie": [sample_data.event_dates[1]],
        },
    )

    with CaptureQueriesContext(connection) as queries:
        result = aggregate_votes_by_date(event)

    assert result
    assert len(queries) <= 3


@pytest.mark.django_db
def test_suitable_dates_for_all_query_count_is_bounded(sample_data):
    event = sample_data.create_event()
    sample_data.add_votes(
        event,
        {
            "Alice": [sample_data.event_dates[0], sample_data.event_dates[1]],
            "Bob": [sample_data.event_dates[0], sample_data.event_dates[1]],
            "Charlie": [sample_data.event_dates[0]],
        },
    )

    with CaptureQueriesContext(connection) as queries:
        result = suitable_dates_for_all(event)

    assert isinstance(result, list)
    assert len(queries) <= 3


@pytest.mark.django_db
def test_suitable_dates_for_all_ignores_participants_without_votes(sample_data):
    event = sample_data.create_event()
    sample_data.add_votes(
        event,
        {
            "Alice": [sample_data.event_dates[0], sample_data.event_dates[1]],
            "Bob": [sample_data.event_dates[0]],
        },
    )
    ParticipantVote.objects.create(event=event, name="Ghost")

    result = suitable_dates_for_all(event)

    assert len(result) == 1
    assert result[0]["date"] == sample_data.event_dates[0]
    assert set(result[0]["people"]) == {"Alice", "Bob"}


@pytest.mark.django_db
def test_suitable_dates_ignores_non_voting_participants(sample_data):
    event = sample_data.create_event()

    # Two voters overlap on first date -> should be suitable.
    sample_data.create_participant_vote(
        event,
        "awel",
        [sample_data.event_dates[0], sample_data.event_dates[2]],
    )
    sample_data.create_participant_vote(
        event,
        "hooker",
        [sample_data.event_dates[0]],
    )

    # Non-voting participant row must not invalidate suitableDates.
    ParticipantVote.objects.create(event=event, name="no-vote-user")

    suitable = suitable_dates_for_all(event)

    assert suitable == [
        {
            "date": sample_data.event_dates[0],
            "people": ["awel", "hooker"],
        }
    ]
