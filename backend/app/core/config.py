"""应用配置模块。

配置统一从环境变量读取，仓库只提交不含密钥的 `.env.example`。
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """定义应用当前需要的配置项及安全默认值。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "LostLink API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "mysql+pymysql://lostlink_app:lostlink_local@127.0.0.1:3306/lostlink?charset=utf8mb4"
    )
    database_echo: bool = False
    # 认证策略集中配置，测试和部署环境可以调整而无需修改业务代码。
    auth_session_ttl_hours: int = Field(default=168, ge=1, le=24 * 90)
    auth_max_login_attempts: int = Field(default=5, ge=1, le=20)
    auth_login_lock_minutes: int = Field(default=15, ge=1, le=24 * 60)
    # 上传文件保存在应用控制的目录，数据库只记录相对存储键。
    upload_directory: Path = Path("var/uploads")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    # OpenAI 兼容的多模态匹配默认关闭，只有完整配置后才发送业务数据。
    matching_ai_enabled: bool = False
    matching_ai_base_url: AnyHttpUrl | None = None
    matching_ai_api_key: SecretStr = SecretStr("")
    matching_ai_model: str = ""
    matching_ai_timeout_seconds: float = Field(default=30, ge=1, le=60)
    matching_ai_max_candidates: int = Field(default=5, ge=1, le=10)
    matching_ai_weight: float = Field(default=0.6, ge=0, le=1)
    matching_ai_max_image_bytes: int = Field(default=5 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    @model_validator(mode="after")
    def validate_matching_ai(self) -> "Settings":
        if self.matching_ai_base_url:
            url = self.matching_ai_base_url
            if url.username or url.password or url.query or url.fragment:
                raise ValueError("MATCHING_AI_BASE_URL 不能包含凭据、查询参数或片段")
            if url.scheme != "https" and url.host not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("远程 MATCHING_AI_BASE_URL 必须使用 HTTPS")
        if self.matching_ai_enabled and (
            not self.matching_ai_base_url
            or not self.matching_ai_api_key.get_secret_value().strip()
            or not self.matching_ai_model.strip()
        ):
            raise ValueError("启用 AI 匹配需要配置 BASE_URL、API_KEY 和 MODEL")
        return self


@lru_cache
def get_settings() -> Settings:
    """缓存配置对象，避免每次请求都重新读取环境变量。"""

    return Settings()
