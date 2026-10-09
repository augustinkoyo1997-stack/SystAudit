from django.urls import path

from .views import agent_heartbeat, agent_register


urlpatterns = [
    path(
        "heartbeat/",
        agent_heartbeat,
        name="agent-heartbeat",
    ),
    path(
        "register/",
        agent_register,
        name="agent-register",
    ),
]
