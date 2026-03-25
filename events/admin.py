from django.contrib import admin

from .models import Event, EventDate, ParticipantVote, Vote


class EventDateInline(admin.TabularInline):
    model = EventDate
    extra = 1


class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    inlines = [EventDateInline]


class VoteInline(admin.TabularInline):
    model = Vote
    extra = 1


class ParticipantVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "event")
    inlines = [VoteInline]


admin.site.register(Event, EventAdmin)
admin.site.register(ParticipantVote, ParticipantVoteAdmin)
admin.site.register(EventDate)
admin.site.register(Vote)
