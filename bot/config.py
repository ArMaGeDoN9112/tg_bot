from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_PATH: str = "db/users_data.csv"
    GIGACHAT_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()