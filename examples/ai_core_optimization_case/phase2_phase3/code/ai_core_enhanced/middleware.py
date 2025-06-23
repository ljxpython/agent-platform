"""
AI智能体中间件系统
提供智能体操作的中间件支持，实现横切关注点的统一处理
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger


@dataclass
class MiddlewareContext:
    """中间件上下文"""

    agent_name: str
    operation: str
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseMiddleware(ABC):
    """中间件基类"""

    def __init__(self, name: str, priority: int = 0):
        """
        初始化中间件

        Args:
            name: 中间件名称
            priority: 优先级（数字越小优先级越高）
        """
        self.name = name
        self.priority = priority
        self.enabled = True

    @abstractmethod
    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        """
        操作前处理

        Args:
            context: 中间件上下文
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 是否继续执行（False表示中断）
        """
        pass

    @abstractmethod
    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        """
        操作后处理

        Args:
            context: 中间件上下文
            result: 操作结果
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 处理后的结果
        """
        pass

    @abstractmethod
    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        """
        错误处理

        Args:
            context: 中间件上下文
            error: 异常对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 是否已处理错误（True表示错误已处理，不再抛出）
        """
        pass


class LoggingMiddleware(BaseMiddleware):
    """日志中间件"""

    def __init__(self, priority: int = 100):
        super().__init__("logging", priority)

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        logger.info(
            f"🚀 [中间件-日志] 开始操作: {context.agent_name}.{context.operation}"
        )
        context.metadata["start_time"] = time.time()
        return True

    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        duration = time.time() - context.metadata.get("start_time", 0)
        logger.info(
            f"✅ [中间件-日志] 操作完成: {context.agent_name}.{context.operation} | 耗时: {duration:.3f}s"
        )
        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        duration = time.time() - context.metadata.get("start_time", 0)
        logger.error(
            f"❌ [中间件-日志] 操作失败: {context.agent_name}.{context.operation} | 耗时: {duration:.3f}s | 错误: {error}"
        )
        return False


class PerformanceMiddleware(BaseMiddleware):
    """性能监控中间件"""

    def __init__(self, priority: int = 90):
        super().__init__("performance", priority)
        self.metrics: Dict[str, List[float]] = {}

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        context.metadata["perf_start_time"] = time.time()
        return True

    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        duration = time.time() - context.metadata.get("perf_start_time", 0)

        # 记录性能指标
        operation_key = f"{context.agent_name}.{context.operation}"
        if operation_key not in self.metrics:
            self.metrics[operation_key] = []
        self.metrics[operation_key].append(duration)

        # 保持最近100次记录
        if len(self.metrics[operation_key]) > 100:
            self.metrics[operation_key] = self.metrics[operation_key][-100:]

        logger.debug(f"📊 [中间件-性能] {operation_key} | 耗时: {duration:.3f}s")
        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        duration = time.time() - context.metadata.get("perf_start_time", 0)
        logger.debug(
            f"📊 [中间件-性能] {context.agent_name}.{context.operation} | 失败耗时: {duration:.3f}s"
        )
        return False

    def get_metrics(self, operation_key: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标"""
        if operation_key:
            durations = self.metrics.get(operation_key, [])
            if durations:
                return {
                    "operation": operation_key,
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "recent": durations[-10:],
                }
            return {"operation": operation_key, "count": 0}

        # 返回所有指标的摘要
        summary = {}
        for op_key, durations in self.metrics.items():
            if durations:
                summary[op_key] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }
        return summary


class ValidationMiddleware(BaseMiddleware):
    """参数验证中间件"""

    def __init__(self, priority: int = 10):
        super().__init__("validation", priority)
        self.validators: Dict[str, Callable] = {}

    def register_validator(self, operation: str, validator: Callable) -> None:
        """注册验证器"""
        self.validators[operation] = validator
        logger.debug(f"🔍 [中间件-验证] 注册验证器: {operation}")

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        operation_key = f"{context.agent_name}.{context.operation}"
        validator = self.validators.get(operation_key) or self.validators.get(
            context.operation
        )

        if validator:
            try:
                if asyncio.iscoroutinefunction(validator):
                    is_valid = await validator(*args, **kwargs)
                else:
                    is_valid = validator(*args, **kwargs)

                if not is_valid:
                    logger.warning(f"⚠️ [中间件-验证] 参数验证失败: {operation_key}")
                    return False

                logger.debug(f"✅ [中间件-验证] 参数验证通过: {operation_key}")

            except Exception as e:
                logger.error(
                    f"❌ [中间件-验证] 验证器执行失败: {operation_key} | 错误: {e}"
                )
                return False

        return True

    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        return False


class CacheMiddleware(BaseMiddleware):
    """缓存中间件"""

    def __init__(self, priority: int = 20, ttl: int = 300):
        super().__init__("cache", priority)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl  # 缓存生存时间（秒）

    def _get_cache_key(self, context: MiddlewareContext, *args, **kwargs) -> str:
        """生成缓存键"""
        # 简单的缓存键生成策略
        key_parts = [context.agent_name, context.operation]

        # 添加参数到键中（简化处理）
        if args:
            key_parts.extend([str(arg)[:50] for arg in args])
        if kwargs:
            key_parts.extend([f"{k}={str(v)[:50]}" for k, v in sorted(kwargs.items())])

        return "|".join(key_parts)

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        return time.time() - cache_entry["timestamp"] < self.ttl

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        cache_key = self._get_cache_key(context, *args, **kwargs)

        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                # 缓存命中
                context.metadata["cache_hit"] = True
                context.metadata["cached_result"] = cache_entry["result"]
                logger.debug(
                    f"🎯 [中间件-缓存] 缓存命中: {context.agent_name}.{context.operation}"
                )
                return False  # 跳过实际操作
            else:
                # 缓存过期
                del self.cache[cache_key]
                logger.debug(
                    f"⏰ [中间件-缓存] 缓存过期: {context.agent_name}.{context.operation}"
                )

        context.metadata["cache_key"] = cache_key
        return True

    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        # 如果是缓存命中，返回缓存的结果
        if context.metadata.get("cache_hit"):
            return context.metadata["cached_result"]

        # 存储结果到缓存
        cache_key = context.metadata.get("cache_key")
        if cache_key:
            self.cache[cache_key] = {"result": result, "timestamp": time.time()}
            logger.debug(
                f"💾 [中间件-缓存] 结果已缓存: {context.agent_name}.{context.operation}"
            )

        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        return False

    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """清除缓存"""
        if pattern:
            # 清除匹配模式的缓存
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(
                f"🧹 [中间件-缓存] 清除匹配缓存: {pattern} | 数量: {len(keys_to_remove)}"
            )
        else:
            # 清除所有缓存
            cache_count = len(self.cache)
            self.cache.clear()
            logger.info(f"🧹 [中间件-缓存] 清除所有缓存 | 数量: {cache_count}")


class MiddlewareManager:
    """中间件管理器"""

    def __init__(self):
        """初始化中间件管理器"""
        self.middlewares: List[BaseMiddleware] = []
        self.enabled = True

        logger.info("🔧 [中间件管理器] 初始化完成")

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """添加中间件"""
        self.middlewares.append(middleware)
        # 按优先级排序
        self.middlewares.sort(key=lambda m: m.priority)
        logger.info(
            f"➕ [中间件管理器] 添加中间件: {middleware.name} | 优先级: {middleware.priority}"
        )

    def remove_middleware(self, name: str) -> bool:
        """移除中间件"""
        for i, middleware in enumerate(self.middlewares):
            if middleware.name == name:
                del self.middlewares[i]
                logger.info(f"➖ [中间件管理器] 移除中间件: {name}")
                return True
        return False

    def get_middleware(self, name: str) -> Optional[BaseMiddleware]:
        """获取中间件"""
        for middleware in self.middlewares:
            if middleware.name == name:
                return middleware
        return None

    def enable_middleware(self, name: str) -> bool:
        """启用中间件"""
        middleware = self.get_middleware(name)
        if middleware:
            middleware.enabled = True
            logger.info(f"✅ [中间件管理器] 启用中间件: {name}")
            return True
        return False

    def disable_middleware(self, name: str) -> bool:
        """禁用中间件"""
        middleware = self.get_middleware(name)
        if middleware:
            middleware.enabled = False
            logger.info(f"⏸️ [中间件管理器] 禁用中间件: {name}")
            return True
        return False

    async def execute_middleware_chain(
        self, context: MiddlewareContext, operation_func: Callable, *args, **kwargs
    ) -> Any:
        """
        执行中间件链

        Args:
            context: 中间件上下文
            operation_func: 要执行的操作函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 操作结果
        """
        if not self.enabled:
            # 中间件系统禁用，直接执行操作
            return (
                await operation_func(*args, **kwargs)
                if asyncio.iscoroutinefunction(operation_func)
                else operation_func(*args, **kwargs)
            )

        # 执行前置中间件
        for middleware in self.middlewares:
            if not middleware.enabled:
                continue

            try:
                should_continue = await middleware.before_operation(
                    context, *args, **kwargs
                )
                if not should_continue:
                    # 中间件要求停止执行
                    logger.debug(f"🛑 [中间件管理器] 中间件停止执行: {middleware.name}")
                    # 检查是否有缓存结果
                    if "cached_result" in context.metadata:
                        return context.metadata["cached_result"]
                    return None
            except Exception as e:
                logger.error(
                    f"❌ [中间件管理器] 前置中间件执行失败: {middleware.name} | 错误: {e}"
                )

        # 执行主操作
        try:
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)

            # 执行后置中间件
            for middleware in reversed(self.middlewares):
                if not middleware.enabled:
                    continue

                try:
                    result = await middleware.after_operation(
                        context, result, *args, **kwargs
                    )
                except Exception as e:
                    logger.error(
                        f"❌ [中间件管理器] 后置中间件执行失败: {middleware.name} | 错误: {e}"
                    )

            return result

        except Exception as e:
            # 执行错误处理中间件
            error_handled = False
            for middleware in self.middlewares:
                if not middleware.enabled:
                    continue

                try:
                    handled = await middleware.on_error(context, e, *args, **kwargs)
                    if handled:
                        error_handled = True
                        break
                except Exception as middleware_error:
                    logger.error(
                        f"❌ [中间件管理器] 错误处理中间件失败: {middleware.name} | 错误: {middleware_error}"
                    )

            if not error_handled:
                raise e

            return None

    def list_middlewares(self) -> List[Dict[str, Any]]:
        """列出所有中间件"""
        return [
            {
                "name": m.name,
                "priority": m.priority,
                "enabled": m.enabled,
                "type": type(m).__name__,
            }
            for m in self.middlewares
        ]


# 全局中间件管理器实例
_middleware_manager: Optional[MiddlewareManager] = None


def get_middleware_manager() -> MiddlewareManager:
    """获取全局中间件管理器实例（单例模式）"""
    global _middleware_manager
    if _middleware_manager is None:
        _middleware_manager = MiddlewareManager()
        # 添加默认中间件
        _middleware_manager.add_middleware(LoggingMiddleware())
        _middleware_manager.add_middleware(PerformanceMiddleware())
    return _middleware_manager


# 便捷装饰器
def with_middleware(
    agent_name: str, operation: str, conversation_id: Optional[str] = None
):
    """
    中间件装饰器

    Args:
        agent_name: 智能体名称
        operation: 操作名称
        conversation_id: 对话ID
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = MiddlewareContext(
                agent_name=agent_name,
                operation=operation,
                conversation_id=conversation_id,
            )

            manager = get_middleware_manager()
            return await manager.execute_middleware_chain(
                context, func, *args, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = MiddlewareContext(
                agent_name=agent_name,
                operation=operation,
                conversation_id=conversation_id,
            )

            manager = get_middleware_manager()
            # 对于同步函数，需要在异步环境中运行
            return asyncio.run(
                manager.execute_middleware_chain(context, func, *args, **kwargs)
            )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# 导出接口
__all__ = [
    "MiddlewareContext",
    "BaseMiddleware",
    "LoggingMiddleware",
    "PerformanceMiddleware",
    "ValidationMiddleware",
    "CacheMiddleware",
    "MiddlewareManager",
    "get_middleware_manager",
    "with_middleware",
]
