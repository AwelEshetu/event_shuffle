from django.core.exceptions import ValidationError
from rest_framework import serializers

from .services import validate_event_dates


def date_child_field() -> serializers.DateField:
    return serializers.DateField(
        input_formats=["%Y-%m-%d"],
        format="%Y-%m-%d",
        help_text="Date in YYYY-MM-DD format.",
    )


class EventCreateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=255,
        allow_blank=False,
        help_text="Event name.",
    )
    dates = serializers.ListField(
        child=date_child_field(),
        allow_empty=False,
        help_text="Candidate event dates (YYYY-MM-DD). Dates must not be in the past.",
    )

    def validate_dates(self, value):
        try:
            return validate_event_dates(value)
        except ValidationError as exc:
            if hasattr(exc, "message_dict") and exc.message_dict:
                raise serializers.ValidationError(exc.message_dict)
            if hasattr(exc, "messages") and exc.messages:
                raise serializers.ValidationError(exc.messages)
            raise serializers.ValidationError(str(exc))


class VoteCreateSerializer(serializers.Serializer):
    votes = serializers.ListField(
        child=date_child_field(),
        allow_empty=False,
        help_text=(
            "Dates selected by the authenticated participant "
            "(must be one of the event's candidate dates)."
        ),
    )


class EventListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EventListResponseSerializer(serializers.Serializer):
    events = EventListItemSerializer(many=True)


class EventListPaginatedResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    events = EventListItemSerializer(many=True)


class EventCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class DatePeopleSerializer(serializers.Serializer):
    date = serializers.DateField(format="%Y-%m-%d")
    people = serializers.ListField(child=serializers.CharField())


class EventDetailResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    dates = serializers.ListField(child=date_child_field())
    votes = DatePeopleSerializer(many=True)


class EventResultsResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    suitableDates = DatePeopleSerializer(many=True)


class VoteDateValidationErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    invalidDates = serializers.ListField(child=date_child_field())
