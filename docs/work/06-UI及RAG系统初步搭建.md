

## UI框架改动



```
请仔细熟悉我的智能体发开框架及步骤,代码及说明在backend/ai_core中,应用范例:接口层:backend/api/v1/testcase.py,服务层:backend/services/testcase
现在我想在对外接口不变化的前提下将UI智能体系统的代码按照该框架实现,UI的接口代码:backend/api/v1/midscene.py,服务层代码:backend/services/ui_testing
```





1. **模块化设计**：`backend/ai_core/` 提供统一的LLM客户端、智能体工厂、内存管理、运行时管理、消息队列
2. ujn业务解耦**：通用组件与业务逻辑分离，提高复用性
3. **健壮性优先**：完整的错误处理和容错机制
4. **工程化友好**：简化业务代码开发，提高开发效率



- **接口层**：`backend/api/v1/testcase.py` - 使用SSE流式输出
- **服务层**：`backend/services/testcase/` - 基于AI核心框架的业务封装
- **智能体实现**：使用`create_assistant_agent`、消息队列、内存管理
- **运行时管理**：专用运行时`TestCaseRuntime`继承`BaseRuntime`



## RAG服务搭建



```
我想搭建一个RAG服务:
技术: LlamaIndex Ollama Milvus

```



现在deepseek上寻求帮助

```
我想llama_index 怎么和ollama及Milvus结合在一起,请做一个demo,框架化一点,我已经远程部署好ollama及Milvus了,我想做一个RAG系统
```

![image-20250624235702179](./assets/image-20250624235702179.png)



deepseek帮我生成了相应的代码,从这份代码学习,将该代码跑通,之后融合到我现在的服务框架中

后续我发现demo还不算太难,但是在这个过程中遇到了很多的报错,需要自己从deepseek的文档中学习查找





```
帮我完成一个RAG系统demo的开发,代码放在
examples/llama_rag_system_demo中
使用Milvus向量数据库,Ollama大模型服务,llama_index
框架如下:
RAG System
├── 数据加载模块 (Data Loader)
├── 嵌入生成模块 (Embedding Generator)
├── Milvus向量数据库 (Vector DB)
├── Ollama大模型服务 (LLM Service)
└── 查询引擎 (Query Engine)

环境的配置在examples/conf/constants.py的settings,具体值在examples/conf/settings.yaml中
嵌入模型: "nomic-embed-text"
大语言模deepseek
大语言开发框架: llama_index
llama_index的文档:https://docs.llamaindex.ai/en/stable/api_reference/
最后给出一个小的案例来进行展示

```



```
1. 关于你刚才遇到的llm导入问题:
可以从这个页面得到答案:https://docs.llamaindex.ai/en/stable/examples/llm/deepseek/
from llama_index.llms.deepseek import DeepSeek
# you can also set DEEPSEEK_API_KEY in your environment variables
llm = DeepSeek(model="deepseek-reasoner", api_key="you_api_key")
2. examples/llama_rag_system_demo/config.py中配置可以放到examples/conf创建一个名为rag_config的目录
2. examples/llama_rag_system_demo目录下,文件太多,删除掉多余的文件,测试文件放在test目录下,让我可以更快的上手这个服务,框架更加清晰明了


```



```
examples/llama_rag_system_demo 这个目录下非服务核心部分的代码全部放到tests目录下
```





**核心服务文件（保留在主目录）**：

- `__init__.py` - 包初始化
- `utils.py` - 工具模块
- `rag.py` - 主入口文件
- `data_loader.py` - 数据加载模块
- `embedding_generator.py` - 嵌入生成模块
- `vector_store.py` - 向量数据库模块
- `llm_service.py` - LLM服务模块
- `query_engine.py` - 查询引擎模块

**非核心文件（移动到tests目录）**：

- `demo.py` - 演示案例
- `quick_start.py` - 快速开始示例
- `simple_example.py` - 简单示例
- `rag_system.py` - 完整版RAG系统（可选保留或移动）
- `README.md` - 文档





```
基于Milvus向量数据库,Ollama大模型服务,llama_index,deepseek开发一个RAG知识库系统,我已经完成了基础的框架,代码在examples/llama_rag_system_demo中
现在我想将其融合到我的后端代码中,后端代码在backend,可以在backend下建立一个rag_core的文件夹,将基础框架的代码放入其中
优化:rag未来支持多个collection可以为后端已有的服务或者不同的业务提供专业的知识库
```



```
向量数据的部分存在问题,嵌入数据库写到了本地backend/services/rag/milvus_llamaindex.db,而非远端的数据库中
```





```
优化AI对话模块backend/services/ai_chat/autogen_service.py,加入RAG知识库,支持选择不同的collection进行知识问答,支持前端上传文件到指定的collection中,回答能实时反馈RAG及智能体每个步骤返回的内容
前后端使用sse流式输出,可以参考backend/ai_core/message_queue.py和backend/services/testcase/agents.py及backend/api/v1/testcase.py中的消息队列流式输出的使用,代码能复用尽量复用
AI对话的API层backend/api/v1/chat.py
前端: frontend/src/pages/ChatPage.tsx做对应的修改和适配


```

前端

![image-20250625130859707](./assets/image-20250625130859707.png)



![image-20250625130916655](./assets/image-20250625130916655.png)





```
1.前段设计一个RAG管理界面放在AI模块下,可以对各个collection进行管理,可以对collection进行增删改查,可以collection中内容进行管理,后端进行相应的功能开发
2. AI对话模块右上角的选择collection及是否启用知识库的图标有些不美观
3. 前端的对话,RAG知识库的部分非流式输出,检查后端代码是否有问题
```



```
当前对话还是会被强制回到流式输出的位置,请继续修复这个问题
```







```
AI对话模块,当前滑动页面,会强制回到流式输出的位置,预期生成流式日志时,我应该还可以自由浏览相关内容
在前端页面刚打开时,会一直加载collecting,应该把collection写入到数据库中,直接调用数据库查询有哪些collecting,之后在前端展示
```







```
请你和我一起探索,作为一款RAG知识库系统,目前还欠缺那些功能,我们一起在已有服务的基础上,继续增强优化
我想在前端单独出一个RAG知识库管理的一级目录,其下面存放对RAG相关功能的管理
比如说单独的文件上传,解析,存储向量数据库等等这些
嵌入模型的管理等等这些
```



```
在backend/controllers目录下,是用来API和数据库交互的,backend/controllers/rag_controller.py不应该在该目录下,后端的目录backend下,backend/api存放接口,backend/controllers接口和数据库交互使用,backend/models数据库建模,backend/schemas接口及响应参数校验
请仔细阅读后端的代码,RAG相关的代码要符合该后端开发框架的规范
```



```
RAG知识库的代码backend/rag_core,请在其目录下创建一个docs,该目录下完成RAG开发规范及使用说明,范例,AI编程助手根据文档就可以知道如何进行相应的开发工作
```





```
统一请求结果和异常处理还需要再封装,抽象出一个可以复用的功能
参考: examples/backend_examples/app/schemas/base.py
和examples/backend_examples/app/core/exceptions.py中的后端框架做进一步优化,封装出通用的响应接口
受到影响的前端进行适配
```





```
请仔细阅读backend目录,在backend/docs目录下完成开发规范及使用说明
给出每一个模块的详细使用方式
sse的相关输出按照协议的规范来就可以了
API层,每个接口如何参数校验,如何统一返回参数,如何和数据库交互增删改查
backend/core/response.py的使用
backend/controllers中,如何复用已有的代码,简化增删改查操作,给出范例
backend/models,如何做模型定义,复用已有代码
backend/schemas 如何校验参数
backend/ai_core层,backend/rag_core层在其目录下已经有详细介绍了
```





```
对docs目录内的内容重新做整理,要分门别类清晰的放到对应的文件内,然后留下README.md
```









## 问题

```
目前RAG里面其实就包含了和llm对话返回内容的部分,但是chat的服务还会调用Autogen的对话,再次问一遍,这个功能以后优化

目前RAG知识库不是流式输出,且内容输出不是使用的消息队列的方式,这个都放到面在优化
```
