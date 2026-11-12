from models import User
from pwdlib import PasswordHash


class UserFactory:

    password_hash = PasswordHash.recommended()

    @staticmethod
    def create_user(name, email, password, role="customer"):

        hashed_password = UserFactory.password_hash.hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        return user