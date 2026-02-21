from django.contrib import admin

from .models import Event, ParticipantVote

admin.site.register(Event)
admin.site.register(ParticipantVote)
