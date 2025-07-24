#!/usr/bin/env node

/**
 * 批量修复未使用的导入和变量
 * 诺亚的快速修复脚本
 */

const fs = require('fs');
const path = require('path');

// 需要修复的文件和对应的修复规则
const fixes = [
  // CollectionManagementEnhanced.tsx
  {
    file: 'src/pages/rag/CollectionManagementEnhanced.tsx',
    fixes: [
      {
        search: /import\s*{\s*([^}]*Form[^}]*)\s*}\s*from\s*'antd';/,
        replace: (match, imports) => {
          const cleanImports = imports
            .split(',')
            .map(imp => imp.trim())
            .filter(imp => !['Form', 'Input', 'InputNumber', 'Statistic', 'Spin'].includes(imp))
            .join(',\n  ');
          return `import {\n  ${cleanImports}\n} from 'antd';`;
        }
      },
      {
        search: /import\s*{\s*([^}]*PlusOutlined[^}]*)\s*}\s*from\s*'@ant-design\/icons';/,
        replace: (match, imports) => {
          const cleanImports = imports
            .split(',')
            .map(imp => imp.trim())
            .filter(imp => !['PlusOutlined', 'SettingOutlined', 'FileTextOutlined', 'CheckCircleOutlined', 'ExclamationCircleOutlined'].includes(imp))
            .join(',\n  ');
          return `import {\n  ${cleanImports}\n} from '@ant-design/icons';`;
        }
      },
      {
        search: /const\s*{\s*Title,\s*Paragraph,\s*Text\s*}\s*=\s*Typography;/,
        replace: 'const { Text } = Typography;'
      }
    ]
  }
];

// 执行修复
fixes.forEach(({ file, fixes: fileFixes }) => {
  const filePath = path.join(__dirname, file);

  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  文件不存在: ${file}`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  fileFixes.forEach(fix => {
    if (typeof fix.replace === 'function') {
      content = content.replace(fix.search, fix.replace);
    } else {
      content = content.replace(fix.search, fix.replace);
    }
  });

  fs.writeFileSync(filePath, content);
  console.log(`✅ 修复完成: ${file}`);
});

console.log('🎉 批量修复完成！');
