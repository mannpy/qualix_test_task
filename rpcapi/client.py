import http.client
import json
import ssl
import uuid
from typing import Any
from urllib.parse import urlsplit

from .exceptions import JSONRPCError, JSONRPCTransportError


class JSONRPCClient:
	"""
	A small, synchronous JSON_RPC 2.0 client over HTTPS.

	Example:
		context = ssl.create_default_context()
		client = JSONRPCClient(endpoint, ssl_context=context)
		result = client.call("auth.method")
	"""

	def __init__(
		self,
		endpoint: str,
		ssl_context: ssl.SSLContext | None = None,
		timeout: float = 10.0

	) -> None:
		parts = urlsplit(endpoint)
		if parts.scheme != "https":
			raise ValueError(f"Only https:// endpoints are supported, got: {endpoint!r}")
		if not parts.hostname:
			raise ValueError(f"Could not parse host from endpoint: {endpoint!r}")

		self._host = parts.hostname
		self._port = parts.port or 443
		self._path = parts.path or "/"
		self._ssl_context = ssl_context or ssl.create_default_context()
		self._timeout = timeout


	def call(self, method: str, params: dict | None = None, request_id: str | None = None) -> Any:
		request_id = request_id or uuid.uuid4().hex
		payload = {
		    "jsonrpc": "2.0",
		    "method": method,
		    "params": params or {},
		    "id": request_id,
		}
		body = json.dumps(payload).encode("utf-8")

		raw = self._send_request(body)
		data = self._parse_response(raw)

		response_id = data.get("id")
		if response_id != request_id:
			raise JSONRPCTransportError(
				f"Response id {response_id!r} does not match request id {request_id!r}"
			)

		return data.get("result")


	def _send_request(self, body: bytes) -> bytes:
		conn = http.client.HTTPSConnection(
			self._host, 
			self._port, 
			context=self._ssl_context,
			timeout=self._timeout,
		)
		try:
			conn.request(
				"POST",
				self._path,
				body=body,
				headers={
					"Content-Type": "application/json",
					"Content-Length": str(len(body)),
					"Accept": "application/json",
				}
			)
			response = conn.getresponse()
			raw = response.read()
		except ssl.SSLError as exc:
			raise JSONRPCTransportError(f"TLS Error talking to {self._host}: {exc}") from exc
		except (OSError, http.client.HTTPException) as exc:
			raise JSONRPCTransportError(f"Nwtwork error talking to {self._host}: {exc}") from exc
		finally:
			conn.close()

		if response.status != 200:
			raise JSONRPCTransportError(
				f"Unexpected HTTP status {response.status} {response.reason} from {self._host}"
			)
		return raw

	@staticmethod
	def _parse_response(raw: bytes) -> dict:
		try:
			data = json.loads(raw.decode("utf-8"))
		except UnicodeDecodeError as exc:
			raise JSONRPCTransportError(f"Response was not valid UTF-8: {exc}") from exc
		except json.JSONDecodeError as exc:
			raise JSONRPCTransportError(f"Response was not valid JSON: {exc}") from exc

		if not isinstance(data, dict):
			raise JSONRPCTransportError("Response data was not a JSON object")

		error = data.get("error")
		if error:
			if not isinstance(error, dict):
				raise JSONRPCTransportError(f"Mailformed error member: {error!r}")
			raise JSONRPCError(
				code = error.get("code"),
				message=error.get("message", "Unknown error"),
				data=error.get("data"),
			)

		return data

