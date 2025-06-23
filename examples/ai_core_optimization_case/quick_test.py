#!/usr/bin/env python3
"""
AI核心框架优化案例快速验证脚本
验证案例代码的完整性和功能性
"""

import sys
from pathlib import Path

# 添加案例代码路径
case_root = Path(__file__).parent
sys.path.insert(0, str(case_root))


def test_case_structure():
    """测试案例目录结构"""
    print("🔍 检查案例目录结构...")

    required_files = [
        "README.md",
        "docs/optimization_plan.md",
        "docs/optimization_summary.md",
        "docs/usage_guide.md",
        "code/ai_core_enhanced/__init__.py",
        "code/ai_core_enhanced/builder.py",
        "code/ai_core_enhanced/config.py",
        "code/ai_core_enhanced/templates.py",
        "code/integration_examples/demo.py",
        "code/integration_examples/optimized_service.py",
        "configs/agents/requirement_analysis.yaml",
        "configs/templates/requirement_analysis.txt",
        "tests/test_optimization.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = case_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")

    if missing_files:
        print(f"\n❌ 缺失文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("✅ 目录结构完整")
    return True


def test_imports():
    """测试模块导入"""
    print("\n🔍 测试模块导入...")

    try:
        # 测试增强版AI核心模块导入
        from code.ai_core_enhanced import (
            AgentBuilder,
            PresetAgentBuilder,
            agent_builder,
            get_agent_config,
            render_template,
        )

        print("   ✅ 增强版AI核心模块导入成功")
        return True

    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False


def test_config_files():
    """测试配置文件"""
    print("\n🔍 测试配置文件...")

    try:
        import yaml

        # 测试智能体配置文件
        config_file = case_root / "configs/agents/requirement_analysis.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        required_keys = ["name", "model_type", "system_message"]
        for key in required_keys:
            if key not in config:
                print(f"   ❌ 配置文件缺少字段: {key}")
                return False

        print("   ✅ 智能体配置文件格式正确")

        # 测试模板文件
        template_file = case_root / "configs/templates/requirement_analysis.txt"
        with open(template_file, "r", encoding="utf-8") as f:
            template_content = f.read()

        if (
            "{project_background}" in template_content
            and "{analysis_focus}" in template_content
        ):
            print("   ✅ 模板文件格式正确")
            return True
        else:
            print("   ❌ 模板文件缺少必要变量")
            return False

    except Exception as e:
        print(f"   ❌ 配置文件测试失败: {e}")
        return False


def test_documentation():
    """测试文档完整性"""
    print("\n🔍 测试文档完整性...")

    try:
        # 检查README文档
        readme_file = case_root / "README.md"
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()

        required_sections = ["案例概述", "目录结构", "优化目标", "优化效果", "快速体验"]

        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)

        if missing_sections:
            print(f"   ❌ README缺少章节: {missing_sections}")
            return False

        print("   ✅ README文档完整")

        # 检查使用指南
        guide_file = case_root / "docs/usage_guide.md"
        if guide_file.exists():
            print("   ✅ 使用指南存在")
        else:
            print("   ❌ 使用指南缺失")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 文档测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 AI核心框架优化案例快速验证")
    print("=" * 50)

    tests = [
        ("目录结构", test_case_structure),
        ("模块导入", test_imports),
        ("配置文件", test_config_files),
        ("文档完整性", test_documentation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 项通过")

    if passed == total:
        print("🎉 案例验证通过！所有组件都已正确整理。")
        print("\n📋 使用说明:")
        print("   1. 查看 README.md 了解案例概述")
        print("   2. 阅读 docs/usage_guide.md 学习使用方法")
        print("   3. 运行 code/integration_examples/demo.py 体验功能")
        print("   4. 参考 code/ 目录下的代码实现")
    else:
        print("⚠️ 案例验证失败，请检查相关文件。")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
