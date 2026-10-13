# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
# 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
"""认证 API 的请求、响应和枚举契约。

本模块负责：
- 校验注册与登录请求的公开字段；
- 定义用户角色、账号状态以及返回给前端的安全用户摘要；
- 使用 ``SecretStr`` 避免密码在对象日志和调试输出中直接出现。

本模块不负责密码哈希、会话签发或数据库持久化；这些职责分别属于
``core.security``、``services.auth_service`` 和 ``repositories.auth_repository``。
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, SecretStr


# 文档对应：图2-1 校园用户及系统管理员的权限角色；3.1节。
class UserRole(StrEnum):
    """当前系统支持的用户角色。"""

    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    """账号是否允许建立和继续使用会话。"""

    ACTIVE = "active"
    RESTRICTED = "restricted"


# 文档对应：图2-2-1a 注册输入；2.2节用例业务规则 账号3至64字符、注册密码8至128字符。
# 设计文档对应：图4-1-1 注册请求约束。
class RegisterRequest(BaseModel):
    """使用校园账号和密码创建本地账号。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    account: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._@-]+$",
        examples=["20260001"],
    )
    password: SecretStr = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=50)


# 文档对应：图2-2-1 登录输入；2.2.1节 已有凭据核验。
# 设计文档对应：图4-1-2 登录请求约束。
class LoginRequest(BaseModel):
    """使用账号和密码换取服务端会话令牌。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    account: str = Field(min_length=3, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=128)


# 设计文档对应：图4-2 Service 返回的公开用户摘要。
class UserRead(BaseModel):
    """可以安全返回给已登录用户的账号摘要。"""

    id: int
    account: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    campus_verified: bool
    created_at: datetime


# 设计文档对应：图4-1-2 登录令牌与用户摘要响应。
class TokenResponse(BaseModel):
    """登录成功后返回的不透明 Bearer 令牌。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0, description="令牌剩余有效秒数")
    user: UserRead
