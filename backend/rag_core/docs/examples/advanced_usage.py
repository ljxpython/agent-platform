"""
RAG知识库系统高级使用示例

本文件展示了RAG系统的高级功能，包括：
- 多Collection查询
- 业务类型查询
- 自定义配置
- 性能优化
- 并发处理
"""

import asyncio
from typing import Any, Dict, List

from backend.conf.rag_config import CollectionConfig, RAGConfig
from backend.rag_core.rag_system import RAGSystem


async def multi_collection_query_example():
    """多Collection查询示例"""
    print("🔍 多Collection查询示例")

    async with RAGSystem() as rag:
        # 设置多个Collection
        collections = ["general", "testcase", "ui_testing"]

        for collection_name in collections:
            await rag.setup_collection(collection_name)

        # 为不同Collection添加专业知识
        knowledge_data = {
            "general": [
                "软件开发是创建和维护应用程序、框架或其他软件组件的过程。",
                "敏捷开发是一种迭代的软件开发方法，强调快速交付和持续改进。",
            ],
            "testcase": [
                "测试用例是为了验证软件功能是否符合预期而设计的具体测试步骤。",
                "边界值测试是一种黑盒测试技术，专注于测试输入域的边界条件。",
                "等价类划分是将输入数据分为若干等价类，每类数据的测试效果相同。",
            ],
            "ui_testing": [
                "UI自动化测试使用工具和脚本来自动执行用户界面测试。",
                "Selenium是最流行的Web UI自动化测试框架之一。",
                "页面对象模式是UI测试中常用的设计模式，提高代码的可维护性。",
            ],
        }

        # 添加知识到各个Collection
        for collection_name, documents in knowledge_data.items():
            count = await rag.add_documents(documents, collection_name)
            print(
                f"✅ 向 {collection_name} 添加了 {len(documents)} 个文档，生成 {count} 个节点"
            )

        # 执行多Collection查询
        question = "如何进行软件测试？"
        results = await rag.query_multiple_collections(question, collections)

        print(f"\n❓ 问题: {question}")
        print("💡 多Collection查询结果:")

        for result in results:
            print(f"\n📚 Collection: {result.collection_name}")
            print(f"   回答: {result.answer}")
            print(f"   来源: {result.source_count} 个文档")
            print(f"   置信度: {result.confidence_score:.3f}")

    print()


async def business_type_query_example():
    """业务类型查询示例"""
    print("🏢 业务类型查询示例")

    async with RAGSystem() as rag:
        # 设置不同业务类型的Collection
        collections_config = {
            "general_knowledge": "general",
            "test_automation": "testcase",
            "ui_test_framework": "ui_testing",
            "ai_conversation": "ai_chat",
        }

        for collection_name in collections_config.keys():
            await rag.setup_collection(collection_name)

        # 为不同业务类型添加专业知识
        business_knowledge = {
            "general_knowledge": [
                "项目管理是规划、组织和管理资源以成功完成特定项目目标的过程。"
            ],
            "test_automation": [
                "自动化测试框架提供了执行测试、报告结果和维护测试代码的结构。",
                "持续集成中的自动化测试确保代码变更不会破坏现有功能。",
            ],
            "ui_test_framework": [
                "Playwright是一个现代的端到端测试框架，支持多种浏览器。",
                "Cypress是一个前端测试工具，专为现代Web应用程序设计。",
            ],
            "ai_conversation": [
                "对话系统需要理解用户意图并生成合适的响应。",
                "上下文管理是构建智能对话系统的关键技术。",
            ],
        }

        # 添加业务知识
        for collection_name, documents in business_knowledge.items():
            await rag.add_documents(documents, collection_name)
            print(f"✅ 向 {collection_name} 添加了 {len(documents)} 个文档")

        # 按业务类型查询
        business_queries = {
            "testcase": "如何设计自动化测试？",
            "ui_testing": "推荐的UI测试工具有哪些？",
            "ai_chat": "如何构建对话系统？",
        }

        for business_type, question in business_queries.items():
            print(f"\n🔍 业务类型查询: {business_type}")
            print(f"❓ 问题: {question}")

            results = await rag.query_business_type(question, business_type)

            for result in results:
                print(f"📚 Collection: {result.collection_name}")
                print(f"💡 回答: {result.answer}")
                print(f"📊 来源: {result.source_count} 个文档")

    print()


async def custom_configuration_example():
    """自定义配置示例"""
    print("⚙️ 自定义配置示例")

    # 创建自定义配置
    custom_config = RAGConfig.from_settings()

    # 可以修改配置参数
    print(f"📋 当前Milvus配置: {custom_config.milvus.host}:{custom_config.milvus.port}")
    print(f"📋 当前Ollama模型: {custom_config.ollama.model}")
    print(f"📋 当前DeepSeek模型: {custom_config.deepseek.model}")

    # 使用自定义配置创建RAG系统
    async with RAGSystem(custom_config) as rag:
        await rag.setup_collection("general")

        # 添加文档
        await rag.add_text("这是使用自定义配置的示例。", "general")

        # 查询
        result = await rag.query("这是什么示例？", "general")
        print(f"💡 查询结果: {result.answer}")

    print()


async def concurrent_operations_example():
    """并发操作示例"""
    print("⚡ 并发操作示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 准备多个文档
        documents = [
            f"这是第{i}个文档，包含关于主题{i}的重要信息。" for i in range(1, 11)
        ]

        # 并发添加文档
        print("📝 开始并发添加文档...")
        start_time = asyncio.get_event_loop().time()

        # 分批并发添加
        batch_size = 3
        tasks = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            task = rag.add_documents(batch, "general")
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        total_nodes = sum(results)

        end_time = asyncio.get_event_loop().time()
        print(f"✅ 并发添加完成，总共生成 {total_nodes} 个节点")
        print(f"⏱️ 耗时: {end_time - start_time:.3f}秒")

        # 并发查询
        questions = ["第1个文档说了什么？", "主题5的内容是什么？", "第10个文档的信息？"]

        print("\n🔍 开始并发查询...")
        start_time = asyncio.get_event_loop().time()

        # 并发执行查询
        query_tasks = [rag.query(question, "general") for question in questions]

        query_results = await asyncio.gather(*query_tasks)

        end_time = asyncio.get_event_loop().time()
        print(f"✅ 并发查询完成")
        print(f"⏱️ 耗时: {end_time - start_time:.3f}秒")

        # 显示查询结果
        for i, (question, result) in enumerate(zip(questions, query_results)):
            print(f"\n❓ 问题{i+1}: {question}")
            print(f"💡 回答: {result.answer}")

    print()


async def performance_optimization_example():
    """性能优化示例"""
    print("🚀 性能优化示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 批量操作 vs 单个操作性能对比
        documents = [f"性能测试文档{i}" for i in range(20)]

        # 方式1: 逐个添加（较慢）
        print("📝 方式1: 逐个添加文档")
        start_time = asyncio.get_event_loop().time()

        individual_count = 0
        for doc in documents[:5]:  # 只测试前5个
            count = await rag.add_text(doc, "general")
            individual_count += count

        individual_time = asyncio.get_event_loop().time() - start_time
        print(f"⏱️ 逐个添加5个文档耗时: {individual_time:.3f}秒")

        # 方式2: 批量添加（较快）
        print("\n📝 方式2: 批量添加文档")
        start_time = asyncio.get_event_loop().time()

        batch_count = await rag.add_documents(documents[5:10], "general")

        batch_time = asyncio.get_event_loop().time() - start_time
        print(f"⏱️ 批量添加5个文档耗时: {batch_time:.3f}秒")

        # 性能对比
        if individual_time > 0:
            speedup = individual_time / batch_time if batch_time > 0 else float("inf")
            print(f"🚀 批量操作速度提升: {speedup:.2f}倍")

        # 查询性能优化示例
        print("\n🔍 查询性能优化")

        # 不同top_k值的性能对比
        question = "性能测试相关的内容"

        for top_k in [3, 5, 10]:
            start_time = asyncio.get_event_loop().time()
            result = await rag.query(question, "general", top_k=top_k)
            query_time = asyncio.get_event_loop().time() - start_time

            print(
                f"🔍 top_k={top_k}: 查询耗时 {query_time:.3f}秒, "
                f"检索到 {result.source_count} 个文档"
            )

    print()


async def advanced_metadata_example():
    """高级元数据使用示例"""
    print("🏷️ 高级元数据使用示例")

    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 添加带有丰富元数据的文档
        documents_with_metadata = [
            {
                "text": "Python是一种解释型、面向对象的编程语言。",
                "metadata": {
                    "category": "编程语言",
                    "difficulty": "初级",
                    "tags": ["Python", "编程", "入门"],
                    "author": "技术文档团队",
                    "version": "1.0",
                    "last_updated": "2024-01-01",
                },
            },
            {
                "text": "Django是一个高级Python Web框架，鼓励快速开发和干净、实用的设计。",
                "metadata": {
                    "category": "Web框架",
                    "difficulty": "中级",
                    "tags": ["Django", "Python", "Web开发"],
                    "author": "框架文档团队",
                    "version": "2.0",
                    "last_updated": "2024-01-15",
                },
            },
            {
                "text": "机器学习是人工智能的一个分支，专注于开发能够从数据中学习的算法。",
                "metadata": {
                    "category": "人工智能",
                    "difficulty": "高级",
                    "tags": ["机器学习", "AI", "算法"],
                    "author": "AI研究团队",
                    "version": "3.0",
                    "last_updated": "2024-02-01",
                },
            },
        ]

        # 添加文档
        for doc_info in documents_with_metadata:
            count = await rag.add_text(
                doc_info["text"], "general", metadata=doc_info["metadata"]
            )
            print(
                f"✅ 添加文档: {doc_info['metadata']['category']} - "
                f"难度: {doc_info['metadata']['difficulty']}"
            )

        # 查询并分析元数据
        questions = ["什么是Python？", "Django有什么特点？", "机器学习的定义？"]

        for question in questions:
            result = await rag.query(question, "general")
            print(f"\n❓ 问题: {question}")
            print(f"💡 回答: {result.answer}")

            # 分析检索到的文档元数据
            if result.retrieved_nodes:
                print("📋 相关文档元数据:")
                for i, node in enumerate(result.retrieved_nodes[:2]):  # 只显示前2个
                    if hasattr(node, "metadata") and node.metadata:
                        print(
                            f"   文档{i+1}: {node.metadata.get('category', 'N/A')} "
                            f"(难度: {node.metadata.get('difficulty', 'N/A')})"
                        )

    print()


async def error_recovery_example():
    """错误恢复示例"""
    print("🛡️ 错误恢复示例")

    async with RAGSystem() as rag:
        # 模拟各种错误情况和恢复策略

        # 1. Collection不存在的恢复
        try:
            result = await rag.query("测试问题", "不存在的Collection")
        except Exception as e:
            print(f"❌ Collection不存在错误: {e}")
            print("🔧 自动创建Collection...")
            await rag.setup_collection("不存在的Collection")
            await rag.add_text("这是自动创建的Collection中的文档", "不存在的Collection")
            result = await rag.query("测试问题", "不存在的Collection")
            print(f"✅ 恢复成功，查询结果: {result.answer}")

        # 2. 空查询的处理
        try:
            result = await rag.query("", "general")
        except Exception as e:
            print(f"\n❌ 空查询错误: {e}")
            print("🔧 使用默认查询...")
            result = await rag.query("请介绍一下系统功能", "general")
            print(f"✅ 使用默认查询成功: {result.answer}")

        # 3. 重试机制示例
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 模拟可能失败的操作
                await rag.setup_collection("general")
                result = await rag.query("系统状态如何？", "general")
                print(f"✅ 第{attempt + 1}次尝试成功")
                break
            except Exception as e:
                print(f"❌ 第{attempt + 1}次尝试失败: {e}")
                if attempt == max_retries - 1:
                    print("💥 所有重试都失败了")
                else:
                    print("🔄 准备重试...")
                    await asyncio.sleep(1)  # 等待1秒后重试

    print()


async def main():
    """主函数 - 运行所有高级示例"""
    print("🎯 RAG知识库系统高级使用示例")
    print("=" * 50)

    examples = [
        multi_collection_query_example,
        business_type_query_example,
        custom_configuration_example,
        concurrent_operations_example,
        performance_optimization_example,
        advanced_metadata_example,
        error_recovery_example,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ 示例 {example.__name__} 执行失败: {e}")

        print("-" * 30)

    print("🎉 所有高级示例执行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
