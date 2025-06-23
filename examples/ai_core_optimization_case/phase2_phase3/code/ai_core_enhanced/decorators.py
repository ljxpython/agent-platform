"""
AI智能体装饰器系统
提供简化开发的装饰器，集成监控、调试、中间件等功能
"""

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from .debug import TraceLevel, get_agent_debugger
from .logging_enhanced import get_performance_logger, get_structured_logger
from .middleware import MiddlewareContext, get_middleware_manager
from .monitoring import get_agent_monitor


def agent_operation(
    operation_name: str = None,
    agent_name: str = None,
    enable_monitoring: bool = True,
    enable_debug: bool = True,
    enable_middleware: bool = True,
    conversation_id: Optional[str] = None,
    **metadata,
):
    """
    智能体操作装饰器 - 集成监控、调试、中间件功能

    Args:
        operation_name: 操作名称
        agent_name: 智能体名称
        enable_monitoring: 是否启用监控
        enable_debug: 是否启用调试
        enable_middleware: 是否启用中间件
        conversation_id: 对话ID
        **metadata: 附加元数据
    """

    def decorator(func: Callable) -> Callable:
        # 获取操作名称和智能体名称
        op_name = operation_name or func.__name__
        ag_name = agent_name or getattr(func, "__qualname__", "unknown").split(".")[0]

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 尝试从参数中获取conversation_id
                conv_id = conversation_id
                if not conv_id and kwargs.get("conversation_id"):
                    conv_id = kwargs["conversation_id"]
                elif (
                    not conv_id and args and len(args) > 1 and isinstance(args[1], str)
                ):
                    # 假设第二个参数是conversation_id
                    conv_id = args[1]
                elif not conv_id and args and hasattr(args[0], "conversation_id"):
                    conv_id = getattr(args[0], "conversation_id", None)

                # 监控
                monitor = get_agent_monitor() if enable_monitoring else None

                # 调试
                debugger = get_agent_debugger() if enable_debug else None

                # 中间件
                middleware_manager = (
                    get_middleware_manager() if enable_middleware else None
                )

                # 结构化日志
                structured_logger = get_structured_logger()

                # 开始操作
                if debugger:
                    debugger.trace_event(
                        ag_name,
                        op_name,
                        "operation_started",
                        f"开始执行操作: {op_name}",
                        TraceLevel.INFO,
                        metadata,
                        conv_id,
                    )

                structured_logger.log_agent_operation(
                    ag_name,
                    op_name,
                    "started",
                    conversation_id=conv_id,
                    metadata=metadata,
                )

                try:
                    if enable_middleware and middleware_manager:
                        # 使用中间件执行
                        context = MiddlewareContext(
                            agent_name=ag_name,
                            operation=op_name,
                            conversation_id=conv_id,
                            metadata=metadata.copy(),
                        )
                        result = await middleware_manager.execute_middleware_chain(
                            context, func, *args, **kwargs
                        )
                    elif enable_monitoring and monitor:
                        # 使用监控执行
                        async with monitor.track_operation(
                            ag_name, op_name, **metadata
                        ):
                            result = await func(*args, **kwargs)
                    else:
                        # 直接执行
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        duration = time.time() - start_time

                        structured_logger.log_agent_operation(
                            ag_name,
                            op_name,
                            "completed",
                            duration,
                            conversation_id=conv_id,
                            metadata=metadata,
                        )

                    # 成功完成
                    if debugger:
                        debugger.trace_event(
                            ag_name,
                            op_name,
                            "operation_completed",
                            f"操作完成: {op_name}",
                            TraceLevel.INFO,
                            {"result_type": type(result).__name__},
                            conv_id,
                        )

                    return result

                except Exception as e:
                    # 错误处理
                    if debugger:
                        debugger.trace_event(
                            ag_name,
                            op_name,
                            "operation_failed",
                            f"操作失败: {op_name} | 错误: {str(e)}",
                            TraceLevel.ERROR,
                            {"error_type": type(e).__name__},
                            conv_id,
                        )

                    structured_logger.log_agent_operation(
                        ag_name,
                        op_name,
                        "failed",
                        conversation_id=conv_id,
                        metadata={**metadata, "error": str(e)},
                    )

                    raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步函数的简化处理
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    structured_logger = get_structured_logger()
                    structured_logger.log_agent_operation(
                        ag_name,
                        op_name,
                        "completed",
                        duration,
                        conversation_id=conversation_id,
                        metadata=metadata,
                    )

                    return result

                except Exception as e:
                    duration = time.time() - start_time

                    structured_logger = get_structured_logger()
                    structured_logger.log_agent_operation(
                        ag_name,
                        op_name,
                        "failed",
                        duration,
                        conversation_id=conversation_id,
                        metadata={**metadata, "error": str(e)},
                    )

                    raise

            return sync_wrapper

    return decorator


def monitor_performance(metric_name: str = None, tags: Optional[Dict[str, str]] = None):
    """
    性能监控装饰器

    Args:
        metric_name: 指标名称
        tags: 标签
    """

    def decorator(func: Callable) -> Callable:
        perf_name = metric_name or f"{func.__name__}_performance"

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                performance_logger = get_performance_logger()

                with performance_logger.timer(perf_name, tags):
                    result = await func(*args, **kwargs)

                # 记录内存使用
                performance_logger.log_memory_usage(perf_name, tags)

                return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                performance_logger = get_performance_logger()

                with performance_logger.timer(perf_name, tags):
                    result = func(*args, **kwargs)

                performance_logger.log_memory_usage(perf_name, tags)

                return result

            return sync_wrapper

    return decorator


def debug_trace(event_type: str = None, level: TraceLevel = TraceLevel.INFO):
    """
    调试跟踪装饰器

    Args:
        event_type: 事件类型
        level: 跟踪级别
    """

    def decorator(func: Callable) -> Callable:
        event_name = event_type or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                debugger = get_agent_debugger()

                # 获取智能体名称
                agent_name = "unknown"
                if args and hasattr(args[0], "__class__"):
                    agent_name = args[0].__class__.__name__

                # 获取对话ID
                conversation_id = None
                if kwargs.get("conversation_id"):
                    conversation_id = kwargs["conversation_id"]
                elif args and hasattr(args[0], "conversation_id"):
                    conversation_id = getattr(args[0], "conversation_id", None)

                debugger.trace_event(
                    agent_name,
                    func.__name__,
                    f"{event_name}_started",
                    f"开始执行: {func.__name__}",
                    level,
                    {"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
                    conversation_id,
                )

                try:
                    result = await func(*args, **kwargs)

                    debugger.trace_event(
                        agent_name,
                        func.__name__,
                        f"{event_name}_completed",
                        f"执行完成: {func.__name__}",
                        level,
                        {"result_type": type(result).__name__},
                        conversation_id,
                    )

                    return result

                except Exception as e:
                    debugger.trace_event(
                        agent_name,
                        func.__name__,
                        f"{event_name}_failed",
                        f"执行失败: {func.__name__} | 错误: {str(e)}",
                        TraceLevel.ERROR,
                        {"error_type": type(e).__name__},
                        conversation_id,
                    )
                    raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                debugger = get_agent_debugger()

                agent_name = "unknown"
                if args and hasattr(args[0], "__class__"):
                    agent_name = args[0].__class__.__name__

                debugger.trace_event(
                    agent_name,
                    func.__name__,
                    f"{event_name}_started",
                    f"开始执行: {func.__name__}",
                    level,
                    {"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
                )

                try:
                    result = func(*args, **kwargs)

                    debugger.trace_event(
                        agent_name,
                        func.__name__,
                        f"{event_name}_completed",
                        f"执行完成: {func.__name__}",
                        level,
                        {"result_type": type(result).__name__},
                    )

                    return result

                except Exception as e:
                    debugger.trace_event(
                        agent_name,
                        func.__name__,
                        f"{event_name}_failed",
                        f"执行失败: {func.__name__} | 错误: {str(e)}",
                        TraceLevel.ERROR,
                        {"error_type": type(e).__name__},
                    )
                    raise

            return sync_wrapper

    return decorator


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    结果缓存装饰器

    Args:
        ttl: 缓存生存时间（秒）
        key_func: 自定义键生成函数
    """
    cache = {}

    def default_key_func(*args, **kwargs):
        """默认键生成函数"""
        key_parts = []
        key_parts.extend([str(arg)[:50] for arg in args])
        key_parts.extend([f"{k}={str(v)[:50]}" for k, v in sorted(kwargs.items())])
        return "|".join(key_parts)

    key_generator = key_func or default_key_func

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{key_generator(*args, **kwargs)}"

                # 检查缓存
                if cache_key in cache:
                    cached_data = cache[cache_key]
                    if time.time() - cached_data["timestamp"] < ttl:
                        logger.debug(f"🎯 [缓存装饰器] 缓存命中: {func.__name__}")
                        return cached_data["result"]
                    else:
                        # 缓存过期
                        del cache[cache_key]

                # 执行函数
                result = await func(*args, **kwargs)

                # 存储到缓存
                cache[cache_key] = {"result": result, "timestamp": time.time()}

                logger.debug(f"💾 [缓存装饰器] 结果已缓存: {func.__name__}")
                return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{key_generator(*args, **kwargs)}"

                if cache_key in cache:
                    cached_data = cache[cache_key]
                    if time.time() - cached_data["timestamp"] < ttl:
                        logger.debug(f"🎯 [缓存装饰器] 缓存命中: {func.__name__}")
                        return cached_data["result"]
                    else:
                        del cache[cache_key]

                result = func(*args, **kwargs)

                cache[cache_key] = {"result": result, "timestamp": time.time()}

                logger.debug(f"💾 [缓存装饰器] 结果已缓存: {func.__name__}")
                return result

            return sync_wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    失败重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
    """

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay

                for attempt in range(max_retries + 1):
                    try:
                        result = await func(*args, **kwargs)
                        if attempt > 0:
                            logger.info(
                                f"✅ [重试装饰器] 重试成功: {func.__name__} | 尝试次数: {attempt + 1}"
                            )
                        return result

                    except Exception as e:
                        last_exception = e

                        if attempt < max_retries:
                            logger.warning(
                                f"⚠️ [重试装饰器] 重试 {attempt + 1}/{max_retries}: {func.__name__} | 错误: {e}"
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            logger.error(
                                f"❌ [重试装饰器] 重试失败: {func.__name__} | 最终错误: {e}"
                            )

                raise last_exception

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay

                for attempt in range(max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        if attempt > 0:
                            logger.info(
                                f"✅ [重试装饰器] 重试成功: {func.__name__} | 尝试次数: {attempt + 1}"
                            )
                        return result

                    except Exception as e:
                        last_exception = e

                        if attempt < max_retries:
                            logger.warning(
                                f"⚠️ [重试装饰器] 重试 {attempt + 1}/{max_retries}: {func.__name__} | 错误: {e}"
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            logger.error(
                                f"❌ [重试装饰器] 重试失败: {func.__name__} | 最终错误: {e}"
                            )

                raise last_exception

            return sync_wrapper

    return decorator


# 组合装饰器
def smart_agent_operation(
    operation_name: str = None,
    agent_name: str = None,
    enable_cache: bool = False,
    cache_ttl: int = 300,
    enable_retry: bool = False,
    max_retries: int = 3,
    **kwargs,
):
    """
    智能智能体操作装饰器 - 组合多种功能

    Args:
        operation_name: 操作名称
        agent_name: 智能体名称
        enable_cache: 是否启用缓存
        cache_ttl: 缓存生存时间
        enable_retry: 是否启用重试
        max_retries: 最大重试次数
        **kwargs: 其他参数
    """

    def decorator(func: Callable) -> Callable:
        # 应用基础装饰器
        decorated_func = agent_operation(operation_name, agent_name, **kwargs)(func)

        # 应用缓存装饰器
        if enable_cache:
            decorated_func = cache_result(cache_ttl)(decorated_func)

        # 应用重试装饰器
        if enable_retry:
            decorated_func = retry_on_failure(max_retries)(decorated_func)

        return decorated_func

    return decorator


# 导出接口
__all__ = [
    "agent_operation",
    "monitor_performance",
    "debug_trace",
    "cache_result",
    "retry_on_failure",
    "smart_agent_operation",
]
