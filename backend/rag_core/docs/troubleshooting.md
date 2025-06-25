# RAG知识库系统故障排除指南

## 🔧 常见问题与解决方案

### 1. 连接问题

#### 问题: Milvus连接失败
```
ConnectionError: Failed to connect to Milvus server
```

**可能原因:**
- Milvus服务未启动
- 网络连接问题
- 配置错误

**解决方案:**
```bash
# 1. 检查Milvus服务状态
docker ps | grep milvus

# 2. 启动Milvus服务
docker-compose up -d milvus-standalone

# 3. 检查网络连接
telnet localhost 19530

# 4. 验证配置
python -c "
from backend.conf.rag_config import get_rag_config
config = get_rag_config()
print(f'Milvus: {config.milvus.host}:{config.milvus.port}')
"
```

#### 问题: Ollama连接失败
```
ConnectionError: Failed to connect to Ollama server
```

**解决方案:**
```bash
# 1. 检查Ollama服务
curl http://localhost:11434/api/tags

# 2. 启动Ollama服务
ollama serve

# 3. 拉取嵌入模型
ollama pull nomic-embed-text

# 4. 验证模型可用性
ollama list
```

#### 问题: DeepSeek API调用失败
```
AuthenticationError: Invalid API key
```

**解决方案:**
```bash
# 1. 检查API密钥配置
echo $DEEPSEEK_API_KEY

# 2. 验证API密钥有效性
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     https://api.deepseek.com/v1/models

# 3. 在settings.py中配置
DEEPSEEK_API_KEY = "your_valid_api_key"
```

### 2. 配置问题

#### 问题: Collection配置错误
```
ValueError: Collection configuration is invalid
```

**检查清单:**
```python
# 验证Collection配置
def validate_collection_config(config):
    checks = [
        (config.dimension > 0, "dimension必须大于0"),
        (config.top_k > 0, "top_k必须大于0"),
        (0 <= config.similarity_threshold <= 1, "similarity_threshold必须在0-1之间"),
        (config.chunk_size > 0, "chunk_size必须大于0"),
        (config.chunk_overlap >= 0, "chunk_overlap不能为负数"),
        (config.chunk_overlap < config.chunk_size, "chunk_overlap必须小于chunk_size")
    ]

    for check, message in checks:
        if not check:
            print(f"❌ {message}")
            return False

    print("✅ Collection配置有效")
    return True
```

#### 问题: 环境变量未设置
```
ValueError: Required environment variable not set
```

**解决方案:**
```bash
# 创建.env文件
cat > .env << EOF
DEEPSEEK_API_KEY=your_api_key_here
MILVUS_HOST=localhost
MILVUS_PORT=19530
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
EOF

# 加载环境变量
source .env
```

### 3. 性能问题

#### 问题: 查询响应慢
```
查询耗时超过10秒
```

**诊断步骤:**
```python
import time
from backend.rag_core.rag_system import RAGSystem

async def diagnose_performance():
    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 测试嵌入生成速度
        start = time.time()
        await rag.add_text("测试文本", "general")
        embed_time = time.time() - start
        print(f"嵌入生成耗时: {embed_time:.3f}秒")

        # 测试检索速度
        start = time.time()
        result = await rag.query("测试查询", "general")
        query_time = time.time() - start
        print(f"查询耗时: {query_time:.3f}秒")

        # 分析瓶颈
        if embed_time > 2.0:
            print("⚠️ 嵌入生成较慢，检查Ollama服务")
        if query_time > 5.0:
            print("⚠️ 查询较慢，检查Milvus性能")
```

**优化建议:**
1. **减少top_k值**: 降低检索数量
2. **批量操作**: 使用`add_documents`而非多次`add_text`
3. **调整chunk_size**: 较小的chunk可能提高检索精度
4. **硬件升级**: 增加内存和CPU资源

#### 问题: 内存使用过高
```
MemoryError: Out of memory
```

**解决方案:**
```python
# 1. 监控内存使用
import psutil

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")

# 2. 优化批处理大小
async def optimized_batch_add(rag, documents, collection_name, batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        await rag.add_documents(batch, collection_name)
        monitor_memory()

# 3. 及时清理资源
async with RAGSystem() as rag:
    # 使用上下文管理器确保资源释放
    pass
```

### 4. 数据问题

#### 问题: 文档添加失败
```
EmbeddingError: Failed to generate embeddings
```

**诊断步骤:**
```python
async def diagnose_document_issues():
    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 测试不同类型的文档
        test_cases = [
            ("正常文本", "这是一个正常的文档内容。"),
            ("空文本", ""),
            ("超长文本", "很长的文本..." * 1000),
            ("特殊字符", "包含特殊字符: @#$%^&*()"),
            ("非UTF-8", "包含emoji: 😀🎉🚀"),
        ]

        for name, text in test_cases:
            try:
                count = await rag.add_text(text, "general")
                print(f"✅ {name}: 成功添加 {count} 个节点")
            except Exception as e:
                print(f"❌ {name}: 失败 - {e}")
```

#### 问题: 查询结果不准确
```
查询返回不相关的结果
```

**调优策略:**
```python
async def tune_query_accuracy():
    async with RAGSystem() as rag:
        await rag.setup_collection("general")

        # 添加测试数据
        documents = [
            "Python是一种编程语言",
            "Java是另一种编程语言",
            "苹果是一种水果",
            "香蕉也是水果"
        ]
        await rag.add_documents(documents, "general")

        # 测试不同参数
        question = "编程语言有哪些？"

        for top_k in [2, 3, 5]:
            result = await rag.query(question, "general", top_k=top_k)
            print(f"top_k={top_k}: {result.answer}")
            print(f"置信度: {result.confidence_score:.3f}")
            print("---")
```

### 5. 日志分析

#### 启用详细日志
```python
import logging
from loguru import logger

# 配置详细日志
logger.add(
    "rag_debug.log",
    level="DEBUG",
    format="{time} | {level} | {name}:{function}:{line} - {message}",
    rotation="10 MB"
)

# 在代码中添加调试信息
async def debug_rag_operation():
    logger.debug("开始RAG操作")

    async with RAGSystem() as rag:
        logger.debug("RAG系统初始化完成")

        await rag.setup_collection("general")
        logger.debug("Collection设置完成")

        count = await rag.add_text("测试文档", "general")
        logger.debug(f"文档添加完成，节点数: {count}")

        result = await rag.query("测试查询", "general")
        logger.debug(f"查询完成，结果长度: {len(result.answer)}")
```

#### 常见日志模式
```bash
# 查看错误日志
grep "ERROR" rag_debug.log

# 查看性能相关日志
grep "耗时\|performance" rag_debug.log

# 查看连接问题
grep "connection\|connect" rag_debug.log

# 查看特定组件日志
grep "Milvus\|Ollama\|DeepSeek" rag_debug.log
```

### 6. 系统健康检查

#### 创建健康检查脚本
```python
async def health_check():
    """系统健康检查"""
    print("🏥 RAG系统健康检查")

    checks = []

    # 1. 配置检查
    try:
        from backend.conf.rag_config import get_rag_config
        config = get_rag_config()
        checks.append(("配置加载", True, "配置正常"))
    except Exception as e:
        checks.append(("配置加载", False, str(e)))

    # 2. 服务连接检查
    try:
        async with RAGSystem() as rag:
            await rag.setup_collection("health_check")
            checks.append(("RAG系统", True, "连接正常"))
    except Exception as e:
        checks.append(("RAG系统", False, str(e)))

    # 3. 基本功能检查
    try:
        async with RAGSystem() as rag:
            await rag.setup_collection("health_check")
            await rag.add_text("健康检查文档", "health_check")
            result = await rag.query("健康检查", "health_check")
            checks.append(("基本功能", True, "功能正常"))
    except Exception as e:
        checks.append(("基本功能", False, str(e)))

    # 输出检查结果
    print("\n📋 检查结果:")
    for name, status, message in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {message}")

    # 总体状态
    all_passed = all(check[1] for check in checks)
    status = "健康" if all_passed else "异常"
    print(f"\n🎯 系统状态: {status}")

    return all_passed
```

### 7. 常用调试命令

#### 快速诊断脚本
```bash
#!/bin/bash
# rag_diagnose.sh

echo "🔍 RAG系统快速诊断"

echo "1. 检查服务状态..."
docker ps | grep -E "(milvus|ollama)"

echo "2. 检查端口占用..."
netstat -tlnp | grep -E "(19530|11434)"

echo "3. 检查环境变量..."
env | grep -E "(DEEPSEEK|MILVUS|OLLAMA)"

echo "4. 检查磁盘空间..."
df -h

echo "5. 检查内存使用..."
free -h

echo "6. 测试网络连接..."
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama连接正常" || echo "❌ Ollama连接失败"

echo "诊断完成！"
```

### 8. 性能基准测试

#### 基准测试脚本
```python
import asyncio
import time
from statistics import mean, median

async def benchmark_rag_system():
    """RAG系统性能基准测试"""
    print("📊 RAG系统性能基准测试")

    async with RAGSystem() as rag:
        await rag.setup_collection("benchmark")

        # 1. 文档添加性能测试
        documents = [f"基准测试文档{i}" for i in range(100)]

        start_time = time.time()
        total_nodes = await rag.add_documents(documents, "benchmark")
        add_time = time.time() - start_time

        print(f"📝 文档添加: {len(documents)}个文档, {total_nodes}个节点")
        print(f"   耗时: {add_time:.3f}秒")
        print(f"   速度: {len(documents)/add_time:.2f}文档/秒")

        # 2. 查询性能测试
        questions = [
            "基准测试的目的是什么？",
            "文档1包含什么内容？",
            "测试结果如何？"
        ]

        query_times = []
        for question in questions:
            start_time = time.time()
            result = await rag.query(question, "benchmark")
            query_time = time.time() - start_time
            query_times.append(query_time)

        print(f"\n🔍 查询性能: {len(questions)}个查询")
        print(f"   平均耗时: {mean(query_times):.3f}秒")
        print(f"   中位数耗时: {median(query_times):.3f}秒")
        print(f"   最大耗时: {max(query_times):.3f}秒")
        print(f"   最小耗时: {min(query_times):.3f}秒")

if __name__ == "__main__":
    asyncio.run(benchmark_rag_system())
```

## 🆘 获取帮助

如果以上解决方案都无法解决问题：

1. **查看详细日志**: 启用DEBUG级别日志
2. **运行健康检查**: 使用提供的健康检查脚本
3. **性能基准测试**: 对比正常性能指标
4. **检查系统资源**: CPU、内存、磁盘、网络
5. **验证依赖服务**: Milvus、Ollama、DeepSeek API

## 📞 技术支持

- 查看系统日志: `tail -f rag_debug.log`
- 运行诊断脚本: `bash rag_diagnose.sh`
- 执行健康检查: `python health_check.py`
- 性能基准测试: `python benchmark.py`
