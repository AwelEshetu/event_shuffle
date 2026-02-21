from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255)
    dates = models.JSONField()


class ParticipantVote(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participant_votes",
    )
    name = models.CharField(max_length=255)
    votes = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "name"],
                name="unique_vote_per_person_per_event",
            )
        ]
