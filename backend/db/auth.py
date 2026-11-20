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
        _jwks_client = PyJWKClient(jwks_url, lifespan=60)
    return _jwks_client


async def get_current_user(authorization: str = Header(None)) -> str:
    print(f"[auth] get_current_user called", flush=True)

    if not authorization or not authorization.startswith("Bearer "):
        print(f"[auth] FAIL: no Bearer header", flush=True)
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    print(f"[auth] token[:40] = {token[:40]}", flush=True)

    for attempt in range(2):
        try:
            signing_key = get_jwks_client().get_signing_key_from_jwt(token)
            print(f"[auth] JWKS key found: {signing_key.key_id}", flush=True)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
                leeway=300,
            )
            user_id = payload.get("sub")
            print(f"[auth] TOKEN VALID: sub={user_id}", flush=True)
            if not user_id:
                raise HTTPException(401, "No user ID in token")
            return user_id

        except jwt.InvalidSignatureError:
            if attempt == 0:
                print(f"[auth] Signature failed — refreshing JWKS and retrying", flush=True)
                global _jwks_client
                _jwks_client = None
                continue
            print(f"[auth] FAIL: InvalidSignatureError after retry", flush=True)
            raise HTTPException(401, "Invalid token signature")

        except jwt.ExpiredSignatureError:
            print(f"[auth] FAIL: ExpiredSignatureError", flush=True)
            raise HTTPException(401, "Token expired — please re-login")

        except jwt.InvalidAudienceError as e:
            print(f"[auth] FAIL: InvalidAudienceError — {e}", flush=True)
            raise HTTPException(401, f"Bad audience: {e}")

        except jwt.InvalidTokenError as e:
            print(f"[auth] FAIL: InvalidTokenError — {e}", flush=True)
            raise HTTPException(401, f"Invalid token: {e}")

        except Exception as e:
            print(f"[auth] FAIL: {type(e).__name__} — {e}", flush=True)
            raise HTTPException(401, f"Auth error: {type(e).__name__}: {e}")

    raise HTTPException(401, "Auth failed")