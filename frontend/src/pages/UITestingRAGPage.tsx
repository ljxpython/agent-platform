/**
 * 基于RAG的UI测试查询页面
 * 支持从知识库检索UI测试经验并生成测试方案
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  Input,
  Button,
  Select,
  Form,
  message,
  List,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  Collapse,
  Divider,
  Empty,
} from 'antd';
import {
  SearchOutlined,
  BulbOutlined,
  FileTextOutlined,
  RobotOutlined,
  HistoryOutlined,
} from '@ant-design/icons';

import {
  queryUITestingWithRAG,
  getUITestingCollections,
  type CollectionInfo,
  type UITestingQueryRequest,
} from '../api/ui-testing';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface QueryResult {
  conversation_id: string;
  rag_answer: string;
  retrieved_docs: any[];
  user_requirement: string;
  collection_name: string;
}

interface QueryHistory {
  id: string;
  requirement: string;
  collection: string;
  timestamp: Date;
  result?: QueryResult;
}

const UITestingRAGPage: React.FC = () => {
  const [form] = Form.useForm();
  const [querying, setQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [loadingCollections, setLoadingCollections] = useState(false);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);

  // 加载Collection列表
  const loadCollections = useCallback(async () => {
    setLoadingCollections(true);
    try {
      const response = await getUITestingCollections();
      if (response.code === 200) {
        setCollections(response.data.collections);
      } else {
        message.error('加载Collection列表失败');
      }
    } catch (error) {
      console.error('加载Collection列表失败:', error);
      message.error('加载Collection列表失败');
    } finally {
      setLoadingCollections(false);
    }
  }, []);

  // 组件挂载时加载Collection列表
  React.useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  // 执行RAG查询
  const handleQuery = async () => {
    try {
      const values = await form.validateFields();

      setQuerying(true);
      setQueryResult(null);

      const queryRequest: UITestingQueryRequest = {
        user_requirement: values.userRequirement,
        collection_name: values.collectionName || 'ui_testing',
        user_id: 'current_user',
      };

      const response = await queryUITestingWithRAG(queryRequest);

      if (response.code === 200) {
        setQueryResult(response.data);

        // 添加到查询历史
        const historyItem: QueryHistory = {
          id: response.data.conversation_id,
          requirement: values.userRequirement,
          collection: values.collectionName || 'ui_testing',
          timestamp: new Date(),
          result: response.data,
        };
        setQueryHistory(prev => [historyItem, ...prev.slice(0, 9)]); // 保留最近10条

        message.success('查询完成');
      } else {
        throw new Error(response.msg || '查询失败');
      }
    } catch (error) {
      console.error('RAG查询失败:', error);
      message.error(`查询失败: ${error.message}`);
    } finally {
      setQuerying(false);
    }
  };

  // 使用历史查询
  const useHistoryQuery = (historyItem: QueryHistory) => {
    form.setFieldsValue({
      userRequirement: historyItem.requirement,
      collectionName: historyItem.collection,
    });
    if (historyItem.result) {
      setQueryResult(historyItem.result);
    }
  };

  // 格式化检索文档
  const formatRetrievedDoc = (doc: any, index: number) => {
    const content = doc.content || doc.text || '';
    const score = doc.score || doc.similarity || 0;
    const metadata = doc.metadata || {};

    return (
      <Card
        key={index}
        size="small"
        title={
          <Space>
            <FileTextOutlined />
            <Text strong>相关文档 {index + 1}</Text>
            <Tag color="blue">相似度: {(score * 100).toFixed(1)}%</Tag>
          </Space>
        }
        style={{ marginBottom: 12 }}
      >
        <Paragraph ellipsis={{ rows: 3, expandable: true }}>
          {content.substring(0, 300)}
        </Paragraph>
        {metadata.type && (
          <div style={{ marginTop: 8 }}>
            <Tag color="green">{metadata.type}</Tag>
            {metadata.agent && <Tag color="orange">{metadata.agent}</Tag>}
            {metadata.timestamp && (
              <Tag color="default">
                {new Date(metadata.timestamp).toLocaleDateString()}
              </Tag>
            )}
          </div>
        )}
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Title level={2}>
        <RobotOutlined /> UI测试智能助手
      </Title>
      <Paragraph>
        基于RAG知识库的UI测试查询，从已有的UI分析经验中获取相关信息，生成测试建议和方案。
      </Paragraph>

      <Row gutter={24}>
        <Col span={8}>
          <Card title="查询配置" style={{ marginBottom: 24 }}>
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                collectionName: 'ui_testing',
              }}
            >
              <Form.Item
                name="userRequirement"
                label="测试需求描述"
                rules={[{ required: true, message: '请描述您的测试需求' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="请详细描述您的UI测试需求，例如：
• 如何测试登录表单的验证逻辑？
• 购物车功能的自动化测试方案
• 响应式布局的测试策略
• 表单提交流程的测试用例设计"
                />
              </Form.Item>

              <Form.Item
                name="collectionName"
                label="查询知识库"
                rules={[{ required: true, message: '请选择查询的知识库' }]}
              >
                <Select
                  placeholder="选择要查询的知识库"
                  loading={loadingCollections}
                  onDropdownVisibleChange={(open) => {
                    if (open && collections.length === 0) {
                      loadCollections();
                    }
                  }}
                >
                  {collections.map(collection => (
                    <Option key={collection.name} value={collection.name}>
                      <Space>
                        <span>{collection.display_name}</span>
                        <Tag color="blue">{collection.document_count} 文档</Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleQuery}
                  loading={querying}
                  block
                >
                  智能查询
                </Button>
              </Form.Item>
            </Form>
          </Card>

          {/* 查询历史 */}
          {queryHistory.length > 0 && (
            <Card title={<><HistoryOutlined /> 查询历史</>} size="small">
              <List
                size="small"
                dataSource={queryHistory}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        size="small"
                        onClick={() => useHistoryQuery(item)}
                      >
                        使用
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Text ellipsis style={{ maxWidth: 200 }}>
                          {item.requirement}
                        </Text>
                      }
                      description={
                        <Space>
                          <Tag size="small">{item.collection}</Tag>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {item.timestamp.toLocaleString()}
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </Col>

        <Col span={16}>
          {queryResult ? (
            <div>
              <Card
                title={
                  <Space>
                    <BulbOutlined />
                    <span>AI分析结果</span>
                    <Tag color="green">来自 {queryResult.collection_name}</Tag>
                  </Space>
                }
                style={{ marginBottom: 24 }}
              >
                <Alert
                  message="基于知识库的智能回答"
                  description={queryResult.rag_answer}
                  type="success"
                  showIcon
                />
              </Card>

              {queryResult.retrieved_docs && queryResult.retrieved_docs.length > 0 && (
                <Card title="相关参考文档" style={{ marginBottom: 24 }}>
                  <Collapse ghost>
                    <Panel
                      header={
                        <Space>
                          <FileTextOutlined />
                          <span>检索到 {queryResult.retrieved_docs.length} 个相关文档</span>
                        </Space>
                      }
                      key="docs"
                    >
                      {queryResult.retrieved_docs.map((doc, index) =>
                        formatRetrievedDoc(doc, index)
                      )}
                    </Panel>
                  </Collapse>
                </Card>
              )}

              <Card title="查询信息" size="small">
                <Row gutter={16}>
                  <Col span={12}>
                    <Text type="secondary">查询需求：</Text>
                    <Paragraph>{queryResult.user_requirement}</Paragraph>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">知识库：</Text>
                    <div>
                      <Tag color="blue">{queryResult.collection_name}</Tag>
                    </div>
                    <Text type="secondary">对话ID：</Text>
                    <div>
                      <Text code>{queryResult.conversation_id}</Text>
                    </div>
                  </Col>
                </Row>
              </Card>
            </div>
          ) : (
            <Card style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="请在左侧输入测试需求并点击查询"
              />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default UITestingRAGPage;
