from joserfc.jwt import decode, Token, JWTClaimsRegistry
from joserfc.jwk import KeySet, KeySetSerialization
from joserfc.errors import JoseError, InvalidClaimError
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.settings import get_settings
from app.core.logging import logging
from dataclasses import dataclass
from app.core.settings import Settings
from pydantic import TypeAdapter
import time
import asyncio


logger = logging.getLogger(__name__)

settings: Settings = get_settings()
adapter = TypeAdapter(KeySetSerialization)

security = HTTPBearer()


_OIDC_ISSUER = f"{settings.app.oidc.url}/realms/{settings.app.oidc.realm}"
_OPENID_CONFIG = f"{_OIDC_ISSUER}/.well-known/openid-configuration"

_JWKS_KEYSET: KeySet | None = None
_JWKS_CACHE_EXPIRY: float = 0
_KEYSET_LOCK = asyncio.Lock()

_JWKS_CACHE_WAIT = 300



@dataclass
class User:
    user_id: str
    roles: list[str]

async def get_keyset(force_refresh: bool = False) -> KeySet:
    global _JWKS_KEYSET, _JWKS_CACHE_EXPIRY

    now = time.monotonic()
    if not force_refresh and _JWKS_KEYSET is not None and now < _JWKS_CACHE_EXPIRY:
        return _JWKS_KEYSET

    async with _KEYSET_LOCK:
        now = time.monotonic()
        if not force_refresh and _JWKS_KEYSET is not None and now < _JWKS_CACHE_EXPIRY:
            return _JWKS_KEYSET
        
        async with httpx.AsyncClient() as client:
            config = await client.get(_OPENID_CONFIG)
            config.raise_for_status()

            jwks_uri = config.json()["jwks_uri"]

            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()

            try:
                validated_jwks = adapter.validate_python(
                    jwks_response.json()
                )
            except Exception as e:
                logger.error("Error validating Keycloak keys response")
                logger.error(e)
                raise HTTPException(status_code=500, detail="Internal server error")

    _JWKS_KEYSET = KeySet.import_key_set(validated_jwks)
    _JWKS_CACHE_EXPIRY = now + _JWKS_CACHE_WAIT

    return _JWKS_KEYSET

async def verify_token(token: str) -> User:
    keyset: KeySet = await get_keyset()
    claims_registry = JWTClaimsRegistry(
        # Issuer (check if the issuers match)
        iss={"essential": True, "value": _OIDC_ISSUER},
        # Audiences (check if at least one of the app's defined values is avaialble in the token)
        aud={"essential": True, "values": settings.app.oidc.audiences},
        # Expiration Time (Fails if token is expired or missing 'exp')
        exp={"essential": True},
        # Subject (Ensures a unique User ID exists in the token)
        sub={"essential": True},
        # # Prevent Token Type Confusion (This isn't a Refresh Token)
        # typ={"essential": True, "value": "Bearer"},
        # Issued at (detect tokens with suspicious timestamps)
        iat={"essential": True},
        # # Not before 
        # nbf={"essential": True}
    )
    try:
        decoded_token = decode(token, keyset)
    except JoseError:
        try:
            logger.info("Try to get a new set of keys from Keycloak.")
            keyset: KeySet = await get_keyset(force_refresh=True)
            decoded_token = decode(token, keyset)
        except JoseError as e:
            logger.error(f"Token deconding failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
            

    try:
        claims_registry.validate(decoded_token.claims)
    except InvalidClaimError as e:
        logger.error(f"Claims validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = User(user_id = decoded_token.claims["sub"],
        roles = decoded_token.claims
            .get("resource_access", {})
            .get(settings.app.oidc.client, {})
            .get("roles", [])
    )
    return user

async def auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials

    user = await verify_token(token)
    return user

def require_role(role: str):
    async def checker(user: User = Depends(auth_dependency)):
        if role not in user.roles:
            logger.error(f"user '{user.user_id}' does not have the role '{role}'")
            raise HTTPException(
                status_code=403,
                detail="Forbidden"
            )
        return user

    return checker