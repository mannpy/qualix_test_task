from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from rpcapi.exceptions import JSONRPCError, JSONRPCTransportError

from .forms import JSONRPCCallForm


class JSONRPCCallFormTests(SimpleTestCase):
	def test_valid_params_parsed_as_dict(self):
		form = JSONRPCCallForm(data={"method": "auth.check", "params": '{"a": 1}'})
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data["params"], {"a": 1})


	def test_method_is_required(self):
		form = JSONRPCCallForm(data={"method": "", "params": ""})
		self.assertFalse(form.is_valid())
		self.assertIn("method", form.errors)

	def test_blank_params_defaults_to_empty_object(self):
		form = JSONRPCCallForm(data={"method": "auth.check", "params": ""})
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data["params"], {})

	def test_invalid_json_is_rejected(self):
		form = JSONRPCCallForm(data={"method": "auth.check", "params": "{invalid json"})
		self.assertFalse(form.is_valid())
		self.assertIn("params", form.errors)

	def test_non_object_is_rejected(self):
		form = JSONRPCCallForm(data={"method": "auth.check", "params": "[1, 2, 3]"})
		self.assertFalse(form.is_valid())
		self.assertIn("params", form.errors)


class JSONRPCViewTests(SimpleTestCase):
    def test_get_renders_empty_form(self):
        response = self.client.get(reverse("web:json_rpc_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "auth.check")

    @patch("web.views.get_client")
    def test_successful_call_shows_result(self, mock_get_client):
        mock_get_client.return_value.call.return_value = {"authorized": True}

        response = self.client.post(
            reverse("web:json_rpc_view"), {"method": "auth.check", "params": "{}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "authorized")
        mock_get_client.return_value.call.assert_called_once_with("auth.check", {})

    @patch("web.views.get_client")
    def test_rpc_error_is_displayed(self, mock_get_client):
        mock_get_client.return_value.call.side_effect = JSONRPCError(
            code=-32601, message="Method not found"
        )

        response = self.client.post(
            reverse("web:json_rpc_view"), {"method": "no.such", "params": "{}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Method not found")

    @patch("web.views.get_client")
    def test_transport_error_is_displayed(self, mock_get_client):
        mock_get_client.return_value.call.side_effect = JSONRPCTransportError("boom")

        response = self.client.post(
            reverse("web:json_rpc_view"), {"method": "auth.check", "params": "{}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Транспортная ошибка")

    def test_invalid_form_reshows_page_without_calling_client(self):
        with patch("web.views.get_client") as mock_get_client:
            response = self.client.post(
                reverse("web:json_rpc_view"), {"method": "auth.check", "params": "not json"}
            )
        self.assertEqual(response.status_code, 200)
        mock_get_client.assert_not_called()