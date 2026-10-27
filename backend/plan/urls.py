from django.urls import path

from backend.plan.views import WorkVolumeListView

app_name = "plan"

urlpatterns = [
    path("work-volume-list/", WorkVolumeListView.as_view(), name="work-volume-list"),
]
