# app/crypto.py
import os, hashlib
from typing import Callable, Tuple, Optional

# --- Hash selection (default: SHA3-256) ---
def _hash_fn(name: str) -> Callable[[bytes], bytes]:
    name = (name or "sha3_256").lower()
    if name == "sha3_256":
        return lambda b: hashlib.sha3_256(b).digest()
    if name == "sha3_512":
        return lambda b: hashlib.sha3_512(b).digest()
    if name == "sha256":
        return lambda b: hashlib.sha256(b).digest()
    # safe fallback
    return lambda b: hashlib.sha3_256(b).digest()

HASH_ALGO = os.getenv("JIMINI_HASH_ALGO", "sha3_256")
hash_bytes = _hash_fn(HASH_ALGO)

# --- Optional signing (Ed25519 now; PQ later) ---
# If 'cryptography' is present, we’ll offer Ed25519; otherwise we no-op.
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey
    )
    from cryptography.hazmat.primitives import serialization
    _has_ed25519 = True
except Exception:
    Ed25519PrivateKey = None  # type: ignore
    Ed25519PublicKey = None  # type: ignore
    serialization = None  # type: ignore
    _has_ed25519 = False

SIG_ALGO = os.getenv("JIMINI_SIG_ALGO", "none").lower()
KEY_PATH_PRIV = os.getenv("JIMINI_SIGNING_KEY", "keys/jimini_ed25519.pem")
KEY_PATH_PUB  = os.getenv("JIMINI_SIGNING_PUB", "keys/jimini_ed25519.pub")

def sign_detached(msg: bytes) -> Tuple[str, Optional[bytes]]:
    """
    Returns (algo_label, signature_bytes_or_None).
    If SIG_ALGO=none or key/lib unavailable, returns (none, None).
    """
    if SIG_ALGO != "ed25519" or not _has_ed25519:
        return ("none", None)
    try:
        if serialization is None:
            return ("none", None)
        with open(KEY_PATH_PRIV, "rb") as f:
            sk = serialization.load_pem_private_key(f.read(), password=None)
        if Ed25519PrivateKey is not None and isinstance(sk, Ed25519PrivateKey):
            sig = sk.sign(msg)
            return ("ed25519", sig)
        else:
            return ("none", None)
    except Exception:
        return ("none", None)

def verify_detached(msg: bytes, sig: bytes) -> bool:
    if SIG_ALGO != "ed25519" or not _has_ed25519:
        return False
    try:
        if serialization is None:
            return False
        with open(KEY_PATH_PUB, "rb") as f:
            pk = serialization.load_pem_public_key(f.read())
        if Ed25519PublicKey is not None and isinstance(pk, Ed25519PublicKey):
            pk.verify(sig, msg)
            return True
        else:
            return False
    except Exception:
        return False

def algo_labels() -> Tuple[str, str]:
    return (HASH_ALGO, SIG_ALGO)
