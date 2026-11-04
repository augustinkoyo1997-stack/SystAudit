from django.urls import path

from .views import agent_heartbeat, agent_register
from .deployment_views import deployment_claim, deployment_poll, deployment_progress


urlpatterns = [
    path("deployment/claim/", deployment_claim, name="deployment-claim"),
    path("deployment/poll/", deployment_poll, name="deployment-poll"),
    path("deployment/progress/", deployment_progress, name="deployment-progress"),
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
