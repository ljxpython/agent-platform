import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Tabs,
  Form,
  Input,
  Select,
  message,
  Tag,
  Descriptions,
  Alert,
  Statistic,
  Spin,
} from 'antd';
import {
  DatabaseOutlined,
  FileTextOutlined,
  SearchOutlined,
  MessageOutlined,
  InfoCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import PageLayout from '../../components/PageLayout';

const { Text } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

interface QueryResult {
  success: boolean;
  query: string;
  answer: string;
  collection_name: string;
  project_id: string;
  response_time: number;
  retrieved_count: number;
  retrieved_nodes: Array<{
    text: string;
    score: number;
    metadata: any;
  }>;
}

interface SystemStats {
  project_id: string;
  project_collections: string[];
  project_collection_count: number;
  core_stats: any;
}

const RAGCoreFeatures: React.FC = () => {
  // 状态管理
  const [projectId, setProjectId] = useState<string>('default');
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('general');
  const [loading, setLoading] = useState(false);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);

  // 查询相关
  const [queryForm] = Form.useForm();
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  // 文档添加相关
  const [addTextForm] = Form.useForm();
  const [addTextLoading, setAddTextLoading] = useState(false);

  // 聊天相关
  const [chatForm] = Form.useForm();
  const [chatHistory, setChatHistory] = useState<Array<{question: string, answer: string, timestamp: string}>>([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    loadSystemStats();
  }, [projectId]);

  // 加载系统统计信息
  const loadSystemStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/system/stats?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setSystemStats(data.data);
          setCollections(data.data.project_collections || []);
          if (data.data.project_collections?.length > 0) {
            setSelectedCollection(data.data.project_collections[0]);
          }
        }
      }
    } catch (error) {
      console.error('加载系统统计失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // RAG查询
  const handleQuery = async (values: any) => {
    setQueryLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/query?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: values.question,
          collection_name: values.collection_name || selectedCollection,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setQueryResult(data.data);
          message.success('查询成功');
        } else {
          message.error(data.msg || '查询失败');
        }
      } else {
        message.error('查询失败');
      }
    } catch (error) {
      console.error('查询异常:', error);
      message.error('查询失败');
    } finally {
      setQueryLoading(false);
    }
  };

  // 添加文本
  const handleAddText = async (values: any) => {
    setAddTextLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/documents/add-text?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: values.text,
          collection_name: values.collection_name || selectedCollection,
          metadata: values.metadata ? JSON.parse(values.metadata) : {},
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          message.success('文本添加成功');
          addTextForm.resetFields();
          loadSystemStats(); // 重新加载统计信息
        } else {
          message.error(data.msg || '添加失败');
        }
      } else {
        message.error('添加失败');
      }
    } catch (error) {
      console.error('添加文本异常:', error);
      message.error('添加失败');
    } finally {
      setAddTextLoading(false);
    }
  };

  // RAG聊天
  const handleChat = async (values: any) => {
    setChatLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/chat?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: values.message,
          collection_name: values.collection_name || selectedCollection,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          const newChat = {
            question: values.message,
            answer: data.data.answer,
            timestamp: new Date().toLocaleTimeString(),
          };
          setChatHistory(prev => [...prev, newChat]);
          chatForm.resetFields();
          message.success('聊天成功');
        } else {
          message.error(data.msg || '聊天失败');
        }
      } else {
        message.error('聊天失败');
      }
    } catch (error) {
      console.error('聊天异常:', error);
      message.error('聊天失败');
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <PageLayout
      title="RAG核心功能"
      description="基于backend/rag_core的完整RAG功能展示，包括查询、文档管理、聊天等"
    >
      <Row gutter={[16, 16]}>
        {/* 项目选择和统计信息 */}
        <Col span={24}>
          <Card>
            <Row gutter={16}>
              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>当前项目:</Text>
                  <Select
                    value={projectId}
                    onChange={setProjectId}
                    style={{ width: '100%' }}
                  >
                    <Option value="default">默认项目</Option>
                    <Option value="project1">项目1</Option>
                    <Option value="project2">项目2</Option>
                  </Select>
                </Space>
              </Col>
              <Col span={6}>
                <Statistic
                  title="Collections数量"
                  value={systemStats?.project_collection_count || 0}
                  prefix={<DatabaseOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="当前Collection"
                  value={selectedCollection}
                  prefix={<FileTextOutlined />}
                />
              </Col>
              <Col span={6}>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadSystemStats}
                  loading={loading}
                  style={{ marginTop: 24 }}
                >
                  刷新统计
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 主要功能标签页 */}
        <Col span={24}>
          <Card>
            <Tabs defaultActiveKey="query">
              {/* RAG查询 */}
              <TabPane
                tab={
                  <span>
                    <SearchOutlined />
                    RAG查询
                  </span>
                }
                key="query"
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Card title="查询输入" size="small">
                      <Form
                        form={queryForm}
                        layout="vertical"
                        onFinish={handleQuery}
                      >
                        <Form.Item
                          name="question"
                          label="查询问题"
                          rules={[{ required: true, message: '请输入查询问题' }]}
                        >
                          <TextArea rows={4} placeholder="请输入您的问题..." />
                        </Form.Item>
                        <Form.Item name="collection_name" label="Collection">
                          <Select value={selectedCollection} onChange={setSelectedCollection}>
                            {collections.map(col => (
                              <Option key={col} value={col}>{col}</Option>
                            ))}
                          </Select>
                        </Form.Item>
                        <Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            loading={queryLoading}
                            icon={<PlayCircleOutlined />}
                          >
                            执行查询
                          </Button>
                        </Form.Item>
                      </Form>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="查询结果" size="small">
                      {queryResult ? (
                        <div>
                          <Descriptions size="small" column={1}>
                            <Descriptions.Item label="问题">{queryResult.query}</Descriptions.Item>
                            <Descriptions.Item label="回答">
                              <Text>{queryResult.answer}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="响应时间">
                              {queryResult.response_time}ms
                            </Descriptions.Item>
                            <Descriptions.Item label="检索文档数">
                              {queryResult.retrieved_count}
                            </Descriptions.Item>
                          </Descriptions>

                          {queryResult.retrieved_nodes && queryResult.retrieved_nodes.length > 0 && (
                            <div style={{ marginTop: 16 }}>
                              <Text strong>检索到的文档片段:</Text>
                              {queryResult.retrieved_nodes.map((node, index) => (
                                <Card key={index} size="small" style={{ marginTop: 8 }}>
                                  <Text>{node.text}</Text>
                                  <div style={{ marginTop: 4 }}>
                                    <Tag color="blue">相似度: {node.score.toFixed(3)}</Tag>
                                  </div>
                                </Card>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <Alert message="请执行查询以查看结果" type="info" />
                      )}
                    </Card>
                  </Col>
                </Row>
              </TabPane>

              {/* 文档添加 */}
              <TabPane
                tab={
                  <span>
                    <FileTextOutlined />
                    文档添加
                  </span>
                }
                key="add-text"
              >
                <Card title="添加文本到知识库">
                  <Form
                    form={addTextForm}
                    layout="vertical"
                    onFinish={handleAddText}
                  >
                    <Row gutter={16}>
                      <Col span={16}>
                        <Form.Item
                          name="text"
                          label="文本内容"
                          rules={[{ required: true, message: '请输入文本内容' }]}
                        >
                          <TextArea rows={8} placeholder="请输入要添加到知识库的文本内容..." />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item name="collection_name" label="目标Collection">
                          <Select value={selectedCollection} onChange={setSelectedCollection}>
                            {collections.map(col => (
                              <Option key={col} value={col}>{col}</Option>
                            ))}
                          </Select>
                        </Form.Item>
                        <Form.Item name="metadata" label="元数据 (JSON格式)">
                          <TextArea
                            rows={4}
                            placeholder='{"source": "manual", "topic": "example"}'
                          />
                        </Form.Item>
                        <Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            loading={addTextLoading}
                            icon={<CloudUploadOutlined />}
                            block
                          >
                            添加到知识库
                          </Button>
                        </Form.Item>
                      </Col>
                    </Row>
                  </Form>
                </Card>
              </TabPane>

              {/* RAG聊天 */}
              <TabPane
                tab={
                  <span>
                    <MessageOutlined />
                    RAG聊天
                  </span>
                }
                key="chat"
              >
                <Row gutter={16}>
                  <Col span={16}>
                    <Card title="聊天历史" style={{ height: 500, overflow: 'auto' }}>
                      {chatHistory.length === 0 ? (
                        <Alert message="开始与RAG系统聊天吧！" type="info" />
                      ) : (
                        chatHistory.map((chat, index) => (
                          <div key={index} style={{ marginBottom: 16 }}>
                            <Card size="small">
                              <Text strong>问: </Text>
                              <Text>{chat.question}</Text>
                              <br />
                              <Text strong>答: </Text>
                              <Text>{chat.answer}</Text>
                              <div style={{ textAlign: 'right', marginTop: 8 }}>
                                <Text type="secondary">{chat.timestamp}</Text>
                              </div>
                            </Card>
                          </div>
                        ))
                      )}
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card title="发送消息">
                      <Form
                        form={chatForm}
                        layout="vertical"
                        onFinish={handleChat}
                      >
                        <Form.Item name="collection_name" label="Collection">
                          <Select value={selectedCollection} onChange={setSelectedCollection}>
                            {collections.map(col => (
                              <Option key={col} value={col}>{col}</Option>
                            ))}
                          </Select>
                        </Form.Item>
                        <Form.Item
                          name="message"
                          label="消息"
                          rules={[{ required: true, message: '请输入消息' }]}
                        >
                          <TextArea rows={4} placeholder="请输入您的消息..." />
                        </Form.Item>
                        <Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            loading={chatLoading}
                            icon={<MessageOutlined />}
                            block
                          >
                            发送消息
                          </Button>
                        </Form.Item>
                      </Form>
                    </Card>
                  </Col>
                </Row>
              </TabPane>

              {/* 系统信息 */}
              <TabPane
                tab={
                  <span>
                    <InfoCircleOutlined />
                    系统信息
                  </span>
                }
                key="system"
              >
                <Card title="系统统计信息">
                  {systemStats ? (
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="项目ID">{systemStats.project_id}</Descriptions.Item>
                      <Descriptions.Item label="Collections数量">{systemStats.project_collection_count}</Descriptions.Item>
                      <Descriptions.Item label="可用Collections" span={2}>
                        <Space wrap>
                          {systemStats.project_collections.map(col => (
                            <Tag key={col} color="blue">{col}</Tag>
                          ))}
                        </Space>
                      </Descriptions.Item>
                      <Descriptions.Item label="核心统计" span={2}>
                        <pre>{JSON.stringify(systemStats.core_stats, null, 2)}</pre>
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Spin tip="加载中...">
                      <div style={{ height: 200 }} />
                    </Spin>
                  )}
                </Card>
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </PageLayout>
  );
};

export default RAGCoreFeatures;
