"""
RAG知识库系统自定义Collection示例

本文件展示了如何创建和管理自定义Collection，包括：
- 自定义Collection配置
- 专业领域知识库
- Collection间的关联
- 动态Collection管理
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.conf.rag_config import CollectionConfig
from backend.rag_core.rag_system import RAGSystem

# ==================== 自定义Collection配置示例 ====================


@dataclass
class CustomCollectionConfig:
    """自定义Collection配置"""

    name: str
    display_name: str
    description: str
    business_type: str
    domain: str  # 专业领域
    language: str = "zh"  # 语言
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    specialized_prompts: Dict[str, str] = None  # 专业提示词

    def __post_init__(self):
        if self.specialized_prompts is None:
            self.specialized_prompts = {}


class CustomCollectionManager:
    """自定义Collection管理器"""

    def __init__(self):
        self.rag_system = None
        self.custom_configs = {}

    async def initialize(self):
        """初始化管理器"""
        self.rag_system = RAGSystem()
        await self.rag_system.initialize()
        print("✅ 自定义Collection管理器初始化完成")

    async def create_specialized_collection(self, config: CustomCollectionConfig):
        """创建专业化Collection"""
        # 转换为标准配置
        standard_config = CollectionConfig(
            name=config.name,
            description=config.description,
            business_type=config.business_type,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            top_k=config.top_k,
            similarity_threshold=config.similarity_threshold,
        )

        # 设置Collection
        await self.rag_system.setup_collection(config.name)

        # 保存自定义配置
        self.custom_configs[config.name] = config

        print(f"✅ 创建专业Collection: {config.display_name} ({config.domain})")

    async def add_domain_knowledge(
        self, collection_name: str, knowledge_base: List[str]
    ):
        """添加领域专业知识"""
        if collection_name not in self.custom_configs:
            raise ValueError(f"Collection {collection_name} 不存在")

        config = self.custom_configs[collection_name]

        # 为知识添加领域标签
        metadata_list = [
            {
                "domain": config.domain,
                "language": config.language,
                "collection_type": "specialized",
                "business_type": config.business_type,
            }
            for _ in knowledge_base
        ]

        count = await self.rag_system.add_documents(
            knowledge_base, collection_name, metadata_list
        )

        print(
            f"✅ 向 {config.display_name} 添加了 {len(knowledge_base)} 个专业文档，生成 {count} 个节点"
        )
        return count

    async def specialized_query(
        self, question: str, collection_name: str
    ) -> Dict[str, Any]:
        """专业化查询"""
        if collection_name not in self.custom_configs:
            raise ValueError(f"Collection {collection_name} 不存在")

        config = self.custom_configs[collection_name]

        # 构建专业化查询
        specialized_question = self._build_specialized_query(question, config)

        # 执行查询
        result = await self.rag_system.query(
            specialized_question, collection_name, config.top_k
        )

        # 增强结果
        enhanced_result = {
            "answer": result.answer,
            "domain": config.domain,
            "collection_name": collection_name,
            "display_name": config.display_name,
            "source_count": result.source_count,
            "confidence_score": result.confidence_score,
            "query_time": result.query_time,
            "specialized": True,
            "sources": [
                {
                    "content": node.text,
                    "score": node.score,
                    "metadata": getattr(node, "metadata", {}),
                }
                for node in result.retrieved_nodes
            ],
        }

        return enhanced_result

    def _build_specialized_query(
        self, question: str, config: CustomCollectionConfig
    ) -> str:
        """构建专业化查询"""
        # 获取专业提示词
        domain_prompt = config.specialized_prompts.get(
            config.domain, f"作为{config.domain}领域的专家，"
        )

        # 构建专业化问题
        specialized_question = f"{domain_prompt}请回答以下问题：{question}"

        return specialized_question

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取Collection统计信息"""
        if collection_name not in self.custom_configs:
            raise ValueError(f"Collection {collection_name} 不存在")

        config = self.custom_configs[collection_name]
        base_info = await self.rag_system.get_collection_info(collection_name)

        # 增强统计信息
        enhanced_stats = {
            **base_info,
            "display_name": config.display_name,
            "domain": config.domain,
            "language": config.language,
            "specialized": True,
            "business_type": config.business_type,
        }

        return enhanced_stats

    async def cleanup(self):
        """清理资源"""
        if self.rag_system:
            await self.rag_system.cleanup()


# ==================== 专业领域Collection示例 ====================


async def create_medical_collection_example():
    """创建医学领域Collection示例"""
    print("🏥 医学领域Collection示例")

    manager = CustomCollectionManager()
    await manager.initialize()

    # 创建医学Collection配置
    medical_config = CustomCollectionConfig(
        name="medical_knowledge",
        display_name="医学知识库",
        description="专业医学知识和诊断信息",
        business_type="medical",
        domain="医学",
        chunk_size=800,  # 医学文档通常较长
        chunk_overlap=150,
        top_k=3,  # 医学查询需要精确性
        similarity_threshold=0.8,  # 较高的相似度阈值
        specialized_prompts={"医学": "作为专业医生，基于循证医学原则，"},
    )

    await manager.create_specialized_collection(medical_config)

    # 添加医学知识
    medical_knowledge = [
        "高血压是指血压持续升高的慢性疾病，收缩压≥140mmHg或舒张压≥90mmHg。",
        "糖尿病是一组以高血糖为特征的代谢性疾病，分为1型和2型糖尿病。",
        "心肌梗死是冠状动脉急性、持续性缺血缺氧所引起的心肌坏死。",
        "肺炎是指终末气道、肺泡和肺间质的炎症，可由多种病原体引起。",
        "阿司匹林用于预防心血管疾病，但需注意胃肠道出血风险。",
    ]

    await manager.add_domain_knowledge("medical_knowledge", medical_knowledge)

    # 专业化查询
    medical_questions = [
        "高血压的诊断标准是什么？",
        "糖尿病有哪些类型？",
        "如何预防心肌梗死？",
    ]

    for question in medical_questions:
        result = await manager.specialized_query(question, "medical_knowledge")
        print(f"\n❓ 医学问题: {question}")
        print(f"🏥 专业回答: {result['answer']}")
        print(f"📊 置信度: {result['confidence_score']:.3f}")
        print(f"📚 参考来源: {result['source_count']} 个")

    await manager.cleanup()
    print()


async def create_legal_collection_example():
    """创建法律领域Collection示例"""
    print("⚖️ 法律领域Collection示例")

    manager = CustomCollectionManager()
    await manager.initialize()

    # 创建法律Collection配置
    legal_config = CustomCollectionConfig(
        name="legal_knowledge",
        display_name="法律知识库",
        description="法律条文、案例和法律解释",
        business_type="legal",
        domain="法律",
        chunk_size=1200,  # 法律条文较长
        chunk_overlap=300,
        top_k=4,
        similarity_threshold=0.75,
        specialized_prompts={"法律": "作为专业律师，基于现行法律法规，"},
    )

    await manager.create_specialized_collection(legal_config)

    # 添加法律知识
    legal_knowledge = [
        "《民法典》规定，民事主体的人身权利、财产权利以及其他合法权益受法律保护。",
        "合同是民事主体之间设立、变更、终止民事法律关系的协议。",
        "侵权责任是指行为人因其行为侵害他人民事权益应当承担的民事责任。",
        "知识产权包括著作权、专利权、商标权等，受法律保护。",
        "劳动合同应当具备用人单位信息、劳动者信息、工作内容等必备条款。",
    ]

    await manager.add_domain_knowledge("legal_knowledge", legal_knowledge)

    # 法律专业查询
    legal_questions = [
        "什么是合同？",
        "侵权责任的构成要件是什么？",
        "劳动合同应包含哪些内容？",
    ]

    for question in legal_questions:
        result = await manager.specialized_query(question, "legal_knowledge")
        print(f"\n❓ 法律问题: {question}")
        print(f"⚖️ 法律解答: {result['answer']}")
        print(f"📊 置信度: {result['confidence_score']:.3f}")

    await manager.cleanup()
    print()


async def create_technical_collection_example():
    """创建技术领域Collection示例"""
    print("💻 技术领域Collection示例")

    manager = CustomCollectionManager()
    await manager.initialize()

    # 创建多个技术子领域Collection
    tech_configs = [
        CustomCollectionConfig(
            name="python_dev",
            display_name="Python开发",
            description="Python编程语言和开发技术",
            business_type="technical",
            domain="Python开发",
            chunk_size=600,
            top_k=5,
            specialized_prompts={"Python开发": "作为Python专家开发者，"},
        ),
        CustomCollectionConfig(
            name="web_frontend",
            display_name="前端开发",
            description="Web前端开发技术和框架",
            business_type="technical",
            domain="前端开发",
            chunk_size=700,
            top_k=4,
            specialized_prompts={"前端开发": "作为前端开发专家，"},
        ),
        CustomCollectionConfig(
            name="database_tech",
            display_name="数据库技术",
            description="数据库设计、优化和管理",
            business_type="technical",
            domain="数据库",
            chunk_size=800,
            top_k=3,
            specialized_prompts={"数据库": "作为数据库专家，"},
        ),
    ]

    # 创建所有技术Collection
    for config in tech_configs:
        await manager.create_specialized_collection(config)

    # 添加专业知识
    tech_knowledge = {
        "python_dev": [
            "Python是一种解释型、面向对象的高级编程语言。",
            "Django是一个高级Python Web框架，遵循MVC架构模式。",
            "FastAPI是一个现代、快速的Python Web框架，用于构建API。",
            "pandas是Python中用于数据分析和操作的强大库。",
        ],
        "web_frontend": [
            "React是一个用于构建用户界面的JavaScript库。",
            "Vue.js是一个渐进式JavaScript框架，易于学习和使用。",
            "CSS Grid和Flexbox是现代CSS布局的两大利器。",
            "Webpack是一个现代JavaScript应用程序的静态模块打包器。",
        ],
        "database_tech": [
            "MySQL是一个开源的关系型数据库管理系统。",
            "Redis是一个内存中的数据结构存储，用作数据库、缓存和消息代理。",
            "数据库索引可以显著提高查询性能，但会增加存储开销。",
            "ACID属性确保数据库事务的可靠性和一致性。",
        ],
    }

    # 添加知识到各个Collection
    for collection_name, knowledge in tech_knowledge.items():
        await manager.add_domain_knowledge(collection_name, knowledge)

    # 跨领域技术查询
    tech_questions = [
        ("python_dev", "如何使用Django开发Web应用？"),
        ("web_frontend", "React和Vue.js有什么区别？"),
        ("database_tech", "什么是数据库索引？"),
    ]

    for collection_name, question in tech_questions:
        result = await manager.specialized_query(question, collection_name)
        config = manager.custom_configs[collection_name]

        print(f"\n🔍 {config.display_name}查询: {question}")
        print(f"💻 技术回答: {result['answer']}")
        print(f"📊 置信度: {result['confidence_score']:.3f}")

    # 获取Collection统计
    print("\n📊 技术Collection统计:")
    for config in tech_configs:
        stats = await manager.get_collection_stats(config.name)
        print(f"  {stats['display_name']}: {stats.get('document_count', 0)} 文档")

    await manager.cleanup()
    print()


# ==================== Collection关联示例 ====================


class CollectionRelationshipManager:
    """Collection关联管理器"""

    def __init__(self):
        self.manager = CustomCollectionManager()
        self.relationships = {}  # collection_name -> [related_collections]

    async def initialize(self):
        """初始化关联管理器"""
        await self.manager.initialize()

    def add_relationship(
        self, collection1: str, collection2: str, relationship_type: str = "related"
    ):
        """添加Collection关联关系"""
        if collection1 not in self.relationships:
            self.relationships[collection1] = []
        if collection2 not in self.relationships:
            self.relationships[collection2] = []

        self.relationships[collection1].append(
            {"collection": collection2, "type": relationship_type}
        )
        self.relationships[collection2].append(
            {"collection": collection1, "type": relationship_type}
        )

        print(f"✅ 建立关联: {collection1} <-> {collection2} ({relationship_type})")

    async def cross_collection_query(
        self, question: str, primary_collection: str
    ) -> Dict[str, Any]:
        """跨Collection查询"""
        results = {}

        # 主Collection查询
        primary_result = await self.manager.specialized_query(
            question, primary_collection
        )
        results[primary_collection] = primary_result

        # 关联Collection查询
        if primary_collection in self.relationships:
            for relation in self.relationships[primary_collection]:
                related_collection = relation["collection"]
                try:
                    related_result = await self.manager.specialized_query(
                        question, related_collection
                    )
                    results[related_collection] = related_result
                except Exception as e:
                    print(f"⚠️ 关联查询失败 {related_collection}: {e}")

        return results

    async def cleanup(self):
        """清理资源"""
        await self.manager.cleanup()


async def collection_relationship_example():
    """Collection关联示例"""
    print("🔗 Collection关联示例")

    rel_manager = CollectionRelationshipManager()
    await rel_manager.initialize()

    # 创建相关的Collection
    configs = [
        CustomCollectionConfig(
            name="software_dev",
            display_name="软件开发",
            description="软件开发方法论和最佳实践",
            business_type="technical",
            domain="软件开发",
        ),
        CustomCollectionConfig(
            name="project_mgmt",
            display_name="项目管理",
            description="项目管理理论和实践",
            business_type="management",
            domain="项目管理",
        ),
    ]

    for config in configs:
        await rel_manager.manager.create_specialized_collection(config)

    # 添加知识
    knowledge_data = {
        "software_dev": [
            "敏捷开发是一种迭代的软件开发方法，强调快速交付和持续改进。",
            "代码审查是提高代码质量的重要实践。",
            "持续集成可以及早发现和修复问题。",
        ],
        "project_mgmt": [
            "项目管理包括启动、规划、执行、监控和收尾五个过程组。",
            "风险管理是项目成功的关键因素之一。",
            "团队沟通对项目成功至关重要。",
        ],
    }

    for collection_name, knowledge in knowledge_data.items():
        await rel_manager.manager.add_domain_knowledge(collection_name, knowledge)

    # 建立关联关系
    rel_manager.add_relationship("software_dev", "project_mgmt", "complementary")

    # 跨Collection查询
    question = "如何管理软件开发项目？"
    cross_results = await rel_manager.cross_collection_query(question, "software_dev")

    print(f"\n🔍 跨Collection查询: {question}")
    for collection_name, result in cross_results.items():
        config = rel_manager.manager.custom_configs[collection_name]
        print(f"\n📚 {config.display_name}视角:")
        print(f"   {result['answer']}")
        print(f"   置信度: {result['confidence_score']:.3f}")

    await rel_manager.cleanup()
    print()


# ==================== 主函数 ====================


async def main():
    """主函数 - 运行所有自定义Collection示例"""
    print("🎯 RAG知识库系统自定义Collection示例")
    print("=" * 60)

    examples = [
        create_medical_collection_example,
        create_legal_collection_example,
        create_technical_collection_example,
        collection_relationship_example,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ 示例 {example.__name__} 执行失败: {e}")

        print("-" * 40)

    print("🎉 所有自定义Collection示例执行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
