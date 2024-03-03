from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    crypt_token: str
    jwt_secret: str

    model_config = SettingsConfigDict(env_file='../.env')


settings = _Settings()
