import React, { useState } from 'react';
import { Button, Card, Typography, Space } from 'antd';
import { SystemAPI } from '../../api/system';
import { request } from '../../utils/request';

const { Title, Paragraph } = Typography;

const ApiTest: React.FC = () => {
  const [results, setResults] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const testDirectRequest = async () => {
    try {
      console.log('🧪 [ApiTest] 测试直接request调用...');
      localStorage.setItem('token', 'test-token-for-development');

      const response = await request.get('/v1/system/projects', {
        params: { page: 1, page_size: 20 }
      });

      console.log('🧪 [ApiTest] 直接request响应:', response);
      setResults((prev: any) => ({ ...prev, directRequest: response }));

    } catch (error) {
      console.error('🧪 [ApiTest] 直接request失败:', error);
      setResults((prev: any) => ({ ...prev, directRequestError: error }));
    }
  };

  const testSystemAPI = async () => {
    try {
      console.log('🧪 [ApiTest] 测试SystemAPI调用...');
      localStorage.setItem('token', 'test-token-for-development');

      const response = await SystemAPI.getProjectList({
        page: 1,
        page_size: 20,
      });

      console.log('🧪 [ApiTest] SystemAPI响应:', response);
      setResults((prev: any) => ({ ...prev, systemAPI: response }));

    } catch (error) {
      console.error('🧪 [ApiTest] SystemAPI失败:', error);
      setResults((prev: any) => ({ ...prev, systemAPIError: error }));
    }
  };

  const runAllTests = async () => {
    setLoading(true);
    setResults({});

    await testDirectRequest();
    await testSystemAPI();

    setLoading(false);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3}>API数据流测试</Title>

        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            onClick={runAllTests}
            loading={loading}
          >
            运行所有测试
          </Button>

          <Button onClick={testDirectRequest}>
            测试直接request调用
          </Button>

          <Button onClick={testSystemAPI}>
            测试SystemAPI调用
          </Button>

          <div>
            <Title level={4}>测试结果：</Title>
            <Paragraph>
              <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', maxHeight: '400px', overflow: 'auto' }}>
                {JSON.stringify(results, null, 2)}
              </pre>
            </Paragraph>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ApiTest;
