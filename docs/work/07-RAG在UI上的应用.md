UI的分析加入RAG知识库



步骤是

上传图片 -> UI分析

用户自然语言直接完成脚本



```
请仔细阅读backend/services/ui_testing 服务
对之前的业务逻辑进行调整
之前的逻辑: 用户上传图片 给到UIAnalysisAgent分析
用户自然语言描述 给到 InteractionAnalysisAgent分析
最后,汇总给MidsceneGenerationAgent生成测试用例给到ScriptGenerationAgent生成测试脚本,
当前需要结合RAG进行优化,RAG相关服务的核心代码在backend/rag_core中,请仔细阅读
修改逻辑为: 用户上传图片 给到UIAnalysisAgent分析的结果给到 RAG入库
用户直接说明需求 给到 RAG知识库做增强查询 最后将结果 汇总给MidsceneGenerationAgent生成测试用例 汇总后给到 ScriptGenerationAgent生成测试脚本
前端增加对应的上传图片页面及进度查询和相关Collection管理的界面,可以复用backend/api/v1/rag及backend/services/rag中内容

UI前端Collection分为两个,业务element 业务file


v1目录下建立一个ui-test的目录,UI测试相关图标放到该内容下


@ui_testing_router.get("/analysis-progress/{conversation_id}", summary="查询UI分析进度")的处理方式参考backend/api/v1/testcase.py中@testcase_router.post("/generate/streaming")接口的处理方式,使用消息队列来收集和输出消息




```



```
v1目录下建立一个ui-test的目录,UI测试相关图标放到该内容下
```







```
系统管理中,增加项目管理模块,增加前端页面后端接口数据库
用途: 将不同项目的UI,接口测试RAG知识库区分开来,默认设置一个通用项目
```



## 增加项目管理界面



```
前端问题修复:侧边导航栏,当折叠的二级标题全部展开时,侧边栏最下面的基于Autogen 0.5.7的字样会影响二级标题的展示,最下方的二级标题不能看见,修复该问题
```





```
系统管理中,增加项目管理模块,增加前端页面后端接口数据库
用途: 将不同项目的UI,接口测试RAG知识库区分开来,默认设置一个通用项目
```



```
后端/api/v1/system/projects?page=1&page_size=20 请求前端正常接收,但是前端未正常展示
```





```
1. 项目管理界面,设为默认的选项取消
2.前端: 项目管理每一个项目可以折叠,折叠打开可以看到项目所属部分,成员等等这些信息,数据库也增加相应的字段,都是选填,非必填
```
