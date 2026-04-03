import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from events.admin import ParticipantVoteAdmin, ParticipantVoteAdminForm
from events.models import EventDate, ParticipantVote, Vote


@pytest.mark.django_db
def test_participant_vote_form_filters_dates_by_event_in_post_data(sample_data):
    event_a = sample_data.create_event()
    event_b = sample_data.create_event()

    form = ParticipantVoteAdminForm(data={"event": str(event_a.id), "name": "Alice"})

    assert list(form.fields["selected_dates"].queryset) == list(
        EventDate.objects.filter(event=event_a).order_by("date")
    )
    assert not form.fields["selected_dates"].queryset.filter(event=event_b).exists()


@pytest.mark.django_db
def test_participant_vote_form_shows_dates_on_add_form(sample_data):
    sample_data.create_event()

    form = ParticipantVoteAdminForm()

    assert list(form.fields["selected_dates"].queryset) == []


@pytest.mark.django_db
def test_participant_vote_form_shows_dates_for_initial_event(sample_data):
    event = sample_data.create_event()

    form = ParticipantVoteAdminForm(initial={"event": event.id})

    assert list(form.fields["selected_dates"].queryset) == list(
        EventDate.objects.filter(event=event).order_by("date")
    )


@pytest.mark.django_db
def test_participant_vote_form_filters_dates_by_event_on_edit(sample_data):
    event_a = sample_data.create_event()
    event_b = sample_data.create_event()

    participant = ParticipantVote.objects.create(event=event_a, name="Alice")

    form = ParticipantVoteAdminForm(instance=participant)

    assert list(form.fields["selected_dates"].queryset) == list(
        EventDate.objects.filter(event=event_a).order_by("date")
    )
    assert not form.fields["selected_dates"].queryset.filter(event=event_b).exists()


@pytest.mark.django_db
def test_participant_vote_form_prefills_existing_votes(sample_data):
    event = sample_data.create_event()
    participant = ParticipantVote.objects.create(event=event, name="Alice")
    dates = list(EventDate.objects.filter(event=event).order_by("date"))
    Vote.objects.create(participant=participant, event_date=dates[0])

    form = ParticipantVoteAdminForm(instance=participant)

    assert list(form.fields["selected_dates"].initial) == [dates[0]]


@pytest.mark.django_db
def test_participant_vote_form_save_votes_adds_new_votes(sample_data):
    event = sample_data.create_event()
    participant = ParticipantVote.objects.create(event=event, name="Alice")
    dates = list(EventDate.objects.filter(event=event).order_by("date"))

    form = ParticipantVoteAdminForm(
        data={
            "event": str(event.id),
            "name": "Alice",
            "selected_dates": [str(dates[0].id), str(dates[1].id)],
        },
        instance=participant,
    )

    assert form.is_valid(), form.errors
    form.save_votes(participant)

    voted_ids = set(
        Vote.objects.filter(participant=participant).values_list(
            "event_date_id", flat=True
        )
    )
    assert voted_ids == {dates[0].id, dates[1].id}


@pytest.mark.django_db
def test_participant_vote_form_save_votes_removes_deselected(sample_data):
    event = sample_data.create_event()
    participant = ParticipantVote.objects.create(event=event, name="Alice")
    dates = list(EventDate.objects.filter(event=event).order_by("date"))

    # Pre-existing votes on all three dates
    for d in dates:
        Vote.objects.create(participant=participant, event_date=d)

    # Resubmit with only dates[2] selected
    form = ParticipantVoteAdminForm(
        data={
            "event": str(event.id),
            "name": "Alice",
            "selected_dates": [str(dates[2].id)],
        },
        instance=participant,
    )
    assert form.is_valid(), form.errors
    form.save_votes(participant)

    voted_ids = set(
        Vote.objects.filter(participant=participant).values_list(
            "event_date_id", flat=True
        )
    )
    assert voted_ids == {dates[2].id}


@pytest.mark.django_db
def test_participant_vote_admin_exposes_selected_dates_field():
    admin_instance = ParticipantVoteAdmin(ParticipantVote, AdminSite())
    assert "selected_dates" in admin_instance.fields
    assert "user" in admin_instance.fields


@pytest.mark.django_db
def test_participant_vote_admin_prefills_event_from_query_param(sample_data):
    event = sample_data.create_event()
    admin_instance = ParticipantVoteAdmin(ParticipantVote, AdminSite())
    request = RequestFactory().get(
        "/admin/events/participantvote/add/?event=%s" % event.id
    )

    initial = admin_instance.get_changeform_initial_data(request)

    assert str(initial["event"]) == str(event.id)


@pytest.mark.django_db
def test_participant_vote_form_auto_sets_name_from_selected_user(sample_data):
    event = sample_data.create_event()
    user = get_user_model().objects.create_user(
        username="AliceUser",
        email="alice@example.com",
        password="test-pass-123",
    )

    form = ParticipantVoteAdminForm(
        data={
            "event": str(event.id),
            "user": str(user.id),
            "name": "Manual Name",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["name"] == "AliceUser"


@pytest.mark.django_db
def test_participant_vote_form_requires_name_if_user_not_selected(sample_data):
    event = sample_data.create_event()

    form = ParticipantVoteAdminForm(
        data={
            "event": str(event.id),
            "name": "",
        }
    )

    assert not form.is_valid()
    assert "name" in form.errors
