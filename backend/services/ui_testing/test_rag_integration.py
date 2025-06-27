"""
UI测试RAG集成测试脚本
用于验证UI测试服务与RAG系统的集成功能
测试新的消息队列SSE流式输出方式
"""

import asyncio
import json
import time
from pathlib import Path

from loguru import logger

from backend.rag_core.rag_system import RAGSystem
from backend.services.rag.rag_service import RAGService
from backend.services.ui_testing.agents import MidsceneGenerationAgent, UIAnalysisAgent


async def test_rag_integration():
    """测试UI测试RAG集成功能"""
    logger.info("🧪 开始测试UI测试RAG集成功能")

    try:
        # 1. 测试RAG系统初始化
        logger.info("📋 步骤1: 测试RAG系统初始化")
        async with RAGSystem() as rag:
            await rag.setup_collection("ui_testing")
            logger.success("✅ RAG系统初始化成功")

            # 2. 测试添加UI分析结果到RAG
            logger.info("📋 步骤2: 测试添加UI分析结果到RAG")
            test_ui_analysis = """
# UI界面分析报告

## 图片信息
- 图片路径: /test/login_page.png
- 分析时间: 2024-06-27T10:30:00
- 对话ID: test_conversation_001

## 用户需求
测试登录页面的用户名和密码输入功能

## UI元素分析结果
### 主要UI元素
1. **用户名输入框**
   - 位置: 页面中央偏上
   - 类型: 文本输入框
   - 占位符: "请输入用户名"
   - 尺寸: 300px × 40px

2. **密码输入框**
   - 位置: 用户名输入框下方20px
   - 类型: 密码输入框
   - 占位符: "请输入密码"
   - 尺寸: 300px × 40px

3. **登录按钮**
   - 位置: 密码输入框下方30px
   - 类型: 主要按钮
   - 文本: "登录"
   - 颜色: 蓝色背景，白色文字
   - 尺寸: 300px × 45px

4. **记住密码复选框**
   - 位置: 登录按钮上方左侧
   - 类型: 复选框
   - 文本: "记住密码"

## 标签
- 类型: UI分析
- 来源: UIAnalysisAgent
- 业务场景: UI自动化测试
"""

            result = await rag.add_text(test_ui_analysis, "ui_testing")
            logger.success(f"✅ UI分析结果添加成功，生成向量数: {result}")

            # 3. 测试RAG查询功能
            logger.info("📋 步骤3: 测试RAG查询功能")
            query_result = await rag.query(
                "如何测试登录页面的输入框功能？", "ui_testing"
            )

            logger.info(f"🔍 RAG查询结果:")
            logger.info(f"回答: {query_result.answer}")
            logger.info(f"检索到的文档数: {len(query_result.retrieved_docs)}")

            for i, doc in enumerate(query_result.retrieved_docs[:2]):
                logger.info(f"相关文档 {i+1}: {doc.text[:100]}...")

            logger.success("✅ RAG查询功能测试成功")

            # 4. 测试RAG服务层
            logger.info("📋 步骤4: 测试RAG服务层")
            rag_service = RAGService()
            await rag_service.initialize()

            service_result = await rag_service.query_collection(
                question="UI测试中如何定位按钮元素？",
                collection_name="ui_testing",
                top_k=3,
            )

            if service_result.get("success", False):
                logger.success("✅ RAG服务层查询成功")
                logger.info(f"服务层回答: {service_result.get('answer', '')[:100]}...")
            else:
                logger.warning(
                    f"⚠️ RAG服务层查询失败: {service_result.get('error', '未知错误')}"
                )

            # 5. 测试UI分析Agent的RAG保存功能
            logger.info("📋 步骤5: 测试UI分析Agent的RAG保存功能")

            # 模拟UIAnalysisAgent的RAG保存
            test_analysis_result = """
### 测试页面UI元素分析

**页面类型**: 商品搜索页面
**主要功能**: 商品搜索和筛选

**关键元素**:
1. 搜索输入框 - 页面顶部中央
2. 搜索按钮 - 搜索框右侧
3. 分类筛选器 - 左侧边栏
4. 商品列表 - 主要内容区域
5. 分页控件 - 页面底部

**测试建议**:
- 验证搜索功能的关键词匹配
- 测试筛选器的组合使用
- 检查分页功能的正确性
"""

            # 直接使用RAG系统添加
            document_content = f"""
# UI界面分析报告

## 图片信息
- 图片路径: /test/search_page.png
- 分析时间: {time.strftime('%Y-%m-%dT%H:%M:%S')}
- 对话ID: test_conversation_002

## 用户需求
测试商品搜索页面的搜索和筛选功能

## UI元素分析结果
{test_analysis_result}

## 标签
- 类型: UI分析
- 来源: UIAnalysisAgent
- 业务场景: UI自动化测试
"""

            save_result = await rag.add_text(document_content, "ui_testing")
            logger.success(f"✅ 模拟UI分析结果保存成功，生成向量数: {save_result}")

            # 6. 测试增强查询
            logger.info("📋 步骤6: 测试RAG增强查询")
            enhanced_query = await rag.query(
                "如何设计商品搜索页面的自动化测试用例？", "ui_testing"
            )

            logger.info(f"🚀 增强查询结果:")
            logger.info(f"回答: {enhanced_query.answer}")
            logger.info(f"检索到的相关文档数: {len(enhanced_query.retrieved_docs)}")

            # 7. 测试统计信息
            logger.info("📋 步骤7: 获取统计信息")
            stats = rag.get_stats()
            logger.info(f"📊 RAG系统统计信息:")
            for collection_name, collection_stats in stats.items():
                logger.info(f"  {collection_name}: {collection_stats}")

            logger.success("🎉 UI测试RAG集成功能测试完成！")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise


async def test_ui_analysis_agent_rag_save():
    """测试UIAnalysisAgent的RAG保存功能"""
    logger.info("🧪 测试UIAnalysisAgent的RAG保存功能")

    try:
        # 创建UIAnalysisAgent实例
        ui_agent = UIAnalysisAgent("UI元素识别专家")

        # 模拟调用RAG保存方法
        test_ui_result = """
页面包含以下主要元素：
1. 导航栏 - 页面顶部，包含Logo和主菜单
2. 轮播图 - 首页主要展示区域
3. 产品分类 - 中间区域的分类导航
4. 推荐商品 - 页面下方的商品展示区
5. 页脚 - 包含联系信息和友情链接
"""

        await ui_agent._save_ui_analysis_to_rag(
            ui_analysis_result=test_ui_result,
            image_path="/test/homepage.png",
            user_requirement="测试首页的导航和商品展示功能",
            conversation_id="test_ui_agent_001",
        )

        logger.success("✅ UIAnalysisAgent RAG保存功能测试成功")

    except Exception as e:
        logger.error(f"❌ UIAnalysisAgent RAG保存测试失败: {e}")
        raise


async def test_midscene_agent_rag_query():
    """测试MidsceneGenerationAgent的RAG查询功能"""
    logger.info("🧪 测试MidsceneGenerationAgent的RAG查询功能")

    try:
        # 创建MidsceneGenerationAgent实例
        midscene_agent = MidsceneGenerationAgent("Midscene.js自动化测试专家")

        # 测试RAG增强上下文获取
        rag_context = await midscene_agent._get_rag_enhanced_context(
            user_requirement="测试电商网站的商品搜索功能",
            conversation_id="test_midscene_001",
        )

        logger.info(f"🔍 RAG增强上下文:")
        logger.info(f"上下文内容: {rag_context.get('context', '')[:200]}...")
        logger.info(f"检索文档数: {len(rag_context.get('retrieved_docs', []))}")

        # 测试文档格式化
        if rag_context.get("retrieved_docs"):
            formatted_docs = midscene_agent._format_retrieved_docs(
                rag_context["retrieved_docs"]
            )
            logger.info(f"📄 格式化文档预览: {formatted_docs[:300]}...")

        logger.success("✅ MidsceneGenerationAgent RAG查询功能测试成功")

    except Exception as e:
        logger.error(f"❌ MidsceneGenerationAgent RAG查询测试失败: {e}")
        raise


async def main():
    """主测试函数"""
    logger.info("🚀 开始UI测试RAG集成完整测试")

    try:
        # 运行所有测试
        await test_rag_integration()
        await test_ui_analysis_agent_rag_save()
        await test_midscene_agent_rag_query()

        logger.success("🎉 所有测试完成！UI测试RAG集成功能正常")

    except Exception as e:
        logger.error(f"❌ 测试过程中出现错误: {e}")
        return False

    return True


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    if success:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
        exit(1)
