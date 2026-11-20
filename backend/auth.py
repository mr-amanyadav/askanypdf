from fastapi import Header, HTTPException
import jwt
from jwt import PyJWKClient
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import SUPABASE_URL

print(f"[auth] AUTH MODULE LOADED — URL={SUPABASE_URL}", flush=True)

_jwks_client = None


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        print(f"[auth] Loading JWKS: {jwks_url}", flush=True)
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


async def get_current_user(authorization: str = Header(None)) -> str:
    print(f"[auth] get_current_user called", flush=True)

    if not authorization or not authorization.startswith("Bearer "):
        print(f"[auth] FAIL: no Bearer header (got: {authorization})", flush=True)
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    print(f"[auth] token[:40] = {token[:40]}", flush=True)

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        print(f"[auth] JWKS key found, kid={signing_key.key_id}", flush=True)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
        )
        print(f"[auth] TOKEN VALID: sub={payload.get('sub')}", flush=True)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "No user ID in token")
        return user_id

    except Exception as e:
        print(f"[auth] FAILED — {type(e).__name__}: {e}", flush=True)
        raise HTTPException(401, f"Invalid token: {type(e).__name__}: {e}")