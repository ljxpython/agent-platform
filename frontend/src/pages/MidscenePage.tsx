import React, { useState } from 'react';
import { Layout, Typography, Card, Tabs, TabsProps } from 'antd';
import { InfoCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import UITestIntroPage from './UITestIntroPage';
import UITestExecutePage from './UITestExecutePage';

const { Content } = Layout;
const { Title } = Typography;

const MidscenePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('intro');

  // 监听切换到执行页面的事件
  React.useEffect(() => {
    const handleSwitchToExecute = () => {
      setActiveTab('execute');
    };

    window.addEventListener('switchToExecute', handleSwitchToExecute);
    return () => {
      window.removeEventListener('switchToExecute', handleSwitchToExecute);
    };
  }, []);

  const tabItems: TabsProps['items'] = [
    {
      key: 'intro',
      label: (
        <span>
          <InfoCircleOutlined />
          功能介绍
        </span>
      ),
      children: <UITestIntroPage />,
    },
    {
      key: 'execute',
      label: (
        <span>
          <PlayCircleOutlined />
          开始使用
        </span>
      ),
      children: <UITestExecutePage />,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* 页面标题 */}
          <Card
            style={{
              marginBottom: 24,
              borderRadius: 12,
              background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
              border: 'none'
            }}
            styles={{ body: { padding: '24px 32px' } }}
          >
            <div style={{ display: 'flex', alignItems: 'center', color: 'white' }}>
              <span style={{ fontSize: 32, marginRight: 16 }}>🤖</span>
              <div>
                <Title level={2} style={{ color: 'white', margin: 0, marginBottom: 8 }}>
                  Midscene智能体系统
                </Title>
                <p style={{ color: 'rgba(255,255,255,0.9)', margin: 0, fontSize: 16 }}>
                  基于AI的UI自动化测试脚本生成平台，四智能体协作生成Midscene.js测试脚本
                </p>
              </div>
            </div>
          </Card>

          {/* 功能标签页 */}
          <Card
            style={{
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: 'none'
            }}
            styles={{ body: { padding: 0 } }}
          >
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
              size="large"
              style={{
                minHeight: 'calc(100vh - 200px)'
              }}
              tabBarStyle={{
                marginBottom: 0,
                borderBottom: '1px solid #f0f0f0',
                paddingLeft: 24,
                paddingRight: 24,
                paddingTop: 16
              }}
            />
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default MidscenePage;
