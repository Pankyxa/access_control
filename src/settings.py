from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    crypt_token: str
    jwt_secret: str
    db_username: str = 'user'
    db_password: str = 'password'
    db_ip: str = 'localhost'
    db_port: str = '8000'
    db_name: str = 'postgres'
    front_ip_1: str = '127.0.0.1'
    model_config = SettingsConfigDict(env_file='.env')


settings = _Settings()
