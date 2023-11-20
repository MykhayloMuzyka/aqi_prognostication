from django.contrib import admin
from aqi_forecast.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'duration', 'created_at']
    fields = ["duration"]


admin.site.register(Token, TokenAdmin)
