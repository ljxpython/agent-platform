"""
AI智能体增强日志系统
提供结构化日志、性能日志和可视化日志功能
"""

import json
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, log_dir: str = "logs"):
        """
        初始化结构化日志记录器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 配置不同类型的日志文件
        self._setup_loggers()

        logger.info(f"📝 [结构化日志] 初始化完成 | 日志目录: {self.log_dir}")

    def _setup_loggers(self) -> None:
        """设置不同类型的日志记录器"""

        # 智能体操作日志
        logger.add(
            self.log_dir / "agent_operations.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            filter=lambda record: "agent_operation" in record["extra"],
        )

        # 性能日志
        logger.add(
            self.log_dir / "performance.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="7 days",
            filter=lambda record: "performance" in record["extra"],
        )

        # 错误日志
        logger.add(
            self.log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name} | {function} | {line} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="90 days",
        )

        # 结构化JSON日志
        logger.add(
            self.log_dir / "structured.jsonl",
            format=self._json_formatter,
            level="INFO",
            rotation="100 MB",
            retention="30 days",
            filter=lambda record: "structured" in record["extra"],
        )

    def _json_formatter(self, record) -> str:
        """JSON格式化器"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "extra": record["extra"],
        }

        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback,
            }

        return json.dumps(log_entry, ensure_ascii=False)

    def log_agent_operation(
        self,
        agent_name: str,
        operation: str,
        status: str,
        duration: Optional[float] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录智能体操作日志

        Args:
            agent_name: 智能体名称
            operation: 操作名称
            status: 操作状态 (started, completed, failed)
            duration: 操作耗时（秒）
            conversation_id: 对话ID
            metadata: 附加元数据
        """
        log_data = {
            "agent_operation": True,
            "agent_name": agent_name,
            "operation": operation,
            "status": status,
            "conversation_id": conversation_id,
            "metadata": metadata or {},
        }

        if duration is not None:
            log_data["duration"] = duration

        message = f"[{agent_name}] {operation} - {status}"
        if duration:
            message += f" ({duration:.3f}s)"

        logger.bind(**log_data).info(message)

    def log_performance(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        记录性能指标

        Args:
            metric_name: 指标名称
            value: 指标值
            unit: 单位
            tags: 标签
        """
        log_data = {
            "performance": True,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": tags or {},
        }

        message = f"METRIC {metric_name}={value}{unit}"
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
            message += f" [{tag_str}]"

        logger.bind(**log_data).info(message)

    def log_structured(
        self, event_type: str, data: Dict[str, Any], level: str = "INFO"
    ) -> None:
        """
        记录结构化日志

        Args:
            event_type: 事件类型
            data: 结构化数据
            level: 日志级别
        """
        log_data = {"structured": True, "event_type": event_type, **data}

        message = f"EVENT {event_type}"

        log_func = getattr(logger.bind(**log_data), level.lower())
        log_func(message)

    def log_conversation_flow(
        self,
        conversation_id: str,
        step: str,
        agent_name: str,
        message_type: str,
        content_preview: str = "",
    ) -> None:
        """
        记录对话流程日志

        Args:
            conversation_id: 对话ID
            step: 流程步骤
            agent_name: 智能体名称
            message_type: 消息类型
            content_preview: 内容预览
        """
        self.log_structured(
            "conversation_flow",
            {
                "conversation_id": conversation_id,
                "step": step,
                "agent_name": agent_name,
                "message_type": message_type,
                "content_preview": content_preview[:100] if content_preview else "",
            },
        )


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, structured_logger: StructuredLogger):
        """
        初始化性能日志记录器

        Args:
            structured_logger: 结构化日志记录器
        """
        self.structured_logger = structured_logger
        self.active_timers: Dict[str, float] = {}

    @contextmanager
    def timer(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """
        性能计时上下文管理器

        Args:
            operation_name: 操作名称
            tags: 标签
        """
        import time

        start_time = time.time()
        timer_id = f"{operation_name}_{id(self)}"
        self.active_timers[timer_id] = start_time

        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time

            self.structured_logger.log_performance(
                f"{operation_name}_duration", duration, "seconds", tags
            )

            self.active_timers.pop(timer_id, None)

    def log_memory_usage(
        self, operation: str, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录内存使用情况

        Args:
            operation: 操作名称
            tags: 标签
        """
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            self.structured_logger.log_performance(
                f"{operation}_memory_rss",
                memory_info.rss / 1024 / 1024,  # MB
                "MB",
                tags,
            )

            self.structured_logger.log_performance(
                f"{operation}_memory_vms",
                memory_info.vms / 1024 / 1024,  # MB
                "MB",
                tags,
            )

        except ImportError:
            logger.warning("psutil not available, skipping memory logging")
        except Exception as e:
            logger.error(f"Failed to log memory usage: {e}")

    def log_queue_metrics(
        self, queue_name: str, size: int, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录队列指标

        Args:
            queue_name: 队列名称
            size: 队列大小
            tags: 标签
        """
        self.structured_logger.log_performance(
            f"queue_{queue_name}_size", size, "items", tags
        )


class LogAnalyzer:
    """日志分析器"""

    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志分析器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)

    def analyze_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        分析性能趋势

        Args:
            hours: 分析时间范围（小时）

        Returns:
            Dict[str, Any]: 性能趋势分析结果
        """
        try:
            performance_log = self.log_dir / "performance.log"
            if not performance_log.exists():
                return {"error": "性能日志文件不存在"}

            # 简单的日志分析实现
            metrics = {}
            with open(performance_log, "r", encoding="utf-8") as f:
                for line in f:
                    if "METRIC" in line:
                        # 解析指标行
                        parts = line.split("METRIC ")
                        if len(parts) > 1:
                            metric_part = parts[1].split("=")
                            if len(metric_part) > 1:
                                metric_name = metric_part[0]
                                value_part = metric_part[1].split()[0]
                                try:
                                    value = float(
                                        value_part.rstrip("seconds").rstrip("MB")
                                    )
                                    if metric_name not in metrics:
                                        metrics[metric_name] = []
                                    metrics[metric_name].append(value)
                                except ValueError:
                                    continue

            # 计算统计信息
            analysis = {}
            for metric_name, values in metrics.items():
                if values:
                    analysis[metric_name] = {
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "recent": values[-10:] if len(values) > 10 else values,
                    }

            return {
                "analysis_time": datetime.now().isoformat(),
                "time_range_hours": hours,
                "metrics": analysis,
            }

        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取错误摘要

        Args:
            hours: 分析时间范围（小时）

        Returns:
            Dict[str, Any]: 错误摘要
        """
        try:
            error_log = self.log_dir / "errors.log"
            if not error_log.exists():
                return {"error": "错误日志文件不存在"}

            error_count = 0
            error_types = {}

            with open(error_log, "r", encoding="utf-8") as f:
                for line in f:
                    if "ERROR" in line:
                        error_count += 1
                        # 简单的错误类型提取
                        if "Exception" in line:
                            exception_type = "Exception"
                            for word in line.split():
                                if "Exception" in word or "Error" in word:
                                    exception_type = word
                                    break
                            error_types[exception_type] = (
                                error_types.get(exception_type, 0) + 1
                            )

            return {
                "analysis_time": datetime.now().isoformat(),
                "time_range_hours": hours,
                "total_errors": error_count,
                "error_types": error_types,
            }

        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}


# 全局实例
_structured_logger: Optional[StructuredLogger] = None
_performance_logger: Optional[PerformanceLogger] = None
_log_analyzer: Optional[LogAnalyzer] = None


def get_structured_logger() -> StructuredLogger:
    """获取全局结构化日志记录器实例（单例模式）"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger()
    return _structured_logger


def get_performance_logger() -> PerformanceLogger:
    """获取全局性能日志记录器实例（单例模式）"""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger(get_structured_logger())
    return _performance_logger


def get_log_analyzer() -> LogAnalyzer:
    """获取全局日志分析器实例（单例模式）"""
    global _log_analyzer
    if _log_analyzer is None:
        _log_analyzer = LogAnalyzer()
    return _log_analyzer


# 便捷函数
def log_agent_op(
    agent_name: str,
    operation: str,
    status: str,
    duration: Optional[float] = None,
    **kwargs,
) -> None:
    """记录智能体操作的便捷函数"""
    logger_instance = get_structured_logger()
    logger_instance.log_agent_operation(
        agent_name, operation, status, duration, **kwargs
    )


def log_perf(
    metric_name: str, value: Union[int, float], unit: str = "", **tags
) -> None:
    """记录性能指标的便捷函数"""
    logger_instance = get_structured_logger()
    logger_instance.log_performance(metric_name, value, unit, tags)


# 导出接口
__all__ = [
    "StructuredLogger",
    "PerformanceLogger",
    "LogAnalyzer",
    "get_structured_logger",
    "get_performance_logger",
    "get_log_analyzer",
    "log_agent_op",
    "log_perf",
]
