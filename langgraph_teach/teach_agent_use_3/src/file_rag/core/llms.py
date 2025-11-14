import logging

from file_rag.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)


# 创建图片处理模型
def create_image_model():
    from langchain_openai import ChatOpenAI

    """创建图片处理模型"""
    try:
        return ChatOpenAI(
            base_url=settings.IMAGE_PARSER_API_BASE,
            api_key=settings.IMAGE_PARSER_API_KEY,
            model=settings.IMAGE_PARSER_MODEL,
            max_tokens=settings.IMAGE_PARSER_MAX_TOKENS,
        )
    except Exception as e:
        logger.error(f"Failed to create image model: {e}")
        return None


# 创建文本处理模型
def create_text_model():
    """创建文本处理模型"""
    from langchain_deepseek import ChatDeepSeek

    try:
        return ChatDeepSeek(
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
    except ImportError:
        logger.warning("langchain_deepseek not available")
        return None
    except Exception as e:
        logger.error(f"Failed to create text model: {e}")
        return None


image_llm_model = create_image_model()
deepseek_model = create_text_model()
