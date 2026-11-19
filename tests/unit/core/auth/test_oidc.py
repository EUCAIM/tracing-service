from unittest.mock import Mock
import pytest
from fastapi import HTTPException

from app.core.auth.oidc import require_role, User
from app.core.auth.user_roles import UserRoles

@pytest.mark.asyncio
async def test_user_with_different_roles_than_trace_writer():
    with pytest.raises(HTTPException) as exc_info: 
        checker = require_role(UserRoles.WRITER)
        await checker(User("1", ["no_role"]))

    assert 403 == exc_info.value.status_code
    assert "Forbidden" == exc_info.value.detail

@pytest.mark.asyncio
async def test_user_with_no_roles():
    with pytest.raises(HTTPException) as exc_info: 
        checker = require_role(UserRoles.WRITER)
        await checker(User("1", []))

    assert 403 == exc_info.value.status_code
    assert "Forbidden" == exc_info.value.detail

@pytest.mark.asyncio
async def test_user_has_role_trace_writer():
    initial_user: User = User("1", [UserRoles.WRITER])
    checker = require_role(UserRoles.WRITER)
    user: User = await checker(initial_user)

    assert initial_user == user
