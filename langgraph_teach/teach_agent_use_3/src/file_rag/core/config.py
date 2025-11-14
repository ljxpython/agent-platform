import logging
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, field_validator, validator
from pydantic_settings import BaseSettings

load_dotenv()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")

    # CORS设置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # LLM配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")

    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))

    # 文档处理配置
    SUPPORTED_FILE_TYPES: List[str] = [".pdf", ".txt", ".md", ".docx", ".doc"]
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    # PDF 多模态处理配置
    ENABLE_PDF_MULTIMODAL: bool = (
        os.getenv("ENABLE_PDF_MULTIMODAL", "false").lower() == "true"
    )
    PDF_EXTRACT_IMAGES: bool = (
        os.getenv("PDF_EXTRACT_IMAGES", "false").lower() == "true"
    )
    PDF_IMAGES_INNER_FORMAT: str = os.getenv("PDF_IMAGES_INNER_FORMAT", "markdown-img")

    # 图片解析 LLM 配置
    IMAGE_PARSER_API_BASE: str = os.getenv(
        "IMAGE_PARSER_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"
    )
    IMAGE_PARSER_API_KEY: str = os.getenv(
        "IMAGE_PARSER_API_KEY", "fb15035a-4d78-4f40-b139-a07743ce84a3"
    )
    IMAGE_PARSER_MODEL: str = os.getenv(
        "IMAGE_PARSER_MODEL", "doubao-seed-1-6-vision-250815"
    )
    IMAGE_PARSER_MAX_TOKENS: int = int(os.getenv("IMAGE_PARSER_MAX_TOKENS", "8192"))

    # 图片解析提示词
    IMAGE_PARSER_PROMPT: str = os.getenv(
        "IMAGE_PARSER_PROMPT",
        """
你是一个负责为图像检索生成摘要的助手。
1. 这些摘要将被嵌入并用于检索原始图像。
为图像提供一个多角度详细且适合检索的摘要。
2. 提取图像中的所有文本。
不要遗漏页面上的任何内容。
答案使用 Markdown 格式，无需解释性文字
开头无需使用 Markdown 分隔符 ```。
""",
    ).strip()

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "agentic_rag.log")
    ENABLE_DETAILED_LOGGING: bool = (
        os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # 允许额外的环境变量

    def validate_configuration(self) -> List[str]:
        """
        验证配置的有效性

        Returns:
            配置问题列表，空列表表示配置正常
        """
        issues = []

        # 检查必需的API密钥
        if not self.LLM_API_KEY:
            issues.append("DEEPSEEK_API_KEY is required for DeepSeek models")

        if not self.IMAGE_PARSER_API_KEY:
            issues.append("IMAGE_PARSER_API_KEY is required for image processing")

        return issues

    def get_safe_config(self) -> Dict[str, Any]:
        """
        获取安全的配置信息（隐藏敏感信息）

        Returns:
            安全的配置字典
        """
        config = self.dict()

        # 隐藏敏感信息
        sensitive_keys = ["DEEPSEEK_API_KEY", "IMAGE_PARSER_API_KEY", "SECRET_KEY"]

        for key in sensitive_keys:
            if key in config and config[key]:
                config[key] = (
                    "***" + config[key][-4:] if len(config[key]) > 4 else "***"
                )

        return config


def create_settings() -> Settings:
    """创建并验证设置"""
    settings = Settings()

    # 验证配置
    issues = settings.validate_configuration()
    if issues:
        logger.warning("Configuration issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")

    return settings


# 该代码会自动执行，并且只会执行一次（单例设计模式）
settings = create_settings()
