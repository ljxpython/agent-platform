import React, { useState, useEffect } from 'react';
import { Button, Card, Typography, Space, message } from 'antd';
import { SystemAPI } from '../../api/system';

const { Title, Text, Paragraph } = Typography;

const ProjectTest: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const testAPI = async () => {
    setLoading(true);
    try {
      // 设置测试token
      localStorage.setItem('token', 'test-token-for-development');

      console.log('🧪 [ProjectTest] 开始测试API...');
      const result = await SystemAPI.getProjectList({
        page: 1,
        page_size: 20,
      });

      console.log('🧪 [ProjectTest] API响应:', result);
      setResponse(result);

      if (result && result.code === 200) {
        setProjects(result.data || []);
        message.success('API测试成功！');
      } else {
        message.error('API测试失败');
      }
    } catch (error) {
      console.error('🧪 [ProjectTest] API测试失败:', error);
      message.error('API测试失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testAPI();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3}>项目管理API测试</Title>

        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            onClick={testAPI}
            loading={loading}
          >
            重新测试API
          </Button>

          <div>
            <Title level={4}>API响应数据：</Title>
            <Paragraph>
              <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {JSON.stringify(response, null, 2)}
              </pre>
            </Paragraph>
          </div>

          <div>
            <Title level={4}>解析后的项目列表：</Title>
            {projects.length > 0 ? (
              projects.map((project) => (
                <Card key={project.id} size="small" style={{ marginBottom: '8px' }}>
                  <Text strong>{project.display_name}</Text> ({project.name})
                  <br />
                  <Text type="secondary">{project.description || '无描述'}</Text>
                  <br />
                  <Text>状态: {project.is_active ? '激活' : '停用'}</Text>
                  {project.is_default && <Text type="warning"> [默认项目]</Text>}
                </Card>
              ))
            ) : (
              <Text type="secondary">暂无项目数据</Text>
            )}
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ProjectTest;
