from django.urls import path

from .views import agent_heartbeat


urlpatterns = [
    path(
        "heartbeat/",
        agent_heartbeat,
        name="agent-heartbeat",
    ),
]
