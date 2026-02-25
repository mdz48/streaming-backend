from app.shared.config.database import get_db_session
from app.features.user.models.user import User, followers_association
from typing import Optional, List

class UserRepository:
    def __init__(self):
        self.db = next(get_db_session())

    def get_all_users(self) -> List[User]:
        return self.db.query(User).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, username: str, password: str, rol: str) -> User:
        new_user = User(username=username, password=password, rol=rol)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def add_follow(self, follower_id: int, streamer_id: int) -> bool:
        """Que un follower siga a un streamer"""
        try:
            self.db.execute(
                followers_association.insert().values(
                    follower_id=follower_id,
                    streamer_id=streamer_id
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def remove_follow(self, follower_id: int, streamer_id: int) -> bool:
        """Que un follower deje de seguir a un streamer"""
        try:
            self.db.execute(
                followers_association.delete().where(
                    (followers_association.c.follower_id == follower_id) &
                    (followers_association.c.streamer_id == streamer_id)
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def is_following(self, follower_id: int, streamer_id: int) -> bool:
        """Verificar si un usuario sigue a otro"""
        result = self.db.execute(
            followers_association.select().where(
                (followers_association.c.follower_id == follower_id) &
                (followers_association.c.streamer_id == streamer_id)
            )
        ).first()
        return result is not None

    def get_followers(self, streamer_id: int) -> List[dict]:
        """Obtener lista de followers de un streamer"""
        result = self.db.execute(
            followers_association.select().where(
                followers_association.c.streamer_id == streamer_id
            )
        ).fetchall()
        return [{"follower_id": row[0]} for row in result]

    def get_following(self, follower_id: int) -> List[User]:
        """Obtener lista de streamers que sigue un usuario"""
        result = self.db.execute(
            followers_association.select().where(
                followers_association.c.follower_id == follower_id
            )
        ).fetchall()
        streamer_ids = [row[1] for row in result]
        return self.db.query(User).filter(User.id.in_(streamer_ids)).all()
