from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255)


class ParticipantVote(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participant_votes",
    )
    name = models.CharField(max_length=255)


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
