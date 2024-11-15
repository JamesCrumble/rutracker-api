from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

ENV_PREFIX: str = 'RA_'


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_prefix=ENV_PREFIX,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    DEBUG: bool = False

    WORKERS: int = 1
    HOST: str = '0.0.0.0'
    PORT: int = 4000
    AUTORELOAD: bool = False

    PROXY_DSN: str
    DOWNLOADING_CHUNK_SIZE: int = 1024 * 4  # in bytes
    DOWNLOAD_FOLDER_PATH: str = 'downloaded_torrents'

    RUTRACKER_SESSION_COOKIE: str
    RUTRACKER_BASE_URL: str = 'https://rutracker.org/forum'

    def on_startup(self) -> None:
        Path(self.DOWNLOAD_FOLDER_PATH).mkdir(exist_ok=True)


settings = Settings()
settings.on_startup()
