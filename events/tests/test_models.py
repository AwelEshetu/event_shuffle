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
