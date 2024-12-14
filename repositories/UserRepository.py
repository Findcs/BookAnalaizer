from fastapi import Depends
from sqlalchemy.orm import Session

from configs.Database import User, get_async_session


class UserRepository:
    db: Session

    def __init__(
            self, db: Session = Depends(get_async_session)
    ) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        return user
