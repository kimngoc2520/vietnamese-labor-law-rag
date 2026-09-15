def get_database_url() -> str:
    from src.config.settings import settings

    return settings.database_url
