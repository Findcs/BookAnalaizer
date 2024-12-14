from functools import lru_cache

from dotenv import find_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_name: str
    db_password: str
    db_host: str
    db_user: str
    secret: str

    class Config:
        env_file = find_dotenv(".env")


@lru_cache()
def get_settings():
    return Settings()
