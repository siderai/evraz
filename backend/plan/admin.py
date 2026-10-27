from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from backend.plan.models import Factory, FactoryUser, WorkVolume, WorkVolumeRecord


class FactoryUserInline(admin.TabularInline):
    model = FactoryUser
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "external_id")
    search_fields = ("name", "external_id")
    readonly_fields = ("external_id",)
    inlines = (FactoryUserInline,)


@admin.register(FactoryUser)
class FactoryUserAdmin(admin.ModelAdmin):
    list_display = ("id", "factory", "user")
    list_filter = ("factory",)
    autocomplete_fields = ("user", "factory")


@admin.register(WorkVolume)
class WorkVolumeAdmin(admin.ModelAdmin):
    list_display = ("id", "factory", "start", "finish", "weight", "created")
    list_filter = ("factory",)
    date_hierarchy = "start"


@admin.register(WorkVolumeRecord)
class WorkVolumeRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "factory", "start", "finish", "weight", "author", "created")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
