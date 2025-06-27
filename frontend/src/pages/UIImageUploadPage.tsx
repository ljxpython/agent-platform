/**
 * UI测试图片上传页面
 * 支持多图片上传、RAG集成、进度查询
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  Card,
  Upload,
  Button,
  Input,
  Select,
  Form,
  message,
  Progress,
  List,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  Spin,
} from 'antd';
import {
  InboxOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';

import {
  uploadUIImages,
  createProgressListener,
  getUITestingCollections,
  validateImageFile,
  validateFileSize,
  formatFileSize,
  type CollectionInfo,
} from '../api/ui-testing';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

interface AnalysisProgress {
  type: string;
  agent?: string;
  step?: string;
  content?: string;
  timestamp?: string;
}

const UIImageUploadPage: React.FC = () => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [analysisLogs, setAnalysisLogs] = useState<AnalysisProgress[]>([]);
  const [conversationId, setConversationId] = useState<string>('');
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [loadingCollections, setLoadingCollections] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

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

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // 验证文件类型
      if (!validateImageFile(file)) {
        message.error(`${file.name} 不是有效的图片文件`);
        return false;
      }

      // 验证文件大小
      if (!validateFileSize(file, 10)) {
        message.error(`${file.name} 文件大小超过10MB限制`);
        return false;
      }

      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setFileList(info.fileList);
    },
    onRemove: (file) => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
    },
  };

  // 开始分析
  const handleAnalyze = async () => {
    try {
      const values = await form.validateFields();

      if (fileList.length === 0) {
        message.error('请至少上传一张图片');
        return;
      }

      setUploading(true);
      setAnalyzing(true);
      setProgress(0);
      setAnalysisLogs([]);

      // 转换文件格式
      const files = fileList.map(file => file.originFileObj as File);

      // 上传图片并开始分析
      const response = await uploadUIImages(
        files,
        values.userRequirement,
        values.collectionName || 'ui_testing',
        'current_user'
      );

      if (response.code === 200) {
        const { conversation_id } = response.data;
        setConversationId(conversation_id);
        message.success('图片上传成功，开始UI分析...');

        // 开始监听分析进度
        startProgressListener(conversation_id);
      } else {
        throw new Error(response.msg || '上传失败');
      }
    } catch (error) {
      console.error('分析启动失败:', error);
      message.error(`分析启动失败: ${error.message}`);
      setUploading(false);
      setAnalyzing(false);
    }
  };

  // 开始监听分析进度
  const startProgressListener = (conversationId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    eventSourceRef.current = createProgressListener(
      conversationId,
      (data) => {
        console.log('收到分析进度:', data);

        setAnalysisLogs(prev => [...prev, data]);

        // 根据消息类型更新进度
        switch (data.type) {
          case 'agent_start':
            setProgress(prev => Math.min(prev + 20, 90));
            break;
          case 'agent_complete':
            setProgress(prev => Math.min(prev + 25, 95));
            break;
          case 'rag_save':
            setProgress(100);
            break;
          case 'agent_error':
            message.error(`分析失败: ${data.content}`);
            setAnalyzing(false);
            setUploading(false);
            break;
        }

        // 检查是否完成
        if (data.type === 'rag_save' || data.step?.includes('完成')) {
          setTimeout(() => {
            setAnalyzing(false);
            setUploading(false);
            setProgress(100);
            message.success('UI分析完成！结果已保存到知识库');
          }, 1000);
        }
      },
      (error) => {
        console.error('SSE连接错误:', error);
        message.error('连接分析服务失败');
        setAnalyzing(false);
        setUploading(false);
      }
    );
  };

  // 清理资源
  React.useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setFileList([]);
    setProgress(0);
    setAnalysisLogs([]);
    setConversationId('');
    setAnalyzing(false);
    setUploading(false);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>UI界面分析</Title>
      <Paragraph>
        上传UI界面截图，AI将自动分析界面元素并将结果存入知识库，为后续的自动化测试提供支持。
      </Paragraph>

      <Row gutter={24}>
        <Col span={12}>
          <Card title="图片上传与分析" style={{ height: '100%' }}>
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
                  rows={4}
                  placeholder="请详细描述您想要测试的功能或场景，例如：用户登录流程、商品搜索功能、表单提交等..."
                />
              </Form.Item>

              <Form.Item
                name="collectionName"
                label="目标知识库"
                rules={[{ required: true, message: '请选择目标知识库' }]}
              >
                <Select
                  placeholder="选择存储分析结果的知识库"
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

              <Form.Item label="上传界面截图">
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽图片到此区域上传</p>
                  <p className="ant-upload-hint">
                    支持单个或批量上传。支持 JPG、PNG、GIF、WebP 格式，单个文件不超过10MB
                  </p>
                </Dragger>
              </Form.Item>

              {fileList.length > 0 && (
                <Alert
                  message={`已选择 ${fileList.length} 个文件`}
                  description={`总大小: ${formatFileSize(
                    fileList.reduce((total, file) => total + (file.size || 0), 0)
                  )}`}
                  type="info"
                  style={{ marginBottom: 16 }}
                />
              )}

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<CloudUploadOutlined />}
                    onClick={handleAnalyze}
                    loading={uploading}
                    disabled={fileList.length === 0}
                  >
                    开始分析
                  </Button>
                  <Button onClick={handleReset} disabled={analyzing}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="分析进度" style={{ height: '100%' }}>
            {analyzing && (
              <div style={{ marginBottom: 16 }}>
                <Progress
                  percent={progress}
                  status={analyzing ? 'active' : 'success'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <Text type="secondary">
                  {analyzing ? '正在分析中...' : '分析完成'}
                </Text>
              </div>
            )}

            {analysisLogs.length > 0 && (
              <List
                size="small"
                dataSource={analysisLogs}
                renderItem={(item, index) => (
                  <List.Item key={index}>
                    <List.Item.Meta
                      avatar={
                        item.type === 'agent_complete' ? (
                          <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        ) : item.type === 'agent_error' ? (
                          <DeleteOutlined style={{ color: '#ff4d4f' }} />
                        ) : (
                          <LoadingOutlined style={{ color: '#1890ff' }} />
                        )
                      }
                      title={
                        <Space>
                          <Text strong>{item.agent || '系统'}</Text>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}
                          </Text>
                        </Space>
                      }
                      description={
                        <div>
                          {item.step && <Text type="secondary">{item.step}</Text>}
                          {item.content && (
                            <div style={{ marginTop: 4 }}>
                              <Text>{item.content}</Text>
                            </div>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}

            {!analyzing && analysisLogs.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                <EyeOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>上传图片后，分析进度将在这里显示</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default UIImageUploadPage;
