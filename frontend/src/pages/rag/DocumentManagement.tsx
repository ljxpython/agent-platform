import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  Space,
  Tag,
  Progress,
  message,
  Tabs,
  Typography,
  Row,
  Col,
  Statistic,
  Popconfirm,
  Tooltip,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
  EditOutlined,
  CloudUploadOutlined,
  SyncOutlined,
  DatabaseOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import PageLayout from '@/components/PageLayout';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

interface Document {
  id: string;
  title: string;
  content: string;
  file_path?: string;
  file_type: string;
  file_size: number;
  collection_name: string;
  node_count: number;
  embedding_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  metadata: any;
}

interface ProcessingJob {
  id: string;
  file_name: string;
  collection_name: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  error_message?: string;
}

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>([]);
  const [collections, setCollections] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [textModalVisible, setTextModalVisible] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [form] = Form.useForm();
  const [textForm] = Form.useForm();

  useEffect(() => {
    loadDocuments();
    loadCollections();
    loadProcessingJobs();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/rag/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadCollections = async () => {
    try {
      const response = await fetch('/api/v1/rag/collections');
      if (response.ok) {
        const data = await response.json();
        setCollections(Object.keys(data.data.collections || {}));
      }
    } catch (error) {
      console.error('加载Collections失败:', error);
    }
  };

  const loadProcessingJobs = async () => {
    try {
      const response = await fetch('/api/v1/rag/processing/jobs');
      if (response.ok) {
        const data = await response.json();
        setProcessingJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('加载处理任务失败:', error);
    }
  };

  const handleFileUpload = async (fileList: any[]) => {
    if (!selectedCollection) {
      message.error('请选择目标Collection');
      return;
    }

    const formData = new FormData();
    fileList.forEach(file => {
      formData.append('files', file.originFileObj);
    });
    formData.append('collection_name', selectedCollection);

    try {
      const response = await fetch('/api/v1/rag/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      if (result.success) {
        message.success('文件上传成功，正在处理中...');
        setUploadModalVisible(false);
        form.resetFields();
        loadDocuments();
        loadProcessingJobs();
      } else {
        message.error(result.message || '文件上传失败');
      }
    } catch (error) {
      message.error('文件上传失败');
    }
  };

  const handleTextAdd = async (values: any) => {
    try {
      const response = await fetch('/api/v1/rag/documents/add-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });

      const result = await response.json();
      if (result.success) {
        message.success('文本添加成功');
        setTextModalVisible(false);
        textForm.resetFields();
        loadDocuments();
      } else {
        message.error(result.message || '文本添加失败');
      }
    } catch (error) {
      message.error('文本添加失败');
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/v1/rag/documents/${documentId}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      if (result.success) {
        message.success('文档删除成功');
        loadDocuments();
      } else {
        message.error(result.message || '文档删除失败');
      }
    } catch (error) {
      message.error('文档删除失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'processing': return 'blue';
      case 'pending': return 'orange';
      case 'failed': return 'red';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '处理中';
      case 'pending': return '等待中';
      case 'failed': return '失败';
      default: return '未知';
    }
  };

  const documentColumns = [
    {
      title: '文档标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Document) => (
        <Space>
          <FileTextOutlined />
          <div>
            <div style={{ fontWeight: 'bold' }}>{text}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.file_type} • {(record.file_size / 1024).toFixed(1)} KB
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Collection',
      dataIndex: 'collection_name',
      key: 'collection_name',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '节点数量',
      dataIndex: 'node_count',
      key: 'node_count',
      render: (count: number) => (
        <Statistic value={count} suffix="个" valueStyle={{ fontSize: '14px' }} />
      ),
    },
    {
      title: '处理状态',
      dataIndex: 'embedding_status',
      key: 'embedding_status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: Document) => (
        <Space>
          <Tooltip title="查看详情">
            <Button type="link" icon={<EyeOutlined />} size="small" />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="link" icon={<EditOutlined />} size="small" />
          </Tooltip>
          <Popconfirm
            title="确定删除这个文档吗？"
            onConfirm={() => handleDeleteDocument(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="link" danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const processingColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
    },
    {
      title: 'Collection',
      dataIndex: 'collection_name',
      key: 'collection_name',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number, record: ProcessingJob) => (
        <Progress
          percent={progress}
          size="small"
          status={record.status === 'failed' ? 'exception' : 'active'}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  return (
    <PageLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>
            <FileTextOutlined style={{ marginRight: '8px' }} />
            文档管理
          </Title>
          <Paragraph type="secondary">
            管理RAG知识库中的文档，支持文件上传、文本添加、批量处理和状态监控
          </Paragraph>
        </div>

        {/* 统计信息 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总文档数"
                value={documents.length}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="处理中"
                value={documents.filter(d => d.embedding_status === 'processing').length}
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成"
                value={documents.filter(d => d.embedding_status === 'completed').length}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总节点数"
                value={documents.reduce((sum, d) => sum + d.node_count, 0)}
                prefix={<CloudUploadOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <Tabs defaultActiveKey="documents">
          <TabPane tab="文档列表" key="documents">
            <Card>
              <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={() => setUploadModalVisible(true)}
                  >
                    上传文件
                  </Button>
                  <Button
                    icon={<EditOutlined />}
                    onClick={() => setTextModalVisible(true)}
                  >
                    添加文本
                  </Button>
                </Space>
                <Button icon={<ReloadOutlined />} onClick={loadDocuments}>
                  刷新
                </Button>
              </div>

              <Table
                columns={documentColumns}
                dataSource={documents}
                rowKey="id"
                loading={loading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 个文档`,
                }}
              />
            </Card>
          </TabPane>

          <TabPane tab="处理队列" key="processing">
            <Card>
              <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
                <Text>实时监控文档处理状态</Text>
                <Button icon={<ReloadOutlined />} onClick={loadProcessingJobs}>
                  刷新
                </Button>
              </div>

              <Table
                columns={processingColumns}
                dataSource={processingJobs}
                rowKey="id"
                pagination={false}
                locale={{ emptyText: '暂无处理任务' }}
              />
            </Card>
          </TabPane>
        </Tabs>

        {/* 文件上传模态框 */}
        <Modal
          title="上传文件到知识库"
          open={uploadModalVisible}
          onCancel={() => setUploadModalVisible(false)}
          footer={null}
          width={600}
        >
          <Form form={form} layout="vertical">
            <Form.Item
              name="collection_name"
              label="目标Collection"
              rules={[{ required: true, message: '请选择Collection' }]}
            >
              <Select
                placeholder="选择要上传到的Collection"
                onChange={setSelectedCollection}
              >
                {collections.map(collection => (
                  <Option key={collection} value={collection}>
                    {collection}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label="上传文件">
              <Upload.Dragger
                multiple
                beforeUpload={() => false}
                onChange={({ fileList }) => {
                  if (fileList.length > 0) {
                    handleFileUpload(fileList);
                  }
                }}
              >
                <p className="ant-upload-drag-icon">
                  <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持PDF、Word、TXT、Markdown等格式，支持批量上传
                </p>
              </Upload.Dragger>
            </Form.Item>
          </Form>
        </Modal>

        {/* 文本添加模态框 */}
        <Modal
          title="添加文本到知识库"
          open={textModalVisible}
          onCancel={() => setTextModalVisible(false)}
          footer={null}
          width={600}
        >
          <Form form={textForm} layout="vertical" onFinish={handleTextAdd}>
            <Form.Item
              name="collection_name"
              label="目标Collection"
              rules={[{ required: true, message: '请选择Collection' }]}
            >
              <Select placeholder="选择要添加到的Collection">
                {collections.map(collection => (
                  <Option key={collection} value={collection}>
                    {collection}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="title"
              label="文档标题"
              rules={[{ required: true, message: '请输入文档标题' }]}
            >
              <Input placeholder="输入文档标题" />
            </Form.Item>

            <Form.Item
              name="content"
              label="文档内容"
              rules={[{ required: true, message: '请输入文档内容' }]}
            >
              <TextArea
                rows={8}
                placeholder="输入文档内容..."
                showCount
                maxLength={10000}
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  添加文档
                </Button>
                <Button onClick={() => setTextModalVisible(false)}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </PageLayout>
  );
};

export default DocumentManagement;
