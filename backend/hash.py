from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

class Hash:

    @staticmethod
    def bcrypt(password: str):
        password = password[:72]
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain_password, hashed_password):
        plain_password = plain_password[:72]

        return pwd_context.verify(
            plain_password,
            hashed_password
        )