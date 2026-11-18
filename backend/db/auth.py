from fastapi import Header, HTTPException
import jwt   # this is PyJWT, not python-jose
from jwt import PyJWKClient
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import SUPABASE_URL

# Cache the JWKS client (fetches keys once, refreshes as needed)
_jwks_client = None

def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


async def get_current_user(authorization: str = Header(None)) -> str:
    """Verify Supabase JWT (ES256 or HS256) using JWKS public keys."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]

    try:
        # Fetch the signing key matching this token's kid
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],  # accept all common algs
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "No user ID in token")
        return user_id
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")