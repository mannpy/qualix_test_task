import json

from django.conf import settings
from django.views.generic.edit import FormView

from rpcapi.exceptions import JSONRPCError, JSONRPCTransportError
from rpcapi.services import get_client

from .forms import JSONRPCCallForm



class JSONRPCView(FormView):
	template_name = "web/index.html"
	form_class = JSONRPCCallForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["endpoint"] = settings.JSONRPC_ENDPOINT
		return context

	def form_valid(self, form):
		context = self.get_context_data(form=form)
		method = form.cleaned_data["method"]
		params = form.cleaned_data["params"]

		try:
			result = get_client().call(method, params)
		except JSONRPCError as exc:
			context["error_kind"] = "rpc"
			context["error_message"] = str(exc)
			context["error_data"] = exc.data
		except JSONRPCTransportError as exc:
			context["error_kind"] = "transport"
			context["error_message"] = str(exc)
		else:
			context["result_json"] = json.dumps(result, ensure_ascii=False, indent=2)

		context["submitted_method"] = method
		return self.render_to_response(context)

		


