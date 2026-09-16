import json
import os
import ssl
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from .client import JSONRPCClient
from .mtls import build_client_ssl_context
from .exceptions import JSONRPCError, JSONRPCTransportError


FAKE_CERT_PEM = """
-----BEGIN CERTIFICATE-----
q5x32KMxHL/POaP5z7eU8g4oJhR206Lb57r3AdcoW9ryyP4=
-----END CERTIFICATE-----
"""

FAKE_KEY_PEM = """
-----BEGIN PRIVATE KEY-----
abqEOlHhlswzdeq29LlKog==
-----END PRIVATE KEY-----
"""

def _make_response(status=200, reason="OK", payload=b""):
	response = Mock()
	response.status = status
	response.reason = reason
	response.read.return_value = payload
	return response



class JSONRPCClientTests(SimpleTestCase):
	def setUp(self):
		self.client = JSONRPCClient("https://example.test/api/v2")

	def test_rejects_non_https_endpoint(self):
		with self.assertRaises(ValueError):
			JSONRPCClient("http://example.test/api/v2")

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_successful_call_returns_result(self, mock_conn_cls):
		body = json.dumps({"jsonrpc": "2.0", "result": {"ok": True}, "id": "abc"}).encode()
		mock_conn = mock_conn_cls.return_value
		mock_conn.getresponse.return_value = _make_response(payload=body)

		result = self.client.call("auth.check", request_id="abc")

		self.assertEqual(result, {"ok": True})
		sent_body = json.loads(mock_conn.request.call_args.kwargs["body"])
		self.assertEqual(sent_body["method"], "auth.check")
		self.assertEqual(sent_body["jsonrpc"], "2.0")

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_service_error_raises_jsonrpc_error(self, mock_conn_cls):
		body = json.dumps(
			{"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"}
		).encode()
		mock_conn = mock_conn_cls.return_value
		mock_conn.getresponse.return_value = _make_response(payload=body)

		with self.assertRaises(JSONRPCError) as ctx:
			self.client.call("no.such.method", request_id="1")
		self.assertEqual(ctx.exception.code, -32601)

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_non_200_status_raises_transport_error(self, mock_conn_cls):
	    mock_conn = mock_conn_cls.return_value
	    mock_conn.getresponse.return_value = _make_response(status=503, reason="Service Unavailable")

	    with self.assertRaises(JSONRPCTransportError):
	        self.client.call("auth.check")

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_malformed_json_raises_transport_error(self, mock_conn_cls):
	    mock_conn = mock_conn_cls.return_value
	    mock_conn.getresponse.return_value = _make_response(payload=b"not json")

	    with self.assertRaises(JSONRPCTransportError):
	        self.client.call("auth.check")

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_mismatched_id_raises_transport_error(self, mock_conn_cls):
	    body = json.dumps({"jsonrpc": "2.0", "result": 1, "id": "wrong-id"}).encode()
	    mock_conn = mock_conn_cls.return_value
	    mock_conn.getresponse.return_value = _make_response(payload=body)

	    with self.assertRaises(JSONRPCTransportError):
	        self.client.call("auth.check", request_id="expected-id")

	@patch("rpcapi.client.http.client.HTTPSConnection")
	def test_network_failure_raises_transport_error(self, mock_conn_cls):
	    mock_conn = mock_conn_cls.return_value
	    mock_conn.getresponse.side_effect = OSError("connection reset")

	    with self.assertRaises(JSONRPCTransportError):
	        self.client.call("auth.check")


class BuildClientSSLContextTests(SimpleTestCase):
	def test_returns_ssl_context_and_cleans_up_temp_files(self):
		captured_paths = {}

		def fake_load_cert_chain(self, certfile, keyfile):
			captured_paths["cert"] = certfile
			captured_paths["key"] = keyfile
			return None

		with patch.object(ssl.SSLContext, "load_cert_chain", fake_load_cert_chain):
			context = build_client_ssl_context(FAKE_CERT_PEM, FAKE_KEY_PEM)

		self.assertIsInstance(context, ssl.SSLContext)
		# The temp files must be written during the call
		self.assertTrue(captured_paths["cert"].endswith("client.crt"))
		self.assertTrue(captured_paths["key"].endswith("client.key"))
		# and removed again once we're done
		self.assertFalse(os.path.exists(captured_paths["cert"]))
		self.assertFalse(os.path.exists(captured_paths["key"]))
		self.assertFalse(os.path.exists(os.path.dirname(captured_paths["cert"])))




