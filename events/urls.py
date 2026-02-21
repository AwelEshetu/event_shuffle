from django.urls import path

from .views import (EventCreateView, EventDetailView, EventListView,
                    EventResultsView, EventVoteView)

urlpatterns = [
    path("event/list", EventListView.as_view(), name="event-list"),
    path("event", EventCreateView.as_view(), name="event-create"),
    path("event/<int:id>", EventDetailView.as_view(), name="event-detail"),
    path("event/<int:id>/vote", EventVoteView.as_view(), name="event-vote"),
    path("event/<int:id>/results", EventResultsView.as_view(), name="event-results"),
]
