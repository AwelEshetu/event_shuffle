from drf_spectacular.utils import OpenApiParameter, extend_schema
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.generics import (CreateAPIView, GenericAPIView,
                                     ListAPIView, RetrieveAPIView)
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .serializers import (EventCreateResponseSerializer, EventCreateSerializer,
                          EventDetailResponseSerializer,
                          EventListPaginatedResponseSerializer,
                          EventListResponseSerializer,
                          EventResultsResponseSerializer, VoteCreateSerializer,
                          VoteDateValidationErrorSerializer)
from .services import (aggregate_votes_by_date, create_event, get_event_dates,
                       EventNotFoundError,
                       get_event_or_404, get_invalid_vote_dates,
                       list_event_summaries,
                       suitable_dates_for_all, upsert_participant_vote)


class EventListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "pageSize"
    max_page_size = 100


class EventListView(ListAPIView):
    serializer_class = EventListResponseSerializer
    pagination_class = EventListPagination

    @extend_schema(responses={200: EventListPaginatedResponseSerializer})
    def list(self, request):
        events = list_event_summaries()
        page = self.paginate_queryset(events)

        if page is not None:
            return Response(
                {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "events": list(page),
                },
                status=status.HTTP_200_OK,
            )

        return Response({"events": list(events)}, status=status.HTTP_200_OK)


class EventCreateView(CreateAPIView):
    serializer_class = EventCreateSerializer
    parser_classes = [JSONParser]

    @extend_schema(
        request={"application/json": EventCreateSerializer},
        responses={201: EventCreateResponseSerializer, 400: dict},
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = create_event(
            name=serializer.validated_data["name"],
            dates=serializer.validated_data["dates"],
        )
        return Response({"id": event.id}, status=status.HTTP_201_CREATED)


class EventDetailView(RetrieveAPIView):
    serializer_class = EventDetailResponseSerializer
    lookup_url_kwarg = "id"

    def get_object(self):
        try:
            return get_event_or_404(self.kwargs[self.lookup_url_kwarg])
        except EventNotFoundError as exc:
            raise Http404("Event not found.") from exc

    @extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)],
        responses={200: EventDetailResponseSerializer, 404: dict},
    )
    def retrieve(self, request, *args, **kwargs):
        event = self.get_object()
        return Response(
            {
                "id": event.id,
                "name": event.name,
                "dates": get_event_dates(event),
                "votes": aggregate_votes_by_date(event),
            },
            status=status.HTTP_200_OK,
        )


class EventVoteView(GenericAPIView):
    serializer_class = VoteCreateSerializer
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    def get_event(self, id: int):
        try:
            return get_event_or_404(id)
        except EventNotFoundError as exc:
            raise Http404("Event not found.") from exc

    @extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)],
        request={"application/json": VoteCreateSerializer},
        responses={
            200: EventDetailResponseSerializer,
            400: VoteDateValidationErrorSerializer,
            404: dict,
        },
    )
    def post(self, request, id: int):
        event = self.get_event(id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vote_dates = serializer.validated_data["votes"]
        invalid_dates = get_invalid_vote_dates(event, vote_dates)
        if invalid_dates:
            return Response(
                {
                    "detail": "Vote dates must be part of the event candidate dates.",
                    "invalidDates": invalid_dates,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        upsert_participant_vote(event, request.user, vote_dates)

        return Response(
            {
                "id": event.id,
                "name": event.name,
                "dates": get_event_dates(event),
                "votes": aggregate_votes_by_date(event),
            },
            status=status.HTTP_200_OK,
        )


class EventResultsView(RetrieveAPIView):
    serializer_class = EventResultsResponseSerializer
    lookup_url_kwarg = "id"

    def get_object(self):
        try:
            return get_event_or_404(self.kwargs[self.lookup_url_kwarg])
        except EventNotFoundError as exc:
            raise Http404("Event not found.") from exc

    @extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)],
        responses={200: EventResultsResponseSerializer, 404: dict},
    )
    def retrieve(self, request, *args, **kwargs):
        event = self.get_object()
        return Response(
            {
                "id": event.id,
                "name": event.name,
                "suitableDates": suitable_dates_for_all(event),
            },
            status=status.HTTP_200_OK,
        )
