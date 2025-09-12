from app.metrics.vault import get_certificate_validity
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import app.metrics.vault as vault_module


def make_cert(valid_days: int) -> str:
    """Generate a self-signed PEM certificate valid for `valid_days`."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, u"Test Org"),
        x509.NameAttribute(x509.NameOID.COMMON_NAME, u"test.local"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=valid_days))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def test_valid_certificate():
    """Ensure certificate validity calculation returns positive seconds."""
    pem = make_cert(valid_days=30)
    seconds = get_certificate_validity(pem)
    assert seconds > 0
    assert seconds > 10 * 24 * 3600  # more than 10 days


def test_update_metrics_with_valid_issuer(monkeypatch):
    """Ensure update_metrics updates Prometheus gauge for
    a valid PKI issuer."""

    monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")

    with patch.object(vault_module, "VAULT_ADDR", "http://127.0.0.1:8200"):
        mock_client = MagicMock()
        mock_client.sys.list_mounted_secrets_engines.return_value = {
            "data": {
                "pki/": {"type": "pki"},
                "secret/": {"type": "kv"}
            }
        }

        mock_client.secrets.pki.list_issuers.return_value = {
            'data': {
                'keys': ['issuer1']
            }
        }

        mock_client.secrets.pki.read_issuer.return_value = {
            "data": {"certificate": make_cert(10)}
        }

        monkeypatch.setattr(vault_module, "create_client", lambda: mock_client)

        # Patch certificate_expiry gauge
        with patch.object(vault_module, "certificate_expiry") as mock_gauge:
            mock_label = mock_gauge.labels.return_value
            vault_module.update_metrics()

            # Verify correct labels used
            mock_gauge.labels.assert_called_once_with(
                engine="pki/",
                issuer="issuer1",
                url="http://127.0.0.1:8200"
            )

            # Verify metric was updated with a positive number
            mock_label.set.assert_called_once()
            assert mock_label.set.call_args.args[0] > 0
