import datetime
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Tuple

import pytest

from events.models import Event, EventDate, ParticipantVote, Vote
from events.services import create_event


@dataclass
class SampleData:
    event_name: str = "Jake's secret party"
    event_dates: Optional[Tuple[str, ...]] = None
    participants: Tuple[str, ...] = ("John", "Julia", "Dick", "Paul", "Daisy")
    listed_events: Tuple[tuple[str, Tuple[str, ...]], ...] = ()

    def __post_init__(self):
        if not self.event_dates:
            today = datetime.date.today()
            self.event_dates = (
                (today + timedelta(days=1)).isoformat(),
                (today + timedelta(days=5)).isoformat(),
                (today + timedelta(days=12)).isoformat(),
            )

    def create_event(self) -> Event:
        if not self.event_dates:
            today = datetime.date.today()
            self.event_dates = (
                (today + timedelta(days=1)).isoformat(),
                (today + timedelta(days=5)).isoformat(),
                (today + timedelta(days=12)).isoformat(),
            )
        return create_event(name=self.event_name, dates=list(self.event_dates))

    def create_participant_vote(
        self, event: Event, name: str, votes: list[str]
    ) -> ParticipantVote:
        pv = ParticipantVote.objects.create(event=event, name=name)
        # create Vote rows linking to EventDate

        for d in votes:
            try:
                parsed = datetime.date.fromisoformat(str(d))
            except Exception:
                continue
            ed = EventDate.objects.filter(event=event, date=parsed).first()
            if ed:
                Vote.objects.create(participant=pv, event_date=ed)
        return pv

    def add_votes(self, event: Event, votes_map: dict[str, list[str]]) -> None:
        for name, votes in votes_map.items():
            self.create_participant_vote(event, name, votes)

    def create_listed_events(self) -> None:
        if not self.listed_events:
            today = datetime.date.today()
            self.listed_events = (
                ("Bowling night", ((today + timedelta(days=14)).isoformat(),)),
                ("Tabletop gaming", ((today + timedelta(days=30)).isoformat(),)),
            )

        for name, dates in self.listed_events:
            create_event(name=name, dates=list(dates))


@pytest.fixture
def sample_data() -> SampleData:
    return SampleData()


@pytest.fixture
def event_name(sample_data) -> str:
    return sample_data.event_name


@pytest.fixture
def event_dates(sample_data) -> list[str]:
    return list(sample_data.event_dates)


@pytest.fixture
def create_event_payload(event_name, event_dates) -> dict:
    return {"name": event_name, "dates": event_dates}


@pytest.fixture
def add_vote_payload(sample_data) -> dict:
    return {
        "name": sample_data.participants[2],
        "votes": [sample_data.event_dates[0], sample_data.event_dates[1]],
    }


@pytest.fixture
def invalid_vote_payload() -> dict:
    future = (datetime.date.today() + timedelta(days=365)).isoformat()
    return {"name": "Someone", "votes": [future]}


@pytest.fixture
def expected_show_event_votes(sample_data) -> list[dict]:
    return [
        {"date": sample_data.event_dates[0], "people": [sample_data.participants[0]]},
        {"date": sample_data.event_dates[1], "people": [sample_data.participants[0]]},
    ]


@pytest.fixture
def expected_suitable_dates(sample_data) -> list[dict]:
    participants = list(sample_data.participants)
    return [
        {
            "date": sample_data.event_dates[0],
            "people": [
                participants[2],
                participants[4],
                participants[0],
                participants[1],
                participants[3],
            ],
        }
    ]


@pytest.fixture
def listed_events_count() -> int:
    return 2


@pytest.fixture
def event(db, sample_data):
    return sample_data.create_event()


@pytest.fixture
def event_with_votes(event, sample_data):
    sample_data.add_votes(
        event,
        {
            sample_data.participants[0]: [sample_data.event_dates[0]],
            sample_data.participants[1]: [
                sample_data.event_dates[0],
                sample_data.event_dates[2],
            ],
            sample_data.participants[3]: [sample_data.event_dates[0]],
            sample_data.participants[4]: [sample_data.event_dates[0]],
        },
    )
    return event


@pytest.fixture
def event_with_user_votes(event, sample_data):
    sample_data.create_participant_vote(
        event,
        sample_data.participants[0],
        [sample_data.event_dates[0], sample_data.event_dates[1]],
    )
    return event


@pytest.fixture
def listed_events(db, sample_data):
    sample_data.create_listed_events()
