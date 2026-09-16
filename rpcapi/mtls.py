import contextlib
import os
import ssl
import stat
import tempfile
from dataclasses import dataclass
from typing import Iterator


def build_client_ssl_context(cert_pem: str, key_pem: str, *, check_hostname: bool = True) -> ssl.SSLContext:
	"""Build an SS:Context configured for mutual TLS"""

	context = ssl.create_default_context()
	context.check_hostname = check_hostname

	with _temporary_pem_files(cert_pem, key_pem) as pem:
		try:
			context.load_cert_chain(certfile=pem.cert_path, keyfile=pem.key_path)
		except ssl.SSLError as exc:
			raise ValueError("Invalid client certificate or key") from exc

	return context


@dataclass(frozen=True)
class _PemPaths:
	cert_path: str
	key_path: str


@contextlib.contextmanager
def _temporary_pem_files(cert_pem: str, key_pem: str) -> Iterator[_PemPaths]:
	"""
	Materialize PEM strings as 0600 temp files, delete on exit.
	"""
	with tempfile.TemporaryDirectory(prefix="mtls-") as tmp_dir:
		cert_path = os.path.join(tmp_dir, "client.crt")
		key_path = os.path.join(tmp_dir, "client.key")
		
		for path, content in ((cert_path, cert_pem), (key_path, key_pem)):
			fd = os.open(
				path, 
				os.O_WRONLY | os.O_CREAT | os.O_EXCL,
				stat.S_IRUSR | stat.S_IWUSR,
			)
			with os.fdopen(fd, "w") as fh:
				fh.write(content) 

		yield _PemPaths(cert_path, key_path)