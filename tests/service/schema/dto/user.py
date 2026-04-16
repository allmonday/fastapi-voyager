"""
User and UserAddress DTOs.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """用户"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="用户唯一标识 ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")


class UserAddress(BaseModel):
    """用户地址"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="地址 ID")
    user_id: int = Field(description="用户 ID")
    province: str = Field(description="省份")
    city: str = Field(description="城市")
    district: str = Field(description="区县")
    detail: str = Field(description="详细地址")
    is_default: bool = Field(default=False, description="是否默认地址")
