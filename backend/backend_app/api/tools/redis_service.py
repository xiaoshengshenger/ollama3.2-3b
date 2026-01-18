from typing import Any, Optional, List, Dict, TYPE_CHECKING
from typing_extensions import Literal

import redis
import json
from injector import inject, singleton
from pydantic import BaseModel, Field
from redis.exceptions import RedisError, ConnectionError, TimeoutError

if TYPE_CHECKING:
    from redis import Redis as RedisClient


class RedisConfig(BaseModel):
    """Redis 连接配置模型"""
    host: str = Field(default="localhost", examples=["127.0.0.1"])
    port: int = Field(default=6379, examples=[6379])
    db: int = Field(default=0, examples=[0])
    password: Optional[str] = Field(default=None, examples=["your_redis_pwd"])
    socket_timeout: int = Field(default=5, examples=[5])
    socket_connect_timeout: int = Field(default=5, examples=[5])
    decode_responses: bool = Field(default=True, examples=[True])


@singleton
class RedisService:
    """
    Redis 缓存服务类（适配项目依赖注入风格）
    提供标准化的 Redis 操作接口，支持对象序列化/反序列化
    """
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional["RedisClient"] = None

    @inject
    def __init__(self, redis_config: Optional[RedisConfig] = None) -> None:
        """
        初始化 Redis 连接池和客户端
        :param redis_config: Redis 连接配置（支持依赖注入传入）
        """
        # 使用默认配置如果未传入
        self.config = redis_config or RedisConfig()
        self._init_connection()

    def _init_connection(self) -> None:
        """初始化 Redis 连接池和客户端"""
        try:
            # 创建连接池（单例模式，全局唯一）
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=self.config.decode_responses
            )
            # 获取客户端实例
            self._client = redis.Redis(connection_pool=self._pool)
            # 测试连接
            self._client.ping()
        except (ConnectionError, TimeoutError) as e:
            raise RedisError(f"Redis 连接失败: {str(e)}") from e

    def _get_client(self) -> "RedisClient":
        """获取 Redis 客户端（确保连接有效）"""
        if not self._client or not self._pool:
            self._init_connection()
        return self._client

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置缓存值
        :param key: 缓存键
        :param value: 缓存值（支持任意可序列化对象）
        :param ex: 过期时间（秒）
        :param px: 过期时间（毫秒）
        :param nx: 仅当键不存在时设置
        :param xx: 仅当键存在时设置
        :return: 设置成功返回 True，失败返回 False
        """
        try:
            # 序列化非基础类型值
            serialized_value = self._serialize_value(value)
            
            client = self._get_client()
            result = client.set(
                name=key,
                value=serialized_value,
                ex=ex,
                px=px,
                nx=nx,
                xx=xx
            )
            return result is True
        except RedisError as e:
            raise RedisError(f"设置缓存失败 (key={key}): {str(e)}") from e

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        :param key: 缓存键
        :return: 反序列化后的缓存值，不存在返回 None
        """
        try:
            client = self._get_client()
            value = client.get(key)
            if value is None:
                return None
            # 反序列化值
            return self._deserialize_value(value)
        except RedisError as e:
            raise RedisError(f"获取缓存失败 (key={key}): {str(e)}") from e

    def delete(self, *keys: str) -> int:
        """
        批量删除缓存
        :param keys: 缓存键列表
        :return: 成功删除的键数量
        """
        try:
            client = self._get_client()
            return client.delete(*keys)
        except RedisError as e:
            raise RedisError(f"删除缓存失败 (keys={keys}): {str(e)}") from e

    def mset(self, mapping: Dict[str, Any]) -> bool:
        """
        批量设置缓存
        :param mapping: 键值对字典   
        :return: 成功返回 True
        """
        try:
            # 序列化所有值
            serialized_mapping = {
                k: self._serialize_value(v) for k, v in mapping.items()
            }
            client = self._get_client()
            client.mset(serialized_mapping)
            return True
        except RedisError as e:
            raise RedisError(f"批量设置缓存失败: {str(e)}") from e

    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        批量获取缓存
        :param keys: 缓存键列表
        :return: 按顺序返回的值列表（不存在为 None）
        """
        try:
            client = self._get_client()
            values = client.mget(keys)
            # 反序列化每个值
            return [self._deserialize_value(v) if v is not None else None for v in values]
        except RedisError as e:
            raise RedisError(f"批量获取缓存失败 (keys={keys}): {str(e)}") from e

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置缓存过期时间
        :param key: 缓存键
        :param seconds: 过期时间（秒）
        :return: 设置成功返回 True
        """
        try:
            client = self._get_client()
            return client.expire(key, seconds)
        except RedisError as e:
            raise RedisError(f"设置过期时间失败 (key={key}): {str(e)}") from e

    def exists(self, key: str) -> bool:
        """
        判断缓存键是否存在
        :param key: 缓存键
        :return: 存在返回 True，否则 False
        """
        try:
            client = self._get_client()
            return client.exists(key) > 0
        except RedisError as e:
            raise RedisError(f"检查键存在性失败 (key={key}): {str(e)}") from e

    def _serialize_value(self, value: Any) -> str | int | float | bool:
        """
        序列化值为 Redis 可存储的类型
        :param value: 任意类型的值
        :return: 序列化后的值
        """
        if isinstance(value, (str, int, float, bool)):
            return value
        # 对其他类型（字典、列表等）进行 JSON 序列化
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_value(self, value: str) -> Any:
        """
        反序列化 Redis 存储的值
        :param value: 字符串值
        :return: 反序列化后的原始对象
        """
        try:
            # 尝试解析为 JSON
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 非 JSON 格式直接返回
            return value

    def close(self) -> None:
        """关闭 Redis 连接池"""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            self._client = None