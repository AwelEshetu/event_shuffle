from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Event(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class ParticipantVote(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participant_votes",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_votes",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_event_user_vote",
            )
        ]

    @property
    def display_name(self) -> str:
        if self.user_id:
            return self.user.get_username()
        return self.name

    def __str__(self) -> str:
        return f"{self.display_name} ({self.event.name})"


class EventDate(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_dates",
    )
    date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "date"], name="unique_event_date")
        ]

    def __str__(self) -> str:
        return f"{self.event.name} - {self.date.isoformat()}"


class Vote(models.Model):
    participant = models.ForeignKey(
        ParticipantVote,
        on_delete=models.CASCADE,
        related_name="vote_rows",
    )
    event_date = models.ForeignKey(
        EventDate,
        on_delete=models.CASCADE,
        related_name="votes",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "event_date"],
                name="unique_participant_eventdate",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.participant.display_name} -> "
            f"{self.event_date.date.isoformat()}"
        )
