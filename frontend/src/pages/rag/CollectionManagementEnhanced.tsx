import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Select,
  message,
  Popconfirm,
  Typography,
  Row,
  Col,
  Tooltip,
  Tabs,
  Alert,
  Badge,
  Descriptions,
  Divider,
} from 'antd';
import {
  DatabaseOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  CloudSyncOutlined,
  InfoCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import PageLayout from '../../components/PageLayout';

const { Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface Collection {
  id: number;
  name: string;
  display_name: string;
  description: string;
  business_type: string;
  chunk_size: number;
  chunk_overlap: number;
  dimension: number;
  top_k: number;
  similarity_threshold: number;
  is_active: boolean;
  document_count: number;
  created_at: string;
  updated_at: string;
  project_id?: string;
  project_collection_name?: string;
}

interface MilvusCollection {
  name: string;
  project_collection_name: string;
  project_id: string;
}

interface MilvusCollectionInfo {
  name: string;
  description: string;
  num_entities: number;
  schema: {
    fields: Array<{
      name: string;
      type: string;
      is_primary: boolean;
      auto_id: boolean;
      description: string;
    }>;
  };
  indexes: Array<{
    field_name: string;
    index_name: string;
    params: any;
  }>;
  original_name: string;
  project_collection_name: string;
  project_id: string;
}

const CollectionManagementEnhanced: React.FC = () => {
  // 状态管理
  const [collections, setCollections] = useState<Collection[]>([]);
  const [milvusCollections, setMilvusCollections] = useState<MilvusCollection[]>([]);
  const [projectId, setProjectId] = useState<string>('default');
  const [loading, setLoading] = useState(false);
  const [milvusLoading, setMilvusLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('sqlite');

  // 模态框状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [milvusDetailModalVisible, setMilvusDetailModalVisible] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [selectedMilvusCollection, setSelectedMilvusCollection] = useState<MilvusCollectionInfo | null>(null);

  useEffect(() => {
    loadCollections();
    if (activeTab === 'milvus') {
      loadMilvusCollections();
    }
  }, [projectId, activeTab]);

  // 加载SQLite中的Collections
  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/collections/?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setCollections(data.data?.collections || []);
          message.success(`加载了 ${data.data?.collections?.length || 0} 个Collection`);
        } else {
          message.error(data.msg || '获取Collection列表失败');
        }
      } else {
        message.error('获取Collection列表失败');
      }
    } catch (error) {
      console.error('加载Collection列表异常:', error);
      message.error('加载Collection列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载Milvus中的Collections
  const loadMilvusCollections = async () => {
    setMilvusLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/collections/milvus?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setMilvusCollections(data.data?.collections || []);
          message.success(`发现 ${data.data?.collections?.length || 0} 个Milvus Collection`);
        } else {
          message.error(data.msg || '获取Milvus Collection列表失败');
        }
      } else {
        message.error('获取Milvus Collection列表失败');
      }
    } catch (error) {
      console.error('加载Milvus Collection列表异常:', error);
      message.error('加载Milvus Collection列表失败');
    } finally {
      setMilvusLoading(false);
    }
  };

  // 从Milvus同步Collections
  const syncFromMilvus = async () => {
    setSyncLoading(true);
    try {
      const response = await fetch(`/api/v1/rag/collections/sync-from-milvus?project_id=${projectId}`, {
        method: 'POST',
      });
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          message.success(data.msg || '同步成功');
          // 重新加载两个列表
          loadCollections();
          loadMilvusCollections();
        } else {
          message.error(data.msg || '同步失败');
        }
      } else {
        message.error('同步失败');
      }
    } catch (error) {
      console.error('同步异常:', error);
      message.error('同步失败');
    } finally {
      setSyncLoading(false);
    }
  };

  // 获取Milvus Collection详细信息
  const getMilvusCollectionInfo = async (collectionName: string) => {
    try {
      const response = await fetch(`/api/v1/rag/collections/${collectionName}/milvus-info?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          setSelectedMilvusCollection(data.data);
          setMilvusDetailModalVisible(true);
        } else {
          message.error(data.msg || '获取Collection信息失败');
        }
      } else {
        message.error('获取Collection信息失败');
      }
    } catch (error) {
      console.error('获取Collection信息异常:', error);
      message.error('获取Collection信息失败');
    }
  };

  // SQLite Collections表格列定义
  const sqliteColumns = [
    {
      title: 'Collection名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Collection) => (
        <Space>
          <DatabaseOutlined />
          <Text strong>{text}</Text>
          {record.project_id !== 'default' && (
            <Tag color="blue">{record.project_id}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: '业务类型',
      dataIndex: 'business_type',
      key: 'business_type',
      render: (text: string) => <Tag color="green">{text}</Tag>,
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      render: (count: number) => (
        <Badge count={count} showZero color="#52c41a" />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Collection) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedCollection(record);
                setDetailModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="text" icon={<EditOutlined />} />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个Collection吗？"
              onConfirm={() => {/* 删除逻辑 */}}
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Milvus Collections表格列定义
  const milvusColumns = [
    {
      title: 'Collection名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Space>
          <CloudSyncOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
          <Tag color="purple">Milvus</Tag>
        </Space>
      ),
    },
    {
      title: '完整名称',
      dataIndex: 'project_collection_name',
      key: 'project_collection_name',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '项目ID',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MilvusCollection) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<InfoCircleOutlined />}
              onClick={() => getMilvusCollectionInfo(record.name)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <PageLayout
      title="Collection管理"
      description="管理RAG知识库的Collections，支持SQLite数据库和Milvus向量数据库"
    >
      <Row gutter={[16, 16]}>
        {/* 项目选择器 */}
        <Col span={24}>
          <Card size="small">
            <Space>
              <Text strong>当前项目:</Text>
              <Select
                value={projectId}
                onChange={setProjectId}
                style={{ width: 200 }}
              >
                <Option value="default">默认项目</Option>
                <Option value="project1">项目1</Option>
                <Option value="project2">项目2</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  loadCollections();
                  if (activeTab === 'milvus') {
                    loadMilvusCollections();
                  }
                }}
              >
                刷新
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 主要内容 */}
        <Col span={24}>
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane
                tab={
                  <span>
                    <DatabaseOutlined />
                    SQLite数据库 ({collections.length})
                  </span>
                }
                key="sqlite"
              >
                <Table
                  columns={sqliteColumns}
                  dataSource={collections}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 个Collection`,
                  }}
                />
              </TabPane>

              <TabPane
                tab={
                  <span>
                    <CloudSyncOutlined />
                    Milvus向量数据库 ({milvusCollections.length})
                  </span>
                }
                key="milvus"
              >
                <Space style={{ marginBottom: 16 }}>
                  <Alert
                    message="这里显示的是Milvus向量数据库中实际存在的Collections"
                    type="info"
                    showIcon
                  />
                  <Button
                    type="primary"
                    icon={<SyncOutlined />}
                    loading={syncLoading}
                    onClick={syncFromMilvus}
                  >
                    同步到SQLite
                  </Button>
                </Space>

                <Table
                  columns={milvusColumns}
                  dataSource={milvusCollections}
                  rowKey="project_collection_name"
                  loading={milvusLoading}
                  pagination={{
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 个Collection`,
                  }}
                />
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>

      {/* SQLite Collection详情模态框 */}
      <Modal
        title="Collection详情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedCollection && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="名称">{selectedCollection.name}</Descriptions.Item>
            <Descriptions.Item label="显示名称">{selectedCollection.display_name}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{selectedCollection.description}</Descriptions.Item>
            <Descriptions.Item label="业务类型">{selectedCollection.business_type}</Descriptions.Item>
            <Descriptions.Item label="维度">{selectedCollection.dimension}</Descriptions.Item>
            <Descriptions.Item label="分块大小">{selectedCollection.chunk_size}</Descriptions.Item>
            <Descriptions.Item label="分块重叠">{selectedCollection.chunk_overlap}</Descriptions.Item>
            <Descriptions.Item label="Top-K">{selectedCollection.top_k}</Descriptions.Item>
            <Descriptions.Item label="相似度阈值">{selectedCollection.similarity_threshold}</Descriptions.Item>
            <Descriptions.Item label="文档数量">{selectedCollection.document_count}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedCollection.is_active ? 'success' : 'default'}>
                {selectedCollection.is_active ? '活跃' : '禁用'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* Milvus Collection详情模态框 */}
      <Modal
        title="Milvus Collection详情"
        visible={milvusDetailModalVisible}
        onCancel={() => setMilvusDetailModalVisible(false)}
        footer={null}
        width={1000}
      >
        {selectedMilvusCollection && (
          <div>
            <Descriptions bordered column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Collection名称">{selectedMilvusCollection.original_name}</Descriptions.Item>
              <Descriptions.Item label="完整名称">{selectedMilvusCollection.project_collection_name}</Descriptions.Item>
              <Descriptions.Item label="项目ID">{selectedMilvusCollection.project_id}</Descriptions.Item>
              <Descriptions.Item label="实体数量">{selectedMilvusCollection.num_entities}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selectedMilvusCollection.description || '无描述'}</Descriptions.Item>
            </Descriptions>

            <Divider>Schema信息</Divider>
            <Table
              size="small"
              columns={[
                { title: '字段名', dataIndex: 'name', key: 'name' },
                { title: '类型', dataIndex: 'type', key: 'type' },
                { title: '主键', dataIndex: 'is_primary', key: 'is_primary', render: (val: boolean) => val ? '是' : '否' },
                { title: '自动ID', dataIndex: 'auto_id', key: 'auto_id', render: (val: boolean) => val ? '是' : '否' },
                { title: '描述', dataIndex: 'description', key: 'description' },
              ]}
              dataSource={selectedMilvusCollection.schema?.fields || []}
              pagination={false}
            />

            {selectedMilvusCollection.indexes && selectedMilvusCollection.indexes.length > 0 && (
              <>
                <Divider>索引信息</Divider>
                <Table
                  size="small"
                  columns={[
                    { title: '字段名', dataIndex: 'field_name', key: 'field_name' },
                    { title: '索引名', dataIndex: 'index_name', key: 'index_name' },
                    { title: '参数', dataIndex: 'params', key: 'params', render: (params: any) => JSON.stringify(params) },
                  ]}
                  dataSource={selectedMilvusCollection.indexes}
                  pagination={false}
                />
              </>
            )}
          </div>
        )}
      </Modal>
    </PageLayout>
  );
};

export default CollectionManagementEnhanced;
