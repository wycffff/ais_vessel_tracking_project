from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/ais_tracking'
    local_database_url: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/ais_tracking'
    app_name: str = 'AIS Vessel Tracking and Prediction Platform'
    api_host: str = '0.0.0.0'
    api_port: int = 8000

    mqtt_host: str = 'meri.digitraffic.fi'
    mqtt_port: int = 443
    mqtt_path: str = '/mqtt'
    mqtt_topic: str = 'vessels-v2/#'
    mqtt_client_id: str = 'ais-tracking-demo-client'

    prediction_default_minutes: int = 15
    map_output_dir: str = 'output'

    llm_model_path: str | None = None
    llm_temperature: float = 0.2


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
