from rest_framework import serializers


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
        help_text="Candidate event dates.",
    )

    def validate_dates(self, value) -> list[str]:
        seen: set[str] = set()
        normalized_dates: list[str] = []

        import datetime

        today = datetime.date.today()
        for date_value in value:
            date_str = date_value.isoformat()
            if date_str in seen:
                raise serializers.ValidationError("Event dates must be unique.")
            if date_value < today:
                raise serializers.ValidationError(
                    {
                        "detail": "Event dates must not be in the past.",
                        "invalidDates": [date_str],
                    }
                )
            seen.add(date_str)
            normalized_dates.append(date_str)

        return normalized_dates


class VoteCreateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=255,
        allow_blank=False,
        help_text="Participant name.",
    )
    votes = serializers.ListField(
        child=date_child_field(),
        allow_empty=False,
        help_text="Dates selected by the participant.",
    )

    def validate_votes(self, value) -> list[str]:
        return [date_value.isoformat() for date_value in value]


class EventListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EventListResponseSerializer(serializers.Serializer):
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
