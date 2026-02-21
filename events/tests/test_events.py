import datetime

import pytest
from django.urls import reverse

from events.models import Event
from events.services import create_event


@pytest.mark.django_db
def test_create_event(client, create_event_payload):
    response = client.post(
        reverse("event-create"),
        data=create_event_payload,
        content_type="application/json",
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert Event.objects.count() == 1


@pytest.mark.django_db
def test_list_events(client, listed_events, listed_events_count):
    response = client.get(reverse("event-list"))

    assert response.status_code == 200
    assert len(response.json()["events"]) == listed_events_count


@pytest.mark.django_db
def test_show_event(client, event_with_user_votes, expected_show_event_votes):
    event = event_with_user_votes

    response = client.get(reverse("event-detail", kwargs={"id": event.id}))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event.id
    assert data["name"] == event.name
    assert data["dates"] == event.dates
    assert data["votes"] == expected_show_event_votes


@pytest.mark.django_db
def test_add_votes_to_event(
    client,
    event_with_user_votes,
    add_vote_payload,
    sample_data,
):
    event = event_with_user_votes

    response = client.post(
        reverse("event-vote", kwargs={"id": event.id}),
        data=add_vote_payload,
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event.id
    assert len(data["votes"]) == 2
    first_vote_people = data["votes"][0]["people"]
    assert sample_data.participants[0] in first_vote_people
    assert sample_data.participants[2] in first_vote_people


@pytest.mark.django_db
def test_add_votes_rejects_invalid_date(client, event, invalid_vote_payload):
    response = client.post(
        reverse("event-vote", kwargs={"id": event.id}),
        data=invalid_vote_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "invalidDates" in response.json()


@pytest.mark.django_db
def test_show_results(client, event_with_votes, expected_suitable_dates, sample_data):
    client.post(
        reverse("event-vote", kwargs={"id": event_with_votes.id}),
        data={
            "name": "Dick",
            "votes": [sample_data.event_dates[0], sample_data.event_dates[1]],
        },
        content_type="application/json",
    )

    response = client.get(reverse("event-results", kwargs={"id": event_with_votes.id}))

    assert response.status_code == 200
    suitable_dates = response.json()["suitableDates"]
    assert len(suitable_dates) == len(expected_suitable_dates)
    assert suitable_dates[0]["date"] == expected_suitable_dates[0]["date"]
    assert set(suitable_dates[0]["people"]) == set(expected_suitable_dates[0]["people"])


@pytest.mark.django_db
def test_list_events_includes_expected_names(client, listed_events, sample_data):
    create_event(name="Jake's secret party", dates=list(sample_data.event_dates))

    response = client.get(reverse("event-list"))

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 3
    names = {event["name"] for event in data["events"]}
    assert names == {"Jake's secret party", "Bowling night", "Tabletop gaming"}


@pytest.mark.django_db
def test_create_event_returns_id(client, create_event_payload):
    response = client.post(
        reverse("event-create"),
        data=create_event_payload,
        content_type="application/json",
    )

    assert response.status_code == 201
    assert "id" in response.json()


@pytest.mark.django_db
def test_create_event_rejects_empty_dates(client):
    response = client.post(
        reverse("event-create"),
        data={"name": "Empty dates", "dates": []},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert (
        "empty" in str(response.json()).lower()
        or "at least one" in str(response.json()).lower()
    )


@pytest.mark.django_db
def test_create_event_rejects_past_dates(client):
    past = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    response = client.post(
        reverse("event-create"),
        data={"name": "Past date", "dates": [past]},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "past" in str(response.json()).lower()


@pytest.mark.django_db
def test_get_event_returns_votes_by_date(
    client,
    event_with_votes,
    sample_data,
):
    response = client.get(reverse("event-detail", kwargs={"id": event_with_votes.id}))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_with_votes.id
    assert data["name"] == "Jake's secret party"
    assert data["dates"] == list(sample_data.event_dates)

    votes_by_date = {entry["date"]: set(entry["people"]) for entry in data["votes"]}
    assert votes_by_date[sample_data.event_dates[0]] == {
        sample_data.participants[0],
        sample_data.participants[1],
        sample_data.participants[3],
        sample_data.participants[4],
    }


@pytest.mark.django_db
def test_add_vote_returns_updated_event(
    client,
    event_with_votes,
    sample_data,
):
    response = client.post(
        reverse("event-vote", kwargs={"id": event_with_votes.id}),
        data={
            "name": "Dick",
            "votes": [sample_data.event_dates[0], sample_data.event_dates[1]],
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_with_votes.id
    assert data["name"] == "Jake's secret party"
    assert data["dates"] == list(sample_data.event_dates)

    votes_by_date = {entry["date"]: set(entry["people"]) for entry in data["votes"]}
    assert votes_by_date[sample_data.event_dates[0]] == {
        sample_data.participants[0],
        sample_data.participants[1],
        sample_data.participants[3],
        sample_data.participants[4],
        "Dick",
    }
    assert votes_by_date[sample_data.event_dates[1]] == {"Dick"}


@pytest.mark.django_db
def test_get_results_returns_suitable_dates(
    client,
    event_with_votes,
    sample_data,
):
    client.post(
        reverse("event-vote", kwargs={"id": event_with_votes.id}),
        data={
            "name": "Dick",
            "votes": [sample_data.event_dates[0], sample_data.event_dates[1]],
        },
        content_type="application/json",
    )

    response = client.get(reverse("event-results", kwargs={"id": event_with_votes.id}))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_with_votes.id
    assert data["name"] == "Jake's secret party"
    assert len(data["suitableDates"]) == 1
    assert data["suitableDates"][0]["date"] == sample_data.event_dates[0]
    assert set(data["suitableDates"][0]["people"]) == {
        sample_data.participants[0],
        sample_data.participants[1],
        sample_data.participants[3],
        sample_data.participants[4],
        "Dick",
    }
