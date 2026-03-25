import datetime

import pytest
from django.core.exceptions import ValidationError

from events.models import EventDate, ParticipantVote
from events.services import (create_event, get_participant_votes,
                             upsert_participant_vote, validate_event_dates)


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
    # add initial vote for John
    upsert_participant_vote(event, "John", [sample_data.event_dates[0]])

    pv = ParticipantVote.objects.get(event=event, name="John")
    votes = get_participant_votes(pv)
    assert len(votes) == 1

    # update votes to a different date
    upsert_participant_vote(event, "John", [sample_data.event_dates[1]])
    pv.refresh_from_db()
    votes = get_participant_votes(pv)
    assert len(votes) == 1
    assert votes[0] == sample_data.event_dates[1]
