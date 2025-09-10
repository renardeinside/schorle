import time
import uuid
import jwt


def make_token(
    secret: str,
) -> str:
    now = int(time.time())
    payload = {
        "iss": "schorle-py",  # who issued the token
        "aud": "nextjs-app",  # who should accept it
        "iat": now,  # issued at
        "exp": now + 5,  # 5s TTL
        "jti": str(uuid.uuid4()),  # nonce for replay protection
    }
    return jwt.encode(payload, secret, algorithm="HS256")
