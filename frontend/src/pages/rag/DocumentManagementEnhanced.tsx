import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Upload,
  message,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Progress,
  Typography,
  Row,
  Col,
  Statistic,
  Tooltip,
  Popconfirm,
  Alert,
  Tabs,
  Descriptions,
  Badge,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  PlusOutlined,
  CloudUploadOutlined,
  FileOutlined,
  FolderOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import PageLayout from '../../components/PageLayout';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface FileRecord {
  id: number;
  filename: string;
  file_md5: string;
  file_size: number;
  collection_name: string;
  user_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface DocumentStats {
  project_id: string;
  total_documents: number;
  completed_documents: number;
  collection_stats: Record<string, number>;
  total_size_mb: number;
  success_rate: number;
}

const DocumentManagementEnhanced: React.FC = () => {
  // 状态管理
  const [projectId, setProjectId] = useState<string>('default');
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('general');
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [documentStats, setDocumentStats] = useState<DocumentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);

  // 模态框状态
  const [addTextModalVisible, setAddTextModalVisible] = useState(false);
  const [fileDetailModalVisible, setFileDetailModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);

  // 表单
  const [addTextForm] = Form.useForm();

  useEffect(() => {
    loadCollections();
    loadDocumentStats();
    if (selectedCollection) {
      loadCollectionFiles();
    }
  }, [projectId, selectedCollection]);

  // 加载Collections列表
  const loadCollections = async () => {
    try {
      const response = await fetch(`/api/v1/rag/collections/?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          const collectionNames = data.data.collections.map((col: any) => col.name);
          setCollections(collectionNames);
          if (collectionNames.length > 0 && !collectionNames.includes(selectedCollection)) {
            setSelectedCollection(collectionNames[0]);
          }
        }
      }
    } catch (error) {
      console.error('加载Collections失败:', error);
    }
  };

  // 加载文档统计信息
  const loadDocumentStats = async () => {
    try {
      const response = await fetch(`/api/v1/rag/documents/stats?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setDocumentStats(data.data);
        }
      }
    } catch (error) {
      console.error('加载文档统计失败:', error);
    }
  };

  // 加载Collection中的文件
  const loadCollectionFiles = async () => {
    if (!selectedCollection) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/documents/files/${selectedCollection}?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setFiles(data.data.files || []);
        } else {
          message.error(data.msg || '获取文件列表失败');
        }
      } else {
        message.error('获取文件列表失败');
      }
    } catch (error) {
      console.error('加载文件列表异常:', error);
      message.error('加载文件列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 添加文本到知识库
  const handleAddText = async (values: any) => {
    setUploadLoading(true);
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
          setAddTextModalVisible(false);
          addTextForm.resetFields();
          loadCollectionFiles();
          loadDocumentStats();
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
      setUploadLoading(false);
    }
  };

  // 文件上传配置
  const uploadProps = {
    name: 'file',
    action: `/api/v1/rag/documents/upload?project_id=${projectId}&collection_name=${selectedCollection}`,
    onChange(info: any) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 文件上传成功`);
        loadCollectionFiles();
        loadDocumentStats();
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 文件上传失败`);
      }
    },
  };

  // 文件表格列定义
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string, record: FileRecord) => (
        <Space>
          <FileOutlined />
          <Text>{text}</Text>
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => {
        const sizeInMB = (size / (1024 * 1024)).toFixed(2);
        return `${sizeInMB} MB`;
      },
    },
    {
      title: 'MD5',
      dataIndex: 'file_md5',
      key: 'file_md5',
      render: (md5: string) => (
        <Text code>{md5.substring(0, 8)}...</Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
          processing: { color: 'processing', icon: <ExclamationCircleOutlined />, text: '处理中' },
          failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
        };
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.processing;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (text: any, record: FileRecord) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedFile(record);
                setFileDetailModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个文件吗？"
              onConfirm={() => {/* 删除逻辑 */}}
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <PageLayout
      title="文档管理"
      description="管理RAG知识库中的文档，支持文件上传和文本添加，具备项目隔离功能"
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
                  title="总文档数"
                  value={documentStats?.total_documents || 0}
                  prefix={<FileTextOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="总大小"
                  value={documentStats?.total_size_mb || 0}
                  suffix="MB"
                  prefix={<FolderOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="成功率"
                  value={documentStats?.success_rate || 0}
                  suffix="%"
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* Collection选择和操作 */}
        <Col span={24}>
          <Card>
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  <Text strong>当前Collection:</Text>
                  <Select
                    value={selectedCollection}
                    onChange={setSelectedCollection}
                    style={{ width: 200 }}
                  >
                    {collections.map(col => (
                      <Option key={col} value={col}>{col}</Option>
                    ))}
                  </Select>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={loadCollectionFiles}
                    loading={loading}
                  >
                    刷新
                  </Button>
                </Space>
              </Col>
              <Col>
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setAddTextModalVisible(true)}
                  >
                    添加文本
                  </Button>
                  <Upload {...uploadProps}>
                    <Button icon={<UploadOutlined />}>上传文件</Button>
                  </Upload>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 文件列表 */}
        <Col span={24}>
          <Card title={`Collection "${selectedCollection}" 中的文件`}>
            <Table
              columns={fileColumns}
              dataSource={files}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个文件`,
              }}
            />
          </Card>
        </Col>

        {/* Collection统计 */}
        {documentStats && (
          <Col span={24}>
            <Card title="各Collection文档统计">
              <Row gutter={16}>
                {Object.entries(documentStats.collection_stats).map(([collection, count]) => (
                  <Col span={6} key={collection}>
                    <Card size="small">
                      <Statistic
                        title={collection}
                        value={count}
                        prefix={<FileTextOutlined />}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>
        )}
      </Row>

      {/* 添加文本模态框 */}
      <Modal
        title="添加文本到知识库"
        visible={addTextModalVisible}
        onCancel={() => setAddTextModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={addTextForm}
          layout="vertical"
          onFinish={handleAddText}
        >
          <Form.Item
            name="text"
            label="文本内容"
            rules={[{ required: true, message: '请输入文本内容' }]}
          >
            <TextArea rows={8} placeholder="请输入要添加到知识库的文本内容..." />
          </Form.Item>
          <Form.Item name="collection_name" label="目标Collection">
            <Select value={selectedCollection} onChange={setSelectedCollection}>
              {collections.map(col => (
                <Option key={col} value={col}>{col}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="metadata" label="元数据 (JSON格式)">
            <TextArea
              rows={3}
              placeholder='{"source": "manual", "topic": "example"}'
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={uploadLoading}
                icon={<CloudUploadOutlined />}
              >
                添加到知识库
              </Button>
              <Button onClick={() => setAddTextModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 文件详情模态框 */}
      <Modal
        title="文件详情"
        visible={fileDetailModalVisible}
        onCancel={() => setFileDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedFile && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="文件名">{selectedFile.filename}</Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {(selectedFile.file_size / (1024 * 1024)).toFixed(2)} MB
            </Descriptions.Item>
            <Descriptions.Item label="MD5哈希">{selectedFile.file_md5}</Descriptions.Item>
            <Descriptions.Item label="Collection">{selectedFile.collection_name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedFile.status === 'completed' ? 'success' : 'processing'}>
                {selectedFile.status === 'completed' ? '已完成' : '处理中'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {new Date(selectedFile.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedFile.updated_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </PageLayout>
  );
};

export default DocumentManagementEnhanced;
