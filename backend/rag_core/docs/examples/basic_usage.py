"""
RAG知识库系统基础使用示例

本文件展示了RAG系统的基本使用方法，包括：
- 系统初始化
- 文档添加
- 知识检索
- 资源管理
"""

import asyncio
from typing import List

from backend.rag_core.rag_system import RAGSystem


async def basic_initialization_example():
    """基础初始化示例"""
    print("🚀 基础初始化示例")

    # 方式1: 使用上下文管理器（推荐）
    async with RAGSystem() as rag:
        print("✅ RAG系统初始化成功")

        # 设置Collection
        await rag.setup_collection("general")
        print("✅ Collection设置完成")

    print("✅ 资源自动清理完成\n")


async def add_text_example():
    """添加文本示例"""
    print("📝 添加文本示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 添加单个文本
        text = "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
        count = await rag.add_text(text, "general")
        print(f"✅ 添加文本成功，生成 {count} 个节点")

        # 添加带元数据的文本
        metadata = {"source": "AI教程", "chapter": "第1章", "author": "张三"}
        count = await rag.add_text(
            "机器学习是人工智能的一个子领域，专注于开发能够从数据中学习的算法。",
            "general",
            metadata=metadata,
        )
        print(f"✅ 添加带元数据的文本成功，生成 {count} 个节点")

    print()


async def add_file_example():
    """添加文件示例"""
    print("📄 添加文件示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 创建示例文件
        sample_file = "sample_document.txt"
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write(
                """
深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。

深度学习的主要特点：
1. 多层神经网络结构
2. 自动特征提取
3. 端到端学习
4. 大数据驱动

深度学习在以下领域有广泛应用：
- 计算机视觉
- 自然语言处理
- 语音识别
- 推荐系统
            """
            )

        try:
            # 添加文件
            count = await rag.add_file(sample_file, "general")
            print(f"✅ 添加文件成功，生成 {count} 个节点")
        except FileNotFoundError:
            print("❌ 文件不存在，请确保文件路径正确")
        finally:
            # 清理示例文件
            import os

            if os.path.exists(sample_file):
                os.remove(sample_file)

    print()


async def batch_add_documents_example():
    """批量添加文档示例"""
    print("📚 批量添加文档示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 准备多个文档
        documents = [
            "自然语言处理（NLP）是人工智能的一个重要分支，专注于让计算机理解和生成人类语言。",
            "计算机视觉是使计算机能够从图像或视频中获取有意义信息的技术领域。",
            "强化学习是机器学习的一个领域，智能体通过与环境交互来学习最优行为策略。",
            "神经网络是受生物神经系统启发的计算模型，由相互连接的节点（神经元）组成。",
        ]

        # 批量添加
        total_count = await rag.add_documents(documents, "general")
        print(f"✅ 批量添加 {len(documents)} 个文档成功，总共生成 {total_count} 个节点")

    print()


async def basic_query_example():
    """基础查询示例"""
    print("🔍 基础查询示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 先添加一些知识
        knowledge_base = [
            "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。",
            "Django是一个基于Python的Web框架，遵循MVC架构模式。",
            "FastAPI是一个现代、快速的Python Web框架，用于构建API。",
            "机器学习是人工智能的一个分支，让计算机能够从数据中学习。",
        ]

        await rag.add_documents(knowledge_base, "general")
        print("✅ 知识库初始化完成")

        # 执行查询
        questions = [
            "什么是Python？",
            "Django有什么特点？",
            "如何构建API？",
            "机器学习的定义是什么？",
        ]

        for question in questions:
            result = await rag.query(question, "general")
            print(f"\n❓ 问题: {question}")
            print(f"💡 回答: {result.answer}")
            print(f"📊 来源: {result.source_count} 个文档")
            print(f"⏱️ 耗时: {result.query_time:.3f}秒")
            print(f"🎯 置信度: {result.confidence_score:.3f}")

    print()


async def query_with_parameters_example():
    """带参数的查询示例"""
    print("⚙️ 带参数的查询示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 添加知识
        documents = [
            "React是一个用于构建用户界面的JavaScript库。",
            "Vue.js是一个渐进式JavaScript框架。",
            "Angular是一个基于TypeScript的Web应用框架。",
            "Node.js是一个基于Chrome V8引擎的JavaScript运行时。",
            "Express.js是一个简洁而灵活的Node.js Web应用框架。",
        ]

        await rag.add_documents(documents, "general")

        question = "前端框架有哪些？"

        # 不同top_k值的查询对比
        for top_k in [2, 3, 5]:
            result = await rag.query(question, "general", top_k=top_k)
            print(f"\n🔍 查询 (top_k={top_k}): {question}")
            print(f"💡 回答: {result.answer}")
            print(f"📊 检索到 {result.source_count} 个相关文档")

    print()


async def collection_info_example():
    """Collection信息查询示例"""
    print("ℹ️ Collection信息查询示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 添加一些文档
        documents = ["文档1内容", "文档2内容", "文档3内容"]
        await rag.add_documents(documents, "general")

        # 获取Collection信息
        info = await rag.get_collection_info("general")
        print("📋 Collection信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        # 列出所有Collection
        collections = await rag.list_collections()
        print(f"\n📚 可用的Collections: {collections}")

        # 获取系统统计
        stats = await rag.get_system_stats()
        print("\n📊 系统统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    print()


async def error_handling_example():
    """错误处理示例"""
    print("⚠️ 错误处理示例")

    async with RAGSystem() as rag:
        # 示例1: 查询不存在的Collection
        try:
            result = await rag.query("测试问题", "不存在的Collection")
        except Exception as e:
            print(f"❌ 预期错误 - Collection不存在: {type(e).__name__}: {e}")

        # 示例2: 添加空文本
        try:
            await rag.setup_collection("general")
            count = await rag.add_text("", "general")
        except Exception as e:
            print(f"❌ 预期错误 - 空文本: {type(e).__name__}: {e}")

        # 示例3: 查询空问题
        try:
            result = await rag.query("", "general")
        except Exception as e:
            print(f"❌ 预期错误 - 空问题: {type(e).__name__}: {e}")

    print()


async def manual_resource_management_example():
    """手动资源管理示例"""
    print("🔧 手动资源管理示例")

    # 不使用上下文管理器的情况
    rag = RAGSystem()

    try:
        # 手动初始化
        await rag.initialize()
        print("✅ 手动初始化成功")

        # 设置Collection
        await rag.setup_collection("general")

        # 添加文档
        count = await rag.add_text("这是一个手动管理资源的示例。", "general")
        print(f"✅ 添加文档成功，生成 {count} 个节点")

        # 查询
        result = await rag.query("这是什么示例？", "general")
        print(f"💡 查询结果: {result.answer}")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

    finally:
        # 手动清理资源
        await rag.cleanup()
        print("✅ 手动清理完成")

    print()


async def main():
    """主函数 - 运行所有示例"""
    print("🎯 RAG知识库系统基础使用示例")
    print("=" * 50)

    examples = [
        basic_initialization_example,
        add_text_example,
        add_file_example,
        batch_add_documents_example,
        basic_query_example,
        query_with_parameters_example,
        collection_info_example,
        error_handling_example,
        manual_resource_management_example,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ 示例 {example.__name__} 执行失败: {e}")

        print("-" * 30)

    print("🎉 所有基础示例执行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
