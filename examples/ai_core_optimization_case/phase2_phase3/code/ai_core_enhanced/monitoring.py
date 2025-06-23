"""
AI智能体性能监控系统
提供智能体调用的性能监控、指标收集和分析功能
"""

import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger


@dataclass
class PerformanceMetric:
    """性能指标数据类"""

    agent_name: str
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def timestamp(self) -> str:
        """获取时间戳字符串"""
        return datetime.fromtimestamp(self.start_time).isoformat()


@dataclass
class AgentStats:
    """智能体统计信息"""

    agent_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    last_call_time: Optional[str] = None
    error_rate: float = 0.0

    def update(self, metric: PerformanceMetric) -> None:
        """更新统计信息"""
        self.total_calls += 1
        self.total_duration += metric.duration
        self.avg_duration = self.total_duration / self.total_calls

        if metric.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.min_duration = min(self.min_duration, metric.duration)
        self.max_duration = max(self.max_duration, metric.duration)
        self.last_call_time = metric.timestamp
        self.error_rate = (
            self.failed_calls / self.total_calls if self.total_calls > 0 else 0.0
        )


class AgentMonitor:
    """智能体性能监控器"""

    def __init__(self, max_metrics: int = 1000):
        """
        初始化监控器

        Args:
            max_metrics: 最大保存的指标数量
        """
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.stats: Dict[str, AgentStats] = {}
        self.operation_stats: Dict[str, Dict[str, AgentStats]] = defaultdict(dict)
        self.active_operations: Dict[str, float] = {}

        logger.info(f"📊 [智能体监控器] 初始化完成 | 最大指标数: {max_metrics}")

    @asynccontextmanager
    async def track_operation(
        self, agent_name: str, operation: str = "default", **metadata
    ):
        """
        跟踪智能体操作的上下文管理器

        Args:
            agent_name: 智能体名称
            operation: 操作名称
            **metadata: 附加元数据
        """
        operation_id = f"{agent_name}:{operation}:{id(asyncio.current_task())}"
        start_time = time.time()
        self.active_operations[operation_id] = start_time

        logger.debug(f"🚀 [智能体监控器] 开始跟踪操作: {agent_name}.{operation}")

        try:
            yield
            # 操作成功
            end_time = time.time()
            duration = end_time - start_time

            metric = PerformanceMetric(
                agent_name=agent_name,
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=True,
                metadata=metadata,
            )

            self._record_metric(metric)
            logger.debug(
                f"✅ [智能体监控器] 操作完成: {agent_name}.{operation} | 耗时: {duration:.3f}s"
            )

        except Exception as e:
            # 操作失败
            end_time = time.time()
            duration = end_time - start_time

            metric = PerformanceMetric(
                agent_name=agent_name,
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=False,
                error_message=str(e),
                metadata=metadata,
            )

            self._record_metric(metric)
            logger.error(
                f"❌ [智能体监控器] 操作失败: {agent_name}.{operation} | 耗时: {duration:.3f}s | 错误: {e}"
            )
            raise

        finally:
            # 清理活跃操作记录
            self.active_operations.pop(operation_id, None)

    def _record_metric(self, metric: PerformanceMetric) -> None:
        """记录性能指标"""
        # 添加到指标队列
        self.metrics.append(metric)

        # 更新智能体统计
        if metric.agent_name not in self.stats:
            self.stats[metric.agent_name] = AgentStats(agent_name=metric.agent_name)
        self.stats[metric.agent_name].update(metric)

        # 更新操作统计
        if metric.agent_name not in self.operation_stats[metric.operation]:
            self.operation_stats[metric.operation][metric.agent_name] = AgentStats(
                agent_name=f"{metric.agent_name}.{metric.operation}"
            )
        self.operation_stats[metric.operation][metric.agent_name].update(metric)

    def get_agent_stats(self, agent_name: str) -> Optional[AgentStats]:
        """获取智能体统计信息"""
        return self.stats.get(agent_name)

    def get_operation_stats(self, operation: str) -> Dict[str, AgentStats]:
        """获取操作统计信息"""
        return self.operation_stats.get(operation, {})

    def get_all_stats(self) -> Dict[str, AgentStats]:
        """获取所有智能体统计信息"""
        return self.stats.copy()

    def get_recent_metrics(
        self,
        agent_name: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        """
        获取最近的性能指标

        Args:
            agent_name: 智能体名称过滤
            operation: 操作名称过滤
            limit: 返回数量限制

        Returns:
            List[PerformanceMetric]: 性能指标列表
        """
        filtered_metrics = []

        for metric in reversed(self.metrics):
            if agent_name and metric.agent_name != agent_name:
                continue
            if operation and metric.operation != operation:
                continue

            filtered_metrics.append(metric)

            if len(filtered_metrics) >= limit:
                break

        return filtered_metrics

    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """获取当前活跃的操作"""
        current_time = time.time()
        active_ops = {}

        for operation_id, start_time in self.active_operations.items():
            agent_name, operation, task_id = operation_id.split(":", 2)
            duration = current_time - start_time

            active_ops[operation_id] = {
                "agent_name": agent_name,
                "operation": operation,
                "task_id": task_id,
                "duration": duration,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
            }

        return active_ops

    def get_performance_summary(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        获取性能摘要

        Args:
            time_window: 时间窗口，None表示全部时间

        Returns:
            Dict[str, Any]: 性能摘要
        """
        if time_window:
            cutoff_time = time.time() - time_window.total_seconds()
            filtered_metrics = [m for m in self.metrics if m.start_time >= cutoff_time]
        else:
            filtered_metrics = list(self.metrics)

        if not filtered_metrics:
            return {"message": "没有性能数据"}

        # 计算总体统计
        total_calls = len(filtered_metrics)
        successful_calls = sum(1 for m in filtered_metrics if m.success)
        failed_calls = total_calls - successful_calls
        total_duration = sum(m.duration for m in filtered_metrics)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0

        # 按智能体分组统计
        agent_summary = {}
        for agent_name in set(m.agent_name for m in filtered_metrics):
            agent_metrics = [m for m in filtered_metrics if m.agent_name == agent_name]
            agent_summary[agent_name] = {
                "total_calls": len(agent_metrics),
                "successful_calls": sum(1 for m in agent_metrics if m.success),
                "failed_calls": sum(1 for m in agent_metrics if not m.success),
                "avg_duration": sum(m.duration for m in agent_metrics)
                / len(agent_metrics),
                "error_rate": sum(1 for m in agent_metrics if not m.success)
                / len(agent_metrics),
            }

        return {
            "time_window": str(time_window) if time_window else "全部时间",
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "active_operations": len(self.active_operations),
            "agents": agent_summary,
        }

    def clear_metrics(self) -> None:
        """清除所有指标数据"""
        self.metrics.clear()
        self.stats.clear()
        self.operation_stats.clear()
        logger.info("🧹 [智能体监控器] 指标数据已清除")


# 全局监控器实例
_agent_monitor: Optional[AgentMonitor] = None


def get_agent_monitor() -> AgentMonitor:
    """获取全局智能体监控器实例（单例模式）"""
    global _agent_monitor
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor()
    return _agent_monitor


# 便捷装饰器
def monitor_agent_operation(operation: str = "default", **metadata):
    """
    智能体操作监控装饰器

    Args:
        operation: 操作名称
        **metadata: 附加元数据
    """

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                # 尝试从参数中获取智能体名称
                agent_name = "unknown"
                if args and hasattr(args[0], "__class__"):
                    agent_name = args[0].__class__.__name__

                monitor = get_agent_monitor()
                async with monitor.track_operation(agent_name, operation, **metadata):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                # 同步函数的监控实现
                agent_name = "unknown"
                if args and hasattr(args[0], "__class__"):
                    agent_name = args[0].__class__.__name__

                monitor = get_agent_monitor()
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    duration = end_time - start_time

                    metric = PerformanceMetric(
                        agent_name=agent_name,
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        success=True,
                        metadata=metadata,
                    )
                    monitor._record_metric(metric)
                    return result

                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time

                    metric = PerformanceMetric(
                        agent_name=agent_name,
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        success=False,
                        error_message=str(e),
                        metadata=metadata,
                    )
                    monitor._record_metric(metric)
                    raise

            return sync_wrapper

    return decorator


# 导出接口
__all__ = [
    "PerformanceMetric",
    "AgentStats",
    "AgentMonitor",
    "get_agent_monitor",
    "monitor_agent_operation",
]
