from anthropic.types import URLImageSourceParam

# Create a vector store with a sample text
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_milvus import Milvus
from pymilvus import Collection, MilvusException, connections, db, utility

text = """
['**《大型语言模型（LLM）系列产品工具及提示词工程》专业培训大纲**\n\n\n目标学员: 金融行业产品经理、运营人员、技术开发者、数据分析师、风险管理人员、\n\n\n合规专员以及对LLM 应用感兴趣的相关人员。\n\n\n培训目标:\n\n\n  - 全面了解主流大型语言模型的特点、能力边界与选型策略。\n\n\n  - 掌握LLM 的多种使用方式，理解企业级接入与部署的关键考量。\n\n\n  - 精通提示词工程的核心原理、结构与高级技巧。\n\n\n  - 能够针对金融领域的具体场景（分析、客服、风控等）设计、优化和应用高效\n\n\n提示词。\n\n\n  - 理解LLM 使用的最佳实践、伦理考量与未来趋势。 **先决条件:** 对人工智能和\n\n\n金融业务有基本了解。\n\n\n**模块一：大型语言模型（LLM）概览与选型**\n\n\n  - **1.1 主流LLM 产品深度解析**\n\n\n`o` **核心模型介绍:**\n\n\n          **国际代表:**\n\n\n              DeepSeek (特点: 开源、代码能力)\n\n\n              ChatGPT (特点: 综合能力、插件生态)\n\n\n              Claude (特点: 长文本处理、安全与伦理)\n\n\n              Gemini (特点: 多模态、Google 生态集成)\n\n\n          **国内代表:**\n\n\n              文心一言 (特点: 中文理解、百度生态)\n\n\n              通义千问 (特点: 综合能力、阿里生态)\n\n\n              讯飞星火 (特点: 语音交互、跨领域知识)\n\n\n          (实时更新) 其他值得关注的新兴模型。\n\n\n          **演示:** 对比不同模型对同一通用任务的响应（如摘要、翻译）。\n\n\n\n-----\n\n`o` **开源 vs. 闭源 LLM:**\n\n\n        定义与代表模型。\n\n\n        **核心差异:** 成本、定制化潜力、数据隐私控制、更新频率、社区\n\n\n支持。\n\n\n        **案例讨论:** 为何某金融科技公司选择基于开源模型微调，而另一\n\n\n家大型银行选择使用闭源模型的API？\n\n\n- **1.2 LLM 核心能力维度对比**\n\n\n`o` **语言理解与生成:**', '家大型银行选择使用闭源模型的API？\n\n\n- **1.2 LLM 核心能力维度对比**\n\n\n`o` **语言理解与生成:**\n\n\n        文本摘要、内容创作、翻译、情感分析等能力对比。\n\n\n        **实例:** 使用不同模型生成同一主题的营销文案，对比风格和效\n\n\n果。\n\n\n`o` **多模态能力:**\n\n\n        图像理解 (OCR, 图表解读, 图像描述)。\n\n\n        图像生成 (根据描述创作)。\n\n\n        音频处理 (语音识别、语音合成)。\n\n\n        **实例:** 使用多模态模型解读财报截图中的图表，或根据语音指令\n\n\n生成会议纪要。\n\n\n`o` **工具使用与代码能力:**\n\n\n        Function Calling / Tool Use 机制介绍。\n\n\n        代码生成、解释、调试能力。\n\n\n        **演示:** 如何让LLM 调用外部API（如实时股价查询）或生成一段\n\n\nPython 数据分析脚本。\n\n\n`o` **安全性与合规性:**\n\n\n        偏见与歧视风险。\n\n\n        数据泄露风险。\n\n\n        “幻觉”现象与事实核查。\n\n\n        不同模型的安全防护机制对比。\n\n\n        **讨论:** 金融场景下，哪些安全合规问题最为关键？\n\n\n\n-----\n\n  - **1.3 如何为您的业务选择合适的LLM**\n\n\n`o` **选型核心考量因素:**\n\n\n          任务匹配度 (特定能力强项)。\n\n\n          性能指标 (准确率、响应速度)。\n\n\n          集成复杂度 (API 友好度、文档支持)。\n\n\n          供应商可靠性与技术支持。\n\n\n          社区生态与未来发展。\n\n\n`o` **成本效益分析:**\n\n\n          API 调用成本 (Token 计费)。\n\n\n          私有化部署成本 (硬件、人力)。\n\n\n          订阅费用。\n\n\n          **模板:** 提供一个简单的成本效益分析框架供学员参考。\n\n\n`o` **隐私保护与数据安全:**', '订阅费用。\n\n\n          **模板:** 提供一个简单的成本效益分析框架供学员参考。\n\n\n`o` **隐私保护与数据安全:**\n\n\n          数据处理协议 (Data Processing Agreements)。\n\n\n          数据是否用于模型再训练？\n\n\n          数据传输与存储加密。\n\n\n          满足金融监管要求（如GDPR, CCPA, 国内相关法规）。\n\n\n          **案例分析:** 对比不同云服务商提供的LLM 在数据隐私保护条款\n\n\n上的差异。\n\n\n**模块二：LLM 使用方式与企业级集成**\n\n\n  - **2.1 多样化的LLM 使用方式**\n\n\n`o` **Web/移动端交互:**\n\n\n          官方界面、第三方应用。\n\n\n          优点：易上手、快速验证。缺点：自动化程度低、难以集成。\n\n\n          **实操:** 学员现场体验不同模型的官方Web 界面。\n\n\n`o` **API 调用:**\n\n\n\n-----\n\n        RESTful API 基础。\n\n\n        关键参数 (模型、温度、最大Token 数等) 解释。\n\n\n        **代码示例:** Python 调用主流LLM API 的基本代码框架。\n\n\n`o` **大型云平台服务 (LLM as a Service):**\n\n\n        AWS Bedrock, Azure OpenAI Service, Google Vertex AI 等。\n\n\n        优点：托管服务、易扩展、集成生态。\n\n\n        **介绍:** 各大云平台提供的LLM 服务特点和优势。\n\n\n- **2.2 企业级LLM 接入与部署策略**\n\n\n`o` **私有化部署 vs. 云服务:**\n\n\n        **对比维度:** 数据控制权、安全性、成本、维护复杂度、性能、合\n\n\n规性。\n\n\n        **决策树:** 提供一个简单的决策框架，帮助企业根据自身情况选\n\n\n择。\n\n\n        **案例研究:** 分析某证券公司选择私有化部署的动因和挑战。\n\n\n`o` **安全访问与身份认证:**\n\n\n        API 密钥管理最佳实践。', '择。\n\n\n        **案例研究:** 分析某证券公司选择私有化部署的动因和挑战。\n\n\n`o` **安全访问与身份认证:**\n\n\n        API 密钥管理最佳实践。\n\n\n        身份认证与授权 (IAM, OAuth)。\n\n\n        网络隔离 (VPC, Private Link)。\n\n\n`o` **数据保护与敏感信息处理:**\n\n\n        数据脱敏技术 (假名化、匿名化)。\n\n\n        PII (个人身份信息) 检测与过滤。\n\n\n        输入/输出内容监控与审计。\n\n\n        **讨论:** 如何在客服场景中应用LLM，同时确保客户敏感信息不被\n\n\n泄露或滥用？\n\n\n- **2.3 LLM 应用开发平台与工具**\n\n\n`o` **低代码/无代码平台:**\n\n\n        介绍集成LLM 能力的平台 (如 Zapier, Make, Coze 等)。\n\n\n        **演示:** 如何通过无代码平台快速搭建一个“邮件内容摘要”应用。\n\n\n\n-----\n\n`o` **应用开发框架:**\n\n\n          LangChain, LlamaIndex 等核心概念与用途。\n\n\n          **简介:** 如何使用框架构建更复杂的LLM 应用 (如 RAG)。\n\n\n`o` **知识库与LLM 结合 (Retrieval-Augmented Generation - RAG):**\n\n\n          原理：解决LLM“幻觉”和知识更新问题。\n\n\n          构建流程：数据准备、向量化、检索、生成。\n\n\n          **案例:** 如何构建一个基于内部合规文档库的智能问答系统。\n\n\n**模块三：提示词工程（Prompt Engineering）核心原理与技巧**\n\n\n  - **3.1 提示词工程导论**\n\n\n`o` **定义:** 什么是提示词 (Prompt)？它为何如此重要？(Garbage In,\n\n\nGarbage Out)。\n\n\n`o` **类比:** 提示词如同与“非常聪明但不了解具体任务的实习生”沟通的指\n\n\n令。\n\n\n`o` **基本原则:** 清晰性 (Clarity)、具体性 (Specificity)、上下文 (Context)、', '令。\n\n\n`o` **基本原则:** 清晰性 (Clarity)、具体性 (Specificity)、上下文 (Context)、\n\n\n简洁性 (Conciseness)。\n\n\n`o` **好/坏提示词对比:**\n\n\n          **实例:** 对比模糊指令与清晰指令产生的巨大差异。\n\n\n              差: "总结一下市场情况。"\n\n\n              好: "请扮演一位资深金融分析师，根据过去24 小时[指\n\n\n定信息源]的主要新闻，为我总结全球股票市场的三个关\n\n\n键动态，并指出每个动态对科技板块可能的影响。使用\n\n\n项目符号列表格式。"\n\n\n  **3.2 高效提示词的结构化设计 (CRISP/RCIOS 等框架)**\n\n\n`o` **核心要素拆解:**\n\n\n          **角色 (Role/Persona):** "你是一位经验丰富的财富顾问..."\n\n\n          **指令 (Instruction/Task):** "请分析这份财报..." / "生成一封安抚邮\n\n\n件..."\n\n\n          **背景 (Context/Input Data):** "这是客户过去一年的交易记录..." /\n\n\n\n-----\n\n"以下是相关的市场新闻..."\n\n\n        **输出格式 (Output Format):** "请以JSON 格式返回结果..." / "使\n\n\n用专业的商业信函格式..."\n\n\n        **补充要素:** 语气 (Tone), 目标受众 (Audience), 约束条件\n\n\n(Constraints)。\n\n\n`o` **模板化:** 提供几种常用场景的提示词模板结构。\n\n\n`o` **练习:** 学员分组，针对给定场景，设计结构化的提示词。\n\n\n- **3.3 实用提示词技巧与高级模式**\n\n\n`o` **任务分解 (Decomposition / Chain of Thought - CoT):**\n\n\n        引导模型“思考步骤”。将复杂任务拆解为子任务。\n\n\n        **实例:** 如何让模型先分析原因，再提出解决方案。\n\n\n`o` **思维链提示 (Chain-of-Thought Prompting):**', '**实例:** 如何让模型先分析原因，再提出解决方案。\n\n\n`o` **思维链提示 (Chain-of-Thought Prompting):**\n\n\n        提供包含推理过程的示例，引导模型模仿。\n\n\n        **演示:** 对比标准提示和CoT 提示在解决逻辑推理问题上的效\n\n\n果。\n\n\n`o` **少量示例学习 (Few-Shot Learning):**\n\n\n        在提示词中提供1-5 个输入/输出范例。\n\n\n        **实例:** 如何通过示例让模型学会特定风格的文本生成或信息提\n\n\n取。\n\n\n`o` **零示例学习 (Zero-Shot Learning):** 依靠模型的泛化能力直接执行任\n\n\n务。\n\n\n`o` **迭代优化:**\n\n\n        测试 -> 分析输出 -> 修改提示词 -> 再测试 的循环过程。\n\n\n        如何根据不理想的输出反推提示词的问题所在。\n\n\n        **技巧:** 尝试不同措辞、调整结构、增减上下文、改变温度参数\n\n\n等。\n\n\n`o` **实战演练:** 提供一个不完美的提示词和输出，引导学员进行分析和优\n\n\n化。\n\n\n\n-----\n\n**模块四：金融场景提示词工程实战应用**\n\n\n  - **4.1 金融分析与研究报告类应用**\n\n\n`o` **市场动态分析:**\n\n\n          **模板:** 设计用于总结宏观经济指标、行业新闻、竞品动态的提示\n\n\n词。\n\n\n          **案例:** 从大量财经新闻中自动提取关键信息，生成每日市场摘\n\n\n要。\n\n\n`o` **财务报告解读:**\n\n\n          **模板:** 提取关键财务指标 (营收、利润、增长率)、分析变化原\n\n\n因、识别潜在风险。\n\n\n          **案例:** 快速解读上市公司季度财报PDF，生成关键要点摘要。\n\n\n`o` **投资研究与建议:**\n\n\n          **模板:** 结构化生成投资逻辑、风险评估、估值分析框架。 (注意:\n\n\n强调LLM 仅为辅助，不能替代专业判断和合规审查)\n\n\n          **讨论:** 如何设计提示词以生成初步的、平衡风险与收益的投资思\n\n\n路？\n\n\n  - **4.2 客户服务与沟通咨询类应用**', '**讨论:** 如何设计提示词以生成初步的、平衡风险与收益的投资思\n\n\n路？\n\n\n  - **4.2 客户服务与沟通咨询类应用**\n\n\n`o` **金融产品智能问答:**\n\n\n          **模板:** 结合RAG，基于产品说明书和FAQ，回答客户关于利\n\n\n率、费用、申请条件的咨询。\n\n\n          **案例:** 构建虚拟客服助手，处理常见的银行业务咨询。\n\n\n`o` **客户意图识别与问题分类:**\n\n\n          **模板:** 分析客户消息，判断其意图（咨询、投诉、建议）并分配\n\n\n给相应处理流程。\n\n\n`o` **沟通文案生成与润色:**\n\n\n          **模板:** 生成标准化的客户通知、营销邮件、投诉回复初稿。\n\n\n          **案例:** 辅助客户经理撰写个性化的客户关怀邮件。\n\n\n`o` **角色扮演练习:** 学员扮演客服，使用LLM 辅助回答模拟的客户刁钻问\n\n\n题。\n\n\n\n-----\n\n  - **4.3 风险管理与合规审查类应用**\n\n\n`o` **文档合规性检查:**\n\n\n          **模板:** 对比合同条款、营销材料与内部合规规则库，识别潜在违\n\n\n规点。\n\n\n          **案例:** 初步审查贷款申请材料是否符合银行政策要求。\n\n\n`o` **风险事件识别与预警:**\n\n\n          **模板:** 从新闻、社交媒体、监管公告中监测与特定公司或行业相\n\n\n关的负面信息或风险信号。\n\n\n`o` **反洗钱(AML)与欺诈检测辅助:**\n\n\n          **模板:** 总结可疑交易模式描述、辅助生成可疑活动报告(SAR)的\n\n\n文本内容 (强调：仅为辅助，需严格遵守法规)。\n\n\n          **讨论:** LLM 在风控合规中的应用边界和潜在风险。\n\n\n  - **4.4 综合实战演练与优化工作坊**\n\n\n`o` **场景设定:** 提供1-2 个贴近学员工作的金融业务场景 (如: "为某基金撰\n\n\n写营销亮点", "分析某股票的近期风险")。\n\n\n`o` **分组任务:** 学员分组，针对指定场景，合作设计、测试并迭代优化提示\n\n\n词。\n\n\n`o` **成果展示与分享:** 各组展示其最佳提示词和生成结果。', '`o` **分组任务:** 学员分组，针对指定场景，合作设计、测试并迭代优化提示\n\n\n词。\n\n\n`o` **成果展示与分享:** 各组展示其最佳提示词和生成结果。\n\n\n`o` **专家点评与最佳实践总结:** 讲师对各组进行点评，总结该场景下的最佳\n\n\n实践和常见陷阱。\n\n\n**模块五：总结、最佳实践与未来展望**\n\n\n  - **5.1 核心要点回顾**\n\n\n`o` LLM 选型关键因素。\n\n\n`o` 企业级应用考量。\n\n\n`o` 高效提示词设计的核心原则 (角色、指令、上下文、格式)。\n\n\n`o` 关键提示词技巧 (CoT, Few-shot, 迭代)。\n\n\n  - **5.2 LLM 使用最佳实践与伦理考量**\n\n\n\n-----\n\n`o` 建立提示词库与版本控制。\n\n\n`o` 持续监控与评估模型输出质量。\n\n\n`o` 人机协同 (Human-in-the-loop) 的重要性。\n\n\n`o` 负责任的AI：识别与缓解偏见、保护隐私、透明度、可解释性。\n\n\n`o` **讨论:** 在金融领域推动LLM 应用时，最重要的伦理原则是什么？\n\n\n- **5.3 未来趋势与展望**\n\n\n`o` 更强的多模态能力。\n\n\n`o` AI Agents 与自主任务执行。\n\n\n`o` 领域专用模型 (Domain-Specific Models) 的发展。\n\n\n`o` 个性化与自适应学习。\n\n\n**5.4 互动问答 (Q&A)**\n\n\n`o` 解答学员疑问，深入探讨特定问题。\n\n\n- **5.5 培训评估与后续资源**\n\n\n`o` 收集反馈。\n\n\n`o` 提供延伸阅读材料、工具链接、社区资源。']


"""
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="qwen3-embedding:0.6b", base_url="http://101.126.90.71:11434"
)
s = embeddings.embed_query(text)
print(s)
# # 使用embeddings 嵌入对象将 text 转换为向量，然后存入向量数据库
# vectorstore = InMemoryVectorStore.from_texts(
#     [text],
#     embedding=embeddings,
# )

URI = "http://101.126.90.71:19530"

conn = connections.connect(host="101.126.90.71", port=19530)


# Check if the database exists
db_name = "milvus_demo"
# try:
#     existing_databases = db.list_database()
#     if db_name in existing_databases:
#         print(f"Database '{db_name}' already exists.")
#
#         # Use the database context
#         db.using_database(db_name)
#
#         # Drop all collections in the database
#         collections = utility.list_collections()
#         for collection_name in collections:
#             collection = Collection(name=collection_name)
#             collection.drop()
#             print(f"Collection '{collection_name}' has been dropped.")
#
#         db.drop_database(db_name)
#         print(f"Database '{db_name}' has been deleted.")
#     else:
#         print(f"Database '{db_name}' does not exist.")
#         database = db.create_database(db_name)
#         print(f"Database '{db_name}' created successfully.")
# except MilvusException as e:
#     print(f"An error occurred: {e}")

vectorstore = Milvus(
    embedding_function=embeddings,
    connection_args={"uri": URI, "token": "root:Milvus", "db_name": "milvus_demo"},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
    consistency_level="Strong",
    drop_old=False,  # set to True if seeking to drop the collection with that name if it exists
)

# 将文本添加到向量数据库
print("正在将文本添加到向量数据库...")
vectorstore.add_texts([text])
print("文本添加成功！")

# 使用向量数据库进行查询
print("\n正在查询相关信息...")
retriever = vectorstore.as_retriever()

# 查询与LLM相关的信息
retrieved_documents = retriever.invoke("什么是大型语言模型？")

# 显示检索到的文档内容
print(f"检索到 {len(retrieved_documents)} 个相关文档")
if retrieved_documents:
    print("\n最相关的文档内容：")
    print(retrieved_documents[0].page_content[:500] + "...")
else:
    print("未检索到相关文档")
