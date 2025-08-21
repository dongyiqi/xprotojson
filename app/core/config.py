from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "XProtoJSON API"
	debug: bool = True
	reload: bool = True
	host: str = "127.0.0.1"
	port: int = 8000

	model_config = SettingsConfigDict(
		env_prefix="XPJ_",
		case_sensitive=False,
	)


settings = Settings()
