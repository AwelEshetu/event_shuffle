from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Event, EventDate, ParticipantVote, Vote
from .services import (
    event_date_queryset_for_event,
    participant_selected_dates_queryset,
    resolve_participant_name,
    sync_participant_vote_dates,
)


class EventDateInline(admin.TabularInline):
    model = EventDate
    extra = 1


class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    inlines = [EventDateInline]


class ParticipantVoteAdminForm(forms.ModelForm):
    """
    Custom form for ParticipantVote that exposes a multi-select 'selected_dates'
    field scoped to the chosen event.  Vote rows are kept in sync by save_related.
    """

    selected_dates = forms.ModelMultipleChoiceField(
        queryset=EventDate.objects.none(),
        required=False,
        label="Available dates",
        help_text=(
            "Select the dates this participant can attend. "
            "Only dates that belong to the selected event are listed."
        ),
        widget=admin.widgets.FilteredSelectMultiple("dates", is_stacked=False),
    )

    class Media:
        js = ("events/admin/participant_vote_event_refresh.js",)

    class Meta:
        model = ParticipantVote
        fields = ("event", "user", "name", "selected_dates")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prefer selecting a real user in admin; when selected, name is auto-filled.
        self.fields["name"].required = False

        # Prefer live POST data so the date list updates when the event changes
        # mid-form (e.g. after a validation error re-render).
        event_id = self.data.get("event")
        if not event_id:
            if self.instance.pk:
                event_id = self.instance.event_id
            elif self.initial.get("event"):
                event_id = self.initial.get("event")

        if event_id:
            self.fields["selected_dates"].queryset = event_date_queryset_for_event(
                event_id
            )

        if self.instance.pk:
            self.fields["selected_dates"].initial = participant_selected_dates_queryset(
                self.instance
            )

    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data["name"] = resolve_participant_name(
                cleaned_data.get("user"), cleaned_data.get("name")
            )
        except ValidationError as exc:
            self.add_error("name", exc.message)

        return cleaned_data

    def save_votes(self, participant: ParticipantVote) -> None:
        """Sync Vote rows to exactly match the selected dates."""
        sync_participant_vote_dates(
            participant=participant,
            selected_dates=self.cleaned_data.get("selected_dates", []),
        )


class ParticipantVoteAdmin(admin.ModelAdmin):
    form = ParticipantVoteAdminForm
    list_display = ("id", "display_name", "user", "event")
    list_select_related = ("event", "user")
    search_fields = ("name", "user__username", "event__name")
    fields = ("event", "user", "name", "selected_dates")

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        event_id = request.GET.get("event")
        if event_id:
            initial["event"] = event_id
        return initial

    def save_related(self, request, form, formsets, change):
        # Called after the participant row is saved — safe to create Vote FKs now.
        super().save_related(request, form, formsets, change)
        form.save_votes(form.instance)


class EventDateAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "date")
    list_select_related = ("event",)
    list_filter = ("event",)
    search_fields = ("event__name",)


class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "participant", "event_date")
    list_select_related = ("participant__event", "event_date")
    search_fields = ("participant__name", "participant__event__name")
    readonly_fields = ("participant", "event_date")


admin.site.register(Event, EventAdmin)
admin.site.register(ParticipantVote, ParticipantVoteAdmin)
admin.site.register(EventDate, EventDateAdmin)
admin.site.register(Vote, VoteAdmin)
