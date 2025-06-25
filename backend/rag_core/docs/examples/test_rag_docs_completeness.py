"""
RAG知识库系统文档完整性测试

验证RAG文档系统的完整性和可用性
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def test_docs_structure():
    """测试文档结构完整性"""
    logger.info("📚 测试文档结构完整性")

    docs_dir = Path(__file__).parent.parent

    required_files = {
        "主文档": [
            "README.md",
            "architecture.md",
            "development_guide.md",
            "api_reference.md",
            "configuration.md",
            "troubleshooting.md",
            "changelog.md",
        ],
        "示例代码": [
            "examples/basic_usage.py",
            "examples/advanced_usage.py",
            "examples/custom_collection.py",
            "examples/integration_examples.py",
        ],
    }

    missing_files = []
    total_files = 0
    existing_files = 0

    for category, files in required_files.items():
        logger.info(f"  检查 {category}...")
        for file_name in files:
            total_files += 1
            file_path = docs_dir / file_name
            if file_path.exists():
                existing_files += 1
                logger.debug(f"    ✅ {file_name}")
            else:
                missing_files.append(f"{category}: {file_name}")
                logger.error(f"    ❌ {file_name}")

    if missing_files:
        logger.error(f"❌ 缺失文件: {missing_files}")
        return False

    coverage = (existing_files / total_files) * 100
    logger.success(
        f"✅ 文档结构完整，覆盖率: {coverage:.1f}% ({existing_files}/{total_files})"
    )
    return True


def test_docs_content_quality():
    """测试文档内容质量"""
    logger.info("📝 测试文档内容质量")

    docs_dir = Path(__file__).parent.parent

    content_checks = {
        "README.md": [
            "快速开始",
            "系统概述",
            "核心组件",
            "基础使用示例",
            "AI编程助手指南",
        ],
        "architecture.md": [
            "系统架构概览",
            "核心组件详解",
            "数据流架构",
            "多Collection架构",
            "配置管理架构",
        ],
        "development_guide.md": [
            "开发原则",
            "代码规范",
            "架构模式",
            "配置管理规范",
            "日志规范",
        ],
        "api_reference.md": [
            "RAGSystem",
            "QueryResult",
            "RAGConfig",
            "异常类",
            "使用模式",
        ],
        "configuration.md": [
            "配置概览",
            "配置类定义",
            "环境变量配置",
            "Django Settings配置",
            "配置加载优先级",
        ],
    }

    quality_issues = []

    for file_name, required_sections in content_checks.items():
        file_path = docs_dir / file_name
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")

            for section in required_sections:
                if section not in content:
                    quality_issues.append(f"{file_name} 缺少章节: {section}")

            # 检查文档长度
            if len(content) < 1000:
                quality_issues.append(f"{file_name} 内容过短 ({len(content)} 字符)")

        except Exception as e:
            quality_issues.append(f"{file_name} 读取失败: {e}")

    if quality_issues:
        logger.error(f"❌ 内容质量问题: {quality_issues}")
        return False

    logger.success("✅ 文档内容质量良好")
    return True


def test_examples_syntax():
    """测试示例代码语法"""
    logger.info("🐍 测试示例代码语法")

    examples_dir = Path(__file__).parent

    example_files = [
        "basic_usage.py",
        "advanced_usage.py",
        "custom_collection.py",
        "integration_examples.py",
    ]

    syntax_errors = []

    for file_name in example_files:
        file_path = examples_dir / file_name
        if not file_path.exists():
            continue

        try:
            # 检查Python语法
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            compile(code, file_path, "exec")
            logger.debug(f"    ✅ {file_name} 语法正确")

        except SyntaxError as e:
            syntax_errors.append(f"{file_name}: {e}")
            logger.error(f"    ❌ {file_name} 语法错误: {e}")
        except Exception as e:
            syntax_errors.append(f"{file_name}: {e}")
            logger.error(f"    ❌ {file_name} 检查失败: {e}")

    if syntax_errors:
        logger.error(f"❌ 语法错误: {syntax_errors}")
        return False

    logger.success("✅ 示例代码语法正确")
    return True


def test_docs_links():
    """测试文档内部链接"""
    logger.info("🔗 测试文档内部链接")

    docs_dir = Path(__file__).parent.parent

    # 检查README.md中的链接
    readme_path = docs_dir / "README.md"
    if not readme_path.exists():
        logger.error("❌ README.md 不存在")
        return False

    readme_content = readme_path.read_text(encoding="utf-8")

    # 检查文档链接
    doc_links = [
        "architecture.md",
        "development_guide.md",
        "api_reference.md",
        "configuration.md",
        "troubleshooting.md",
        "changelog.md",
    ]

    broken_links = []

    for link in doc_links:
        if link not in readme_content:
            broken_links.append(f"README.md 缺少链接: {link}")

        # 检查目标文件是否存在
        target_file = docs_dir / link
        if not target_file.exists():
            broken_links.append(f"链接目标不存在: {link}")

    # 检查示例目录链接
    examples_links = [
        "examples/basic_usage.py",
        "examples/advanced_usage.py",
        "examples/custom_collection.py",
        "examples/integration_examples.py",
    ]

    for link in examples_links:
        target_file = docs_dir / link
        if not target_file.exists():
            broken_links.append(f"示例文件不存在: {link}")

    if broken_links:
        logger.error(f"❌ 链接问题: {broken_links}")
        return False

    logger.success("✅ 文档链接完整")
    return True


def test_ai_assistant_guidance():
    """测试AI编程助手指导内容"""
    logger.info("🤖 测试AI编程助手指导内容")

    docs_dir = Path(__file__).parent.parent

    # 检查AI助手相关内容
    ai_guidance_checks = {
        "README.md": ["AI编程助手指南", "开发新功能时的步骤", "常用开发模式"],
        "development_guide.md": ["开发原则", "代码规范", "架构模式", "代码审查清单"],
        "api_reference.md": ["使用模式", "注意事项"],
    }

    guidance_issues = []

    for file_name, required_content in ai_guidance_checks.items():
        file_path = docs_dir / file_name
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")

        for item in required_content:
            if item not in content:
                guidance_issues.append(f"{file_name} 缺少AI指导内容: {item}")

    # 检查示例代码的完整性
    examples_dir = docs_dir / "examples"
    if examples_dir.exists():
        example_files = list(examples_dir.glob("*.py"))
        if len(example_files) < 4:
            guidance_issues.append(
                f"示例代码不足，当前: {len(example_files)}，期望: 4+"
            )

    if guidance_issues:
        logger.error(f"❌ AI指导内容问题: {guidance_issues}")
        return False

    logger.success("✅ AI编程助手指导内容完整")
    return True


def test_documentation_completeness():
    """测试文档完整性评分"""
    logger.info("📊 测试文档完整性评分")

    docs_dir = Path(__file__).parent.parent

    # 计算各项指标
    metrics = {"文档数量": 0, "示例数量": 0, "总字符数": 0, "代码示例数": 0}

    # 统计主文档
    main_docs = [
        "README.md",
        "architecture.md",
        "development_guide.md",
        "api_reference.md",
        "configuration.md",
        "troubleshooting.md",
        "changelog.md",
    ]

    for doc_name in main_docs:
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            metrics["文档数量"] += 1
            content = doc_path.read_text(encoding="utf-8")
            metrics["总字符数"] += len(content)
            # 统计代码块
            metrics["代码示例数"] += content.count("```")

    # 统计示例文件
    examples_dir = docs_dir / "examples"
    if examples_dir.exists():
        example_files = list(examples_dir.glob("*.py"))
        metrics["示例数量"] = len(example_files)

        for example_file in example_files:
            content = example_file.read_text(encoding="utf-8")
            metrics["总字符数"] += len(content)

    # 计算完整性评分
    max_scores = {
        "文档数量": 7,  # 7个主要文档
        "示例数量": 4,  # 4个示例文件
        "总字符数": 50000,  # 期望总字符数
        "代码示例数": 100,  # 期望代码示例数
    }

    total_score = 0
    max_total = 0

    logger.info("📈 文档指标:")
    for metric, value in metrics.items():
        max_value = max_scores[metric]
        score = min(value / max_value, 1.0) * 100
        total_score += score
        max_total += 100

        logger.info(f"  {metric}: {value} / {max_value} ({score:.1f}%)")

    overall_score = total_score / len(metrics)
    logger.info(f"\n🎯 文档完整性总评分: {overall_score:.1f}%")

    if overall_score >= 90:
        logger.success("🏆 文档质量优秀")
        return True
    elif overall_score >= 70:
        logger.info("👍 文档质量良好")
        return True
    else:
        logger.warning("⚠️ 文档质量需要改进")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始RAG文档完整性测试")

    tests = [
        ("文档结构", test_docs_structure),
        ("文档内容质量", test_docs_content_quality),
        ("示例代码语法", test_examples_syntax),
        ("文档链接", test_docs_links),
        ("AI助手指导", test_ai_assistant_guidance),
        ("文档完整性评分", test_documentation_completeness),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试: {test_name}")

        try:
            result = test_func()
            if result:
                logger.info(f"  ✅ {test_name}: 通过")
                passed += 1
            else:
                logger.info(f"  ❌ {test_name}: 失败")
        except Exception as e:
            logger.error(f"  ❌ {test_name}: 异常 - {e}")

    logger.info(f"\n{'='*50}")
    logger.info(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        logger.success("🎉 RAG文档系统完整性测试全部通过！")
        logger.info("✨ 文档系统特性:")
        logger.info("  📚 完整的开发规范和使用说明")
        logger.info("  🏗️ 详细的系统架构文档")
        logger.info("  📡 完整的API参考文档")
        logger.info("  ⚙️ 全面的配置管理指南")
        logger.info("  💡 丰富的示例代码")
        logger.info("  🔧 详细的故障排除指南")
        logger.info("  🤖 完善的AI编程助手指导")
        logger.info("")
        logger.info("🎯 AI编程助手现在可以基于这些文档:")
        logger.info("  1. 理解RAG系统架构和设计原则")
        logger.info("  2. 遵循开发规范和最佳实践")
        logger.info("  3. 使用完整的API接口")
        logger.info("  4. 参考丰富的示例代码")
        logger.info("  5. 快速定位和解决问题")
        logger.info("  6. 进行高质量的RAG开发工作")
        return True
    else:
        logger.error("💥 部分测试失败！")
        logger.info("🔧 请检查失败的测试项目并完善文档")
        return False


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
