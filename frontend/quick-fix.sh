#!/bin/bash

# 诺亚的快速修复脚本 - 批量删除未使用的导入和变量

echo "🔧 开始批量修复未使用的导入和变量..."

# 修复 CollectionManagementEnhanced.tsx
echo "修复 CollectionManagementEnhanced.tsx..."
sed -i '' '/Form,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/Input,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/InputNumber,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/Statistic,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/Spin,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/PlusOutlined,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/SettingOutlined,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/FileTextOutlined,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/CheckCircleOutlined,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' '/ExclamationCircleOutlined,/d' src/pages/rag/CollectionManagementEnhanced.tsx
sed -i '' 's/const { Title, Paragraph, Text } = Typography;/const { Text } = Typography;/' src/pages/rag/CollectionManagementEnhanced.tsx

# 修复 DocumentManagementEnhanced.tsx
echo "修复 DocumentManagementEnhanced.tsx..."
sed -i '' '/Progress,/d' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' '/Alert,/d' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' '/Badge,/d' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' '/Divider,/d' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' '/InfoCircleOutlined,/d' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' 's/const { Title, Paragraph, Text } = Typography;/const { Text } = Typography;/' src/pages/rag/DocumentManagementEnhanced.tsx
sed -i '' '/const { TabPane } = Tabs;/d' src/pages/rag/DocumentManagementEnhanced.tsx

# 修复 RAGCoreFeatures.tsx
echo "修复 RAGCoreFeatures.tsx..."
sed -i '' '/Table,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' '/Progress,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' '/Upload,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' '/Modal,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' '/SettingOutlined,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' '/UploadOutlined,/d' src/pages/rag/RAGCoreFeatures.tsx
sed -i '' 's/const { Title, Paragraph, Text } = Typography;/const { Text } = Typography;/' src/pages/rag/RAGCoreFeatures.tsx

# 修复 ProjectManagement.tsx
echo "修复 ProjectManagement.tsx..."
sed -i '' '/Statistic,/d' src/pages/system/ProjectManagement.tsx
sed -i '' '/StarOutlined,/d' src/pages/system/ProjectManagement.tsx

# 修复 ProjectTest.tsx
echo "修复 ProjectTest.tsx..."
sed -i '' 's/projects.map((project, index) =>/projects.map((project) =>/' src/pages/test/ProjectTest.tsx

echo "✅ 批量修复完成！"
