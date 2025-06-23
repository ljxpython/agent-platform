"""
AI智能体插件系统
提供可扩展的插件架构，支持智能体功能的动态扩展
"""

import asyncio
import importlib
import inspect
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "enabled": self.enabled,
        }


class PluginHook:
    """插件钩子"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化插件钩子

        Args:
            name: 钩子名称
            description: 钩子描述
        """
        self.name = name
        self.description = description
        self.handlers: List[Callable] = []

    def register(self, handler: Callable) -> None:
        """注册钩子处理器"""
        if handler not in self.handlers:
            self.handlers.append(handler)
            logger.debug(f"🔗 [插件钩子] 注册处理器: {self.name} -> {handler.__name__}")

    def unregister(self, handler: Callable) -> None:
        """注销钩子处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.debug(f"🔗 [插件钩子] 注销处理器: {self.name} -> {handler.__name__}")

    async def execute(self, *args, **kwargs) -> List[Any]:
        """执行所有钩子处理器"""
        results = []

        for handler in self.handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(*args, **kwargs)
                else:
                    result = handler(*args, **kwargs)
                results.append(result)

            except Exception as e:
                logger.error(
                    f"❌ [插件钩子] 处理器执行失败: {self.name} -> {handler.__name__} | 错误: {e}"
                )
                results.append(None)

        return results


class BasePlugin(ABC):
    """插件基类"""

    def __init__(self):
        """初始化插件"""
        self.info: Optional[PluginInfo] = None
        self.hooks: Dict[str, Callable] = {}
        self.enabled = True

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理插件资源"""
        pass

    def register_hook(self, hook_name: str, handler: Callable) -> None:
        """注册钩子处理器"""
        self.hooks[hook_name] = handler

    def get_hooks(self) -> Dict[str, Callable]:
        """获取插件的所有钩子"""
        return self.hooks.copy()


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str = "plugins"):
        """
        初始化插件管理器

        Args:
            plugin_dir: 插件目录
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)

        self.plugins: Dict[str, BasePlugin] = {}
        self.hooks: Dict[str, PluginHook] = {}
        self.plugin_dependencies: Dict[str, List[str]] = {}

        # 预定义的钩子
        self._register_builtin_hooks()

        logger.info(f"🔌 [插件管理器] 初始化完成 | 插件目录: {self.plugin_dir}")

    def _register_builtin_hooks(self) -> None:
        """注册内置钩子"""
        builtin_hooks = [
            ("agent_created", "智能体创建后"),
            ("agent_destroyed", "智能体销毁前"),
            ("message_sent", "消息发送后"),
            ("message_received", "消息接收后"),
            ("operation_started", "操作开始前"),
            ("operation_completed", "操作完成后"),
            ("operation_failed", "操作失败后"),
            ("conversation_started", "对话开始"),
            ("conversation_ended", "对话结束"),
            ("error_occurred", "错误发生时"),
        ]

        for hook_name, description in builtin_hooks:
            self.register_hook(hook_name, description)

    def register_hook(self, name: str, description: str = "") -> PluginHook:
        """
        注册钩子

        Args:
            name: 钩子名称
            description: 钩子描述

        Returns:
            PluginHook: 钩子对象
        """
        if name not in self.hooks:
            self.hooks[name] = PluginHook(name, description)
            logger.debug(f"🔗 [插件管理器] 注册钩子: {name}")

        return self.hooks[name]

    def get_hook(self, name: str) -> Optional[PluginHook]:
        """获取钩子"""
        return self.hooks.get(name)

    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        执行钩子

        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[Any]: 钩子处理器的返回值列表
        """
        hook = self.hooks.get(hook_name)
        if hook:
            return await hook.execute(*args, **kwargs)
        return []

    async def load_plugin(
        self, plugin_name: str, plugin_class: Type[BasePlugin]
    ) -> bool:
        """
        加载插件

        Args:
            plugin_name: 插件名称
            plugin_class: 插件类

        Returns:
            bool: 加载是否成功
        """
        try:
            logger.info(f"🔌 [插件管理器] 加载插件: {plugin_name}")

            # 创建插件实例
            plugin = plugin_class()
            plugin.info = plugin.get_info()

            # 检查依赖
            if not await self._check_dependencies(plugin.info.dependencies):
                logger.error(f"❌ [插件管理器] 插件依赖检查失败: {plugin_name}")
                return False

            # 初始化插件
            if not await plugin.initialize():
                logger.error(f"❌ [插件管理器] 插件初始化失败: {plugin_name}")
                return False

            # 注册插件钩子
            for hook_name, handler in plugin.get_hooks().items():
                hook = self.get_hook(hook_name)
                if hook:
                    hook.register(handler)
                else:
                    logger.warning(f"⚠️ [插件管理器] 未知钩子: {hook_name}")

            # 保存插件
            self.plugins[plugin_name] = plugin
            self.plugin_dependencies[plugin_name] = plugin.info.dependencies

            logger.success(f"✅ [插件管理器] 插件加载成功: {plugin_name}")

            # 触发插件加载钩子
            await self.execute_hook("plugin_loaded", plugin_name, plugin.info)

            return True

        except Exception as e:
            logger.error(f"❌ [插件管理器] 插件加载失败: {plugin_name} | 错误: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载是否成功
        """
        try:
            if plugin_name not in self.plugins:
                logger.warning(f"⚠️ [插件管理器] 插件不存在: {plugin_name}")
                return False

            logger.info(f"🔌 [插件管理器] 卸载插件: {plugin_name}")

            plugin = self.plugins[plugin_name]

            # 注销插件钩子
            for hook_name, handler in plugin.get_hooks().items():
                hook = self.get_hook(hook_name)
                if hook:
                    hook.unregister(handler)

            # 清理插件资源
            await plugin.cleanup()

            # 移除插件
            del self.plugins[plugin_name]
            self.plugin_dependencies.pop(plugin_name, None)

            logger.success(f"✅ [插件管理器] 插件卸载成功: {plugin_name}")

            # 触发插件卸载钩子
            await self.execute_hook("plugin_unloaded", plugin_name)

            return True

        except Exception as e:
            logger.error(f"❌ [插件管理器] 插件卸载失败: {plugin_name} | 错误: {e}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 重新加载是否成功
        """
        if plugin_name in self.plugins:
            plugin_class = type(self.plugins[plugin_name])
            await self.unload_plugin(plugin_name)
            return await self.load_plugin(plugin_name, plugin_class)
        return False

    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查插件依赖"""
        for dep in dependencies:
            if dep not in self.plugins:
                logger.error(f"❌ [插件管理器] 缺少依赖插件: {dep}")
                return False

            if not self.plugins[dep].enabled:
                logger.error(f"❌ [插件管理器] 依赖插件未启用: {dep}")
                return False

        return True

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有插件"""
        return self.plugins.copy()

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        plugin = self.plugins.get(plugin_name)
        return plugin.info if plugin else None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件信息"""
        return [plugin.info.to_dict() for plugin in self.plugins.values()]

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enabled = True
            logger.info(f"✅ [插件管理器] 插件已启用: {plugin_name}")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enabled = False
            logger.info(f"⏸️ [插件管理器] 插件已禁用: {plugin_name}")
            return True
        return False

    async def discover_plugins(self) -> List[str]:
        """发现插件目录中的插件"""
        discovered = []

        try:
            for plugin_file in self.plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue

                plugin_name = plugin_file.stem
                discovered.append(plugin_name)
                logger.debug(f"🔍 [插件管理器] 发现插件文件: {plugin_name}")

            logger.info(f"🔍 [插件管理器] 发现 {len(discovered)} 个插件文件")

        except Exception as e:
            logger.error(f"❌ [插件管理器] 插件发现失败: {e}")

        return discovered

    async def cleanup_all(self) -> None:
        """清理所有插件"""
        logger.info("🧹 [插件管理器] 开始清理所有插件")

        for plugin_name in list(self.plugins.keys()):
            await self.unload_plugin(plugin_name)

        logger.success("✅ [插件管理器] 所有插件清理完成")


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例（单例模式）"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# 便捷装饰器
def plugin_hook(hook_name: str):
    """
    插件钩子装饰器

    Args:
        hook_name: 钩子名称
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 执行原函数
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

            # 执行钩子
            plugin_manager = get_plugin_manager()
            await plugin_manager.execute_hook(hook_name, *args, **kwargs)

            return result

        return wrapper

    return decorator


# 导出接口
__all__ = [
    "PluginInfo",
    "PluginHook",
    "BasePlugin",
    "PluginManager",
    "get_plugin_manager",
    "plugin_hook",
]
