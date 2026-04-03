import datetime

import pytest
from django.db import IntegrityError

from events.models import EventDate, ParticipantVote, Vote


@pytest.mark.django_db
def test_eventdate_unique_constraint(sample_data):
    event = sample_data.create_event()
    d = datetime.date.fromisoformat(sample_data.event_dates[0])
    ed, created = EventDate.objects.get_or_create(event=event, date=d)
    assert created or ed is not None

    with pytest.raises(IntegrityError):
        EventDate.objects.create(event=event, date=d)


@pytest.mark.django_db
def test_vote_unique_constraint(sample_data):
    event = sample_data.create_event()
    pv = ParticipantVote.objects.create(event=event, name="Alice")
    d = datetime.date.fromisoformat(sample_data.event_dates[0])
    ed, created = EventDate.objects.get_or_create(event=event, date=d)

    Vote.objects.create(participant=pv, event_date=ed)

    with pytest.raises(IntegrityError):
        Vote.objects.create(participant=pv, event_date=ed)


@pytest.mark.django_db
def test_model_string_representations(sample_data):
    event = sample_data.create_event()
    event_date = EventDate.objects.filter(event=event).order_by("date").first()
    participant = ParticipantVote.objects.create(event=event, name="Alice")
    vote = Vote.objects.create(participant=participant, event_date=event_date)

    assert str(event) == event.name
    assert str(participant) == f"Alice ({event.name})"
    assert str(event_date) == f"{event.name} - {event_date.date.isoformat()}"
    assert str(vote) == f"Alice -> {event_date.date.isoformat()}"
