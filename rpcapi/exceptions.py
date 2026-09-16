from dataclasses import dataclass
from typing import Any

class JSONRPCTransportError(Exception):
	"""Network, TLS, HTTP or protocol-envelope level failure"""

@dataclass
class JSONRPCError(Exception):
	"""The remote service returned a JSON-RPC 2.0 error object"""

	code: int | None
	message: str
	data: Any = None

	def __str__(self) -> str:
		return f"JSON-RPC error: {self.code}: {self.message}"
