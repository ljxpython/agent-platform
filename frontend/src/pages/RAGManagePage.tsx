import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Upload,
  message,
  Space,
  Tag,
  Popconfirm,
  Tabs,
  Statistic,
  Row,
  Col,
  Typography,
  Divider,
  Progress,
  List,
  Avatar,
} from 'antd';
import {
  DatabaseOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  FileTextOutlined,
  BarChartOutlined,
  SearchOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import PageLayout from '@/components/PageLayout';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

interface Collection {
  name: string;
  description: string;
  business_type: string;
  document_count?: number;
  last_updated?: string;
  status?: 'active' | 'inactive';
}

interface Document {
  id: string;
  title: string;
  content: string;
  metadata: any;
  created_at: string;
  collection_name: string;
}

const RAGManagePage: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [collectionModalVisible, setCollectionModalVisible] = useState(false);
  const [documentModalVisible, setDocumentModalVisible] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [ragStats, setRagStats] = useState<any>(null);
  const [form] = Form.useForm();
  const [documentForm] = Form.useForm();

  useEffect(() => {
    loadCollections();
    loadRAGStats();
  }, []);

  useEffect(() => {
    if (selectedCollection) {
      loadDocuments(selectedCollection);
    }
  }, [selectedCollection]);

  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/rag/collections');
      const data = await response.json();
      if (data.success) {
        const collectionsData = Object.entries(data.data.collections).map(([name, info]: [string, any]) => ({
          name,
          description: info.description || '',
          business_type: info.business_type || 'general',
          document_count: info.document_count || 0,
          last_updated: info.last_updated || new Date().toISOString(),
          status: info.remote_connected ? 'active' : 'inactive',
        }));
        setCollections(collectionsData);
        if (collectionsData.length > 0 && !selectedCollection) {
          setSelectedCollection(collectionsData[0].name);
        }
      }
    } catch (error) {
      message.error('加载Collections失败');
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async (collectionName: string) => {
    setLoading(true);
    try {
      // 这里需要后端提供文档列表API
      const response = await fetch(`/api/v1/rag/collections/${collectionName}/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('加载文档失败:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadRAGStats = async () => {
    try {
      const response = await fetch('/api/v1/rag/stats');
      const data = await response.json();
      if (data.success) {
        setRagStats(data.data);
      }
    } catch (error) {
      console.error('加载RAG统计失败:', error);
    }
  };

  const handleCreateCollection = async (values: any) => {
    try {
      const response = await fetch('/api/v1/rag/collections/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const result = await response.json();
      if (result.success) {
        message.success('Collection创建成功');
        setCollectionModalVisible(false);
        form.resetFields();
        loadCollections();
      } else {
        message.error(result.message || 'Collection创建失败');
      }
    } catch (error) {
      message.error('Collection创建失败');
    }
  };

  const handleDeleteCollection = async (collectionName: string) => {
    try {
      const response = await fetch(`/api/v1/rag/collections/${collectionName}`, {
        method: 'DELETE',
      });
      const result = await response.json();
      if (result.success) {
        message.success('Collection删除成功');
        loadCollections();
        if (selectedCollection === collectionName) {
          setSelectedCollection('');
        }
      } else {
        message.error(result.message || 'Collection删除失败');
      }
    } catch (error) {
      message.error('Collection删除失败');
    }
  };

  const handleUploadFiles = async (fileList: any[]) => {
    if (!selectedCollection) {
      message.error('请先选择Collection');
      return;
    }

    const formData = new FormData();
    fileList.forEach(file => {
      formData.append('files', file.originFileObj);
    });
    formData.append('collection_name', selectedCollection);

    try {
      const response = await fetch('/api/v1/rag/documents/add-file', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (result.success) {
        message.success('文件上传成功');
        setUploadModalVisible(false);
        loadDocuments(selectedCollection);
        loadCollections(); // 刷新统计信息
      } else {
        message.error(result.message || '文件上传失败');
      }
    } catch (error) {
      message.error('文件上传失败');
    }
  };

  const collectionColumns = [
    {
      title: 'Collection名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Collection) => (
        <Space>
          <DatabaseOutlined style={{ color: record.status === 'active' ? '#52c41a' : '#ff4d4f' }} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '业务类型',
      dataIndex: 'business_type',
      key: 'business_type',
      render: (type: string) => {
        const colors = {
          general: 'blue',
          testcase: 'green',
          ui_testing: 'orange',
          ai_chat: 'purple',
        };
        return <Tag color={colors[type as keyof typeof colors] || 'default'}>{type}</Tag>;
      },
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      render: (count: number) => <Text>{count || 0}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '活跃' : '离线'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: Collection) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingCollection(record);
              form.setFieldsValue(record);
              setCollectionModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个Collection吗？"
            onConfirm={() => handleDeleteCollection(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>
            <DatabaseOutlined style={{ marginRight: '8px' }} />
            RAG知识库管理
          </Title>
          <Paragraph type="secondary">
            管理RAG知识库的Collections和文档，支持多业务场景的专业知识库
          </Paragraph>
        </div>

        <Tabs defaultActiveKey="collections" size="large">
          <TabPane tab="Collections管理" key="collections">
            <Card>
              <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      setEditingCollection(null);
                      form.resetFields();
                      setCollectionModalVisible(true);
                    }}
                  >
                    创建Collection
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={loadCollections}>
                    刷新
                  </Button>
                </Space>
                <Button
                  icon={<UploadOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                  disabled={!selectedCollection}
                >
                  上传文档
                </Button>
              </div>

              <Table
                columns={collectionColumns}
                dataSource={collections}
                rowKey="name"
                loading={loading}
                onRow={(record) => ({
                  onClick: () => setSelectedCollection(record.name),
                  style: {
                    backgroundColor: selectedCollection === record.name ? '#f0f8ff' : undefined,
                    cursor: 'pointer',
                  },
                })}
              />
            </Card>
          </TabPane>

          <TabPane tab="文档管理" key="documents" disabled={!selectedCollection}>
            <Card title={`${selectedCollection} - 文档列表`}>
              <List
                loading={loading}
                dataSource={documents}
                renderItem={(doc) => (
                  <List.Item
                    actions={[
                      <Button type="link" icon={<EditOutlined />}>编辑</Button>,
                      <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<Avatar icon={<FileTextOutlined />} />}
                      title={doc.title || doc.id}
                      description={
                        <div>
                          <Text type="secondary">{doc.content.substring(0, 100)}...</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            创建时间: {new Date(doc.created_at).toLocaleString()}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </TabPane>

          <TabPane tab="系统统计" key="stats">
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总Collections"
                    value={ragStats?.total_collections || 0}
                    prefix={<DatabaseOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="活跃Collections"
                    value={collections.filter(c => c.status === 'active').length}
                    prefix={<BarChartOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总文档数"
                    value={collections.reduce((sum, c) => sum + (c.document_count || 0), 0)}
                    prefix={<FileTextOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="系统状态"
                    value={ragStats?.initialized ? "正常" : "异常"}
                    valueStyle={{ color: ragStats?.initialized ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>

            {ragStats && (
              <Card title="详细统计" style={{ marginTop: '16px' }}>
                <Row gutter={[16, 16]}>
                  {Object.entries(ragStats.collections || {}).map(([name, stats]: [string, any]) => (
                    <Col span={12} key={name}>
                      <Card size="small" title={name}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text>连接状态: </Text>
                            <Tag color={stats.vector_db?.remote_connected ? 'green' : 'red'}>
                              {stats.vector_db?.remote_connected ? '已连接' : '未连接'}
                            </Tag>
                          </div>
                          <div>
                            <Text>业务类型: </Text>
                            <Tag>{stats.business_type}</Tag>
                          </div>
                          <div>
                            <Text>向量维度: </Text>
                            <Text code>{stats.vector_db?.dimension}</Text>
                          </div>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            )}
          </TabPane>
        </Tabs>

        {/* Collection创建/编辑模态框 */}
        <Modal
          title={editingCollection ? '编辑Collection' : '创建Collection'}
          open={collectionModalVisible}
          onCancel={() => setCollectionModalVisible(false)}
          footer={null}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateCollection}
          >
            <Form.Item
              name="name"
              label="Collection名称"
              rules={[{ required: true, message: '请输入Collection名称' }]}
            >
              <Input placeholder="例如: my_knowledge_base" disabled={!!editingCollection} />
            </Form.Item>
            <Form.Item
              name="description"
              label="描述"
              rules={[{ required: true, message: '请输入描述' }]}
            >
              <TextArea rows={3} placeholder="描述这个知识库的用途" />
            </Form.Item>
            <Form.Item
              name="business_type"
              label="业务类型"
              rules={[{ required: true, message: '请选择业务类型' }]}
            >
              <Select placeholder="选择业务类型">
                <Option value="general">通用知识</Option>
                <Option value="testcase">测试用例</Option>
                <Option value="ui_testing">UI测试</Option>
                <Option value="ai_chat">AI对话</Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  {editingCollection ? '更新' : '创建'}
                </Button>
                <Button onClick={() => setCollectionModalVisible(false)}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* 文件上传模态框 */}
        <Modal
          title="上传文档"
          open={uploadModalVisible}
          onCancel={() => setUploadModalVisible(false)}
          footer={null}
          width={600}
        >
          <div style={{ padding: '20px 0' }}>
            <div style={{ marginBottom: '16px' }}>
              <Text strong>目标Collection: </Text>
              <Tag color="blue">{selectedCollection}</Tag>
            </div>
            <Upload.Dragger
              multiple
              beforeUpload={() => false}
              onChange={({ fileList }) => {
                if (fileList.length > 0) {
                  handleUploadFiles(fileList);
                }
              }}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个或批量上传。支持常见文档格式：PDF、Word、TXT等
              </p>
            </Upload.Dragger>
          </div>
        </Modal>
      </div>
    </PageLayout>
  );
};

export default RAGManagePage;
