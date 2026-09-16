from django.urls import path

from .views import JSONRPCView

app_name = "web"

urlpatterns = [
	path("", JSONRPCView.as_view(), name="json_rpc_view")
]