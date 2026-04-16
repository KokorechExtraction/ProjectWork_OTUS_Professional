from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.post import PostService


@pytest.mark.asyncio
async def test_create_comment_rejects_missing_post() -> None:
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    service = PostService(repo)

    with pytest.raises(ValueError, match="Post not found"):
        await service.create_comment(1, 99, "hello")


@pytest.mark.asyncio
async def test_like_post_adds_like_when_missing() -> None:
    post = SimpleNamespace(id=10, author_id=1)
    repo = AsyncMock()
    repo.get_by_id.side_effect = [post, post]
    repo.has_like.return_value = False
    repo.likes_count.return_value = 3
    service = PostService(repo)

    result = await service.like_post(2, 10)

    assert result is post
    repo.add_like.assert_awaited_once_with(10, 2)
    assert repo.get_by_id.await_count == 2


@pytest.mark.asyncio
async def test_unlike_post_removes_existing_like() -> None:
    post = SimpleNamespace(id=11, author_id=1)
    repo = AsyncMock()
    repo.get_by_id.side_effect = [post, post]
    repo.has_like.return_value = True
    repo.likes_count.return_value = 1
    service = PostService(repo)

    result = await service.unlike_post(2, 11)

    assert result is post
    repo.remove_like.assert_awaited_once_with(11, 2)


@pytest.mark.asyncio
async def test_edit_post_rejects_foreign_user_without_admin_rights() -> None:
    post = SimpleNamespace(id=12, author_id=1)
    repo = AsyncMock()
    repo.get_by_id.return_value = post
    service = PostService(repo)

    with pytest.raises(ValueError, match="cannot edit"):
        await service.edit_post(2, 12, "fixed")


@pytest.mark.asyncio
async def test_edit_post_rejects_empty_text_after_strip() -> None:
    post = SimpleNamespace(id=13, author_id=1)
    repo = AsyncMock()
    repo.get_by_id.return_value = post
    service = PostService(repo)

    with pytest.raises(ValueError, match="cannot be empty"):
        await service.edit_post(1, 13, "   ")


@pytest.mark.asyncio
async def test_delete_post_allows_admin() -> None:
    post = SimpleNamespace(id=14, author_id=1)
    repo = AsyncMock()
    repo.get_by_id.return_value = post
    service = PostService(repo)

    await service.delete_post(999, 14, is_admin=True)

    repo.delete_post.assert_awaited_once_with(post)
