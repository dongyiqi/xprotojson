from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "XProtoJSON API"
	debug: bool = True
	reload: bool = True
	host: str = "127.0.0.1"
	port: int = 8000
	# Feishu credentials managed via standard FastAPI/Pydantic settings
	feishu_app_id: str | None = None
	feishu_app_secret: str | None = None

	model_config = SettingsConfigDict(
		env_prefix="XPJ_",
		case_sensitive=False,
		env_file=".env",
		env_file_encoding="utf-8",
	)


settings = Settings()
