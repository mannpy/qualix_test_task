from functools import lru_cache

from django.conf import settings

from .client import JSONRPCClient
from .mtls import build_client_ssl_context

@lru_cache(maxsize=1)
def get_client() -> JSONRPCClient:
	"""
	Return a process-wide JSONRPCClient configured from settings.
	Cached with lru_cache to build once per process.
	"""
	ssl_context = build_client_ssl_context(
		cert_pem=settings.JSONRPC_CLIENT_CERT_PEM,
		key_pem=settings.JSONRPC_CLIENT_KEY_PEM,
	)
	return JSONRPCClient(
		endpoint=settings.JSONRPC_ENDPOINT,
		ssl_context=ssl_context,
		timeout=settings.JSONRPC_TIMEOUT,
	)