"""
generate_cert.py — one-shot self-signed TLS certificate for local dev.
Writes nginx/ssl/cert.pem and nginx/ssl/key.pem.
"""
import datetime, ipaddress, os, zoneinfo
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SSL_DIR = os.path.join(os.path.dirname(__file__), "nginx", "ssl")
os.makedirs(SSL_DIR, exist_ok=True)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Traffic Monitor Dev"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

key_path  = os.path.join(SSL_DIR, "key.pem")
cert_path = os.path.join(SSL_DIR, "cert.pem")

with open(key_path, "wb") as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))

with open(cert_path, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"✅  cert.pem  → {cert_path}")
print(f"✅  key.pem   → {key_path}")
print("   Valid for 365 days. For production use Let's Encrypt instead.")
