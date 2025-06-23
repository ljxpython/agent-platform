"""
AI智能体调试工具系统
提供智能体运行时的调试、跟踪和诊断功能
"""

import asyncio
import json
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from loguru import logger


class TraceLevel(Enum):
    """跟踪级别"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TraceEvent:
    """跟踪事件"""

    timestamp: str
    level: TraceLevel
    agent_name: str
    operation: str
    event_type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    conversation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "agent_name": self.agent_name,
            "operation": self.operation,
            "event_type": self.event_type,
            "message": self.message,
            "data": self.data,
            "stack_trace": self.stack_trace,
            "conversation_id": self.conversation_id,
        }


@dataclass
class MessageTrace:
    """消息跟踪"""

    message_id: str
    timestamp: str
    source_agent: str
    target_agent: Optional[str]
    message_type: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type,
            "content": str(self.content)[:500],  # 限制内容长度
            "metadata": self.metadata,
        }


class AgentDebugger:
    """智能体调试器"""

    def __init__(self, max_traces: int = 1000, max_messages: int = 500):
        """
        初始化调试器

        Args:
            max_traces: 最大跟踪事件数量
            max_messages: 最大消息跟踪数量
        """
        self.max_traces = max_traces
        self.max_messages = max_messages
        self.debug_enabled = False
        self.trace_level = TraceLevel.INFO

        # 跟踪数据存储
        self.traces: deque = deque(maxlen=max_traces)
        self.message_traces: deque = deque(maxlen=max_messages)
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.conversation_traces: Dict[str, List[TraceEvent]] = defaultdict(list)

        # 性能计数器
        self.counters: Dict[str, int] = defaultdict(int)

        logger.info(
            f"🐛 [智能体调试器] 初始化完成 | 最大跟踪: {max_traces} | 最大消息: {max_messages}"
        )

    def enable_debug(self, level: TraceLevel = TraceLevel.INFO) -> None:
        """启用调试模式"""
        self.debug_enabled = True
        self.trace_level = level
        logger.info(f"🔍 [智能体调试器] 调试模式已启用 | 级别: {level.value}")

    def disable_debug(self) -> None:
        """禁用调试模式"""
        self.debug_enabled = False
        logger.info("🔍 [智能体调试器] 调试模式已禁用")

    def trace_event(
        self,
        agent_name: str,
        operation: str,
        event_type: str,
        message: str,
        level: TraceLevel = TraceLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        """
        记录跟踪事件

        Args:
            agent_name: 智能体名称
            operation: 操作名称
            event_type: 事件类型
            message: 事件消息
            level: 跟踪级别
            data: 附加数据
            conversation_id: 对话ID
        """
        if not self.debug_enabled:
            return

        # 检查级别过滤
        level_order = {
            TraceLevel.DEBUG: 0,
            TraceLevel.INFO: 1,
            TraceLevel.WARNING: 2,
            TraceLevel.ERROR: 3,
        }
        if level_order[level] < level_order[self.trace_level]:
            return

        # 创建跟踪事件
        trace_event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            level=level,
            agent_name=agent_name,
            operation=operation,
            event_type=event_type,
            message=message,
            data=data or {},
            conversation_id=conversation_id,
        )

        # 如果是错误级别，添加堆栈跟踪
        if level == TraceLevel.ERROR:
            trace_event.stack_trace = traceback.format_exc()

        # 存储跟踪事件
        self.traces.append(trace_event)

        # 按对话ID分组存储
        if conversation_id:
            self.conversation_traces[conversation_id].append(trace_event)

        # 更新计数器
        self.counters[f"{agent_name}:{event_type}"] += 1
        self.counters[f"total:{level.value}"] += 1

        # 输出调试日志
        if level == TraceLevel.ERROR:
            logger.error(
                f"🐛 [调试跟踪] {agent_name}.{operation} | {event_type}: {message}"
            )
        elif level == TraceLevel.WARNING:
            logger.warning(
                f"🐛 [调试跟踪] {agent_name}.{operation} | {event_type}: {message}"
            )
        else:
            logger.debug(
                f"🐛 [调试跟踪] {agent_name}.{operation} | {event_type}: {message}"
            )

    def trace_message(
        self,
        message_id: str,
        source_agent: str,
        target_agent: Optional[str],
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        跟踪消息流

        Args:
            message_id: 消息ID
            source_agent: 源智能体
            target_agent: 目标智能体
            message_type: 消息类型
            content: 消息内容
            metadata: 元数据
        """
        if not self.debug_enabled:
            return

        message_trace = MessageTrace(
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            target_agent=target_agent,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
        )

        self.message_traces.append(message_trace)

        # 更新计数器
        self.counters[f"message:{message_type}"] += 1
        self.counters["total:messages"] += 1

        logger.debug(
            f"📨 [消息跟踪] {source_agent} -> {target_agent or 'broadcast'} | {message_type}"
        )

    def update_agent_state(self, agent_name: str, state: Dict[str, Any]) -> None:
        """
        更新智能体状态

        Args:
            agent_name: 智能体名称
            state: 状态数据
        """
        if not self.debug_enabled:
            return

        self.agent_states[agent_name] = {
            **state,
            "last_updated": datetime.now().isoformat(),
        }

        logger.debug(f"🔄 [状态更新] {agent_name} | 状态字段: {list(state.keys())}")

    def get_traces(
        self,
        agent_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        level: Optional[TraceLevel] = None,
        limit: int = 100,
    ) -> List[TraceEvent]:
        """
        获取跟踪事件

        Args:
            agent_name: 智能体名称过滤
            conversation_id: 对话ID过滤
            level: 级别过滤
            limit: 返回数量限制

        Returns:
            List[TraceEvent]: 跟踪事件列表
        """
        if conversation_id and conversation_id in self.conversation_traces:
            traces = self.conversation_traces[conversation_id]
        else:
            traces = list(self.traces)

        # 应用过滤器
        filtered_traces = []
        for trace in reversed(traces):
            if agent_name and trace.agent_name != agent_name:
                continue
            if level and trace.level != level:
                continue

            filtered_traces.append(trace)

            if len(filtered_traces) >= limit:
                break

        return filtered_traces

    def get_message_traces(
        self,
        source_agent: Optional[str] = None,
        target_agent: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MessageTrace]:
        """
        获取消息跟踪

        Args:
            source_agent: 源智能体过滤
            target_agent: 目标智能体过滤
            message_type: 消息类型过滤
            limit: 返回数量限制

        Returns:
            List[MessageTrace]: 消息跟踪列表
        """
        filtered_traces = []

        for trace in reversed(self.message_traces):
            if source_agent and trace.source_agent != source_agent:
                continue
            if target_agent and trace.target_agent != target_agent:
                continue
            if message_type and trace.message_type != message_type:
                continue

            filtered_traces.append(trace)

            if len(filtered_traces) >= limit:
                break

        return filtered_traces

    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        return self.agent_states.get(agent_name)

    def get_all_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体状态"""
        return self.agent_states.copy()

    def get_debug_summary(self) -> Dict[str, Any]:
        """获取调试摘要"""
        return {
            "debug_enabled": self.debug_enabled,
            "trace_level": self.trace_level.value,
            "total_traces": len(self.traces),
            "total_message_traces": len(self.message_traces),
            "active_agents": len(self.agent_states),
            "conversations": len(self.conversation_traces),
            "counters": dict(self.counters),
            "recent_errors": len(
                [t for t in self.traces if t.level == TraceLevel.ERROR]
            ),
        }

    def export_traces(
        self, conversation_id: Optional[str] = None, format: str = "json"
    ) -> str:
        """
        导出跟踪数据

        Args:
            conversation_id: 对话ID过滤
            format: 导出格式 (json)

        Returns:
            str: 导出的数据
        """
        if conversation_id and conversation_id in self.conversation_traces:
            traces = self.conversation_traces[conversation_id]
        else:
            traces = list(self.traces)

        if format == "json":
            export_data = {
                "export_time": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "total_traces": len(traces),
                "traces": [trace.to_dict() for trace in traces],
                "message_traces": [trace.to_dict() for trace in self.message_traces],
                "agent_states": self.agent_states,
                "counters": dict(self.counters),
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)

        return ""

    def clear_traces(self, conversation_id: Optional[str] = None) -> None:
        """
        清除跟踪数据

        Args:
            conversation_id: 对话ID，None表示清除所有
        """
        if conversation_id:
            self.conversation_traces.pop(conversation_id, None)
            logger.info(f"🧹 [智能体调试器] 已清除对话跟踪数据: {conversation_id}")
        else:
            self.traces.clear()
            self.message_traces.clear()
            self.agent_states.clear()
            self.conversation_traces.clear()
            self.counters.clear()
            logger.info("🧹 [智能体调试器] 已清除所有跟踪数据")


# 全局调试器实例
_agent_debugger: Optional[AgentDebugger] = None


def get_agent_debugger() -> AgentDebugger:
    """获取全局智能体调试器实例（单例模式）"""
    global _agent_debugger
    if _agent_debugger is None:
        _agent_debugger = AgentDebugger()
    return _agent_debugger


# 便捷函数
def debug_trace(
    agent_name: str,
    operation: str,
    event_type: str,
    message: str,
    level: TraceLevel = TraceLevel.INFO,
    data: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None,
) -> None:
    """调试跟踪的便捷函数"""
    debugger = get_agent_debugger()
    debugger.trace_event(
        agent_name, operation, event_type, message, level, data, conversation_id
    )


def debug_message(
    message_id: str,
    source_agent: str,
    target_agent: Optional[str],
    message_type: str,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """消息跟踪的便捷函数"""
    debugger = get_agent_debugger()
    debugger.trace_message(
        message_id, source_agent, target_agent, message_type, content, metadata
    )


# 导出接口
__all__ = [
    "TraceLevel",
    "TraceEvent",
    "MessageTrace",
    "AgentDebugger",
    "get_agent_debugger",
    "debug_trace",
    "debug_message",
]
