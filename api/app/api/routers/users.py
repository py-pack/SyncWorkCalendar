from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import hash_password
from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.users import UserCreate, UserItem, UserPatch
from app.dao import APIUserDAO


router = APIRouter()


@router.get("", response_model=list[UserItem])
async def list_users(
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserItem]:
    users = await APIUserDAO.list_all(db)
    return [UserItem.model_validate(u) for u in users]


@router.post("", response_model=UserItem, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserItem:
    # Унікальність username і e-mail (регістронезалежно) — явний 409 замість
    # сирого IntegrityError від UNIQUE-констрейнтів.
    if await APIUserDAO.username_exists(db, body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        )
    if await APIUserDAO.email_exists(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already exists",
        )

    # invite без пароля → password_hash = NULL (вхід через Google за e-mail).
    password_hash = hash_password(body.password) if body.password else None
    user = await APIUserDAO.create(
        db,
        username=body.username,
        email=body.email,
        worker_key=body.worker_key,
        password_hash=password_hash,
    )
    return UserItem.model_validate(user)


@router.patch("/{user_id}", response_model=UserItem)
async def patch_user(
    user_id: int,
    body: UserPatch,
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserItem:
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body must contain at least one of: username, worker_key, is_active",
        )

    user = await APIUserDAO.find(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )

    if "username" in fields and await APIUserDAO.username_exists(
        db, fields["username"], exclude_id=user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        )

    await APIUserDAO.update(db, user, **fields)
    return UserItem.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await APIUserDAO.find(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    await APIUserDAO.delete(db, user)
