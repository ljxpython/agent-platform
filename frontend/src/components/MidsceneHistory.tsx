import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Input,
  Select,
  DatePicker,
  message as antMessage,
  Popconfirm,
  Tooltip,
  Card,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  HistoryOutlined,
  EyeOutlined,
  DeleteOutlined,
  DownloadOutlined,
  SearchOutlined,
  ReloadOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// ==================== 类型定义 ====================

interface MidsceneSession {
  id: number;
  session_id: string;
  user_id?: number;
  user_requirement: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_count: number;
  processing_time?: number;
  created_at: string;
  completed_at?: string;
}

interface SessionDetail {
  session: MidsceneSession & {
    ui_analysis_result?: string;
    interaction_analysis_result?: string;
    midscene_generation_result?: string;
    script_generation_result?: string;
    yaml_script?: string;
    playwright_script?: string;
    script_info?: any;
    total_tokens?: number;
  };
  agent_logs: Array<{
    id: number;
    agent_name: string;
    agent_type: string;
    step: string;
    status: string;
    processing_time?: number;
    started_at: string;
    completed_at?: string;
  }>;
  uploaded_files: Array<{
    id: number;
    original_filename: string;
    file_size: number;
    file_type: string;
    uploaded_at: string;
  }>;
}

interface MidsceneHistoryProps {
  visible: boolean;
  onClose: () => void;
}

// ==================== 主组件 ====================

const MidsceneHistory: React.FC<MidsceneHistoryProps> = ({ visible, onClose }) => {
  // 状态管理
  const [sessions, setSessions] = useState<MidsceneSession[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [total, setTotal] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);

  // 筛选状态
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [searchText, setSearchText] = useState<string>('');

  // 详情模态框
  const [detailVisible, setDetailVisible] = useState<boolean>(false);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // ==================== 数据获取 ====================

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
      });

      if (statusFilter) {
        params.append('status', statusFilter);
      }

      if (dateRange) {
        params.append('start_date', dateRange[0].format('YYYY-MM-DD'));
        params.append('end_date', dateRange[1].format('YYYY-MM-DD'));
      }

      const response = await fetch(`/api/midscene/admin/sessions?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSessions(data.sessions);
      setTotal(data.total);
    } catch (error: any) {
      console.error('获取会话列表失败:', error);
      antMessage.error(`获取会话列表失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetail = async (sessionId: string) => {
    setDetailLoading(true);
    try {
      const response = await fetch(`/api/midscene/admin/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSelectedSession(data);
      setDetailVisible(true);
    } catch (error: any) {
      console.error('获取会话详情失败:', error);
      antMessage.error(`获取会话详情失败: ${error.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/midscene/admin/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      antMessage.success('会话删除成功');
      fetchSessions(); // 重新加载列表
    } catch (error: any) {
      console.error('删除会话失败:', error);
      antMessage.error(`删除会话失败: ${error.message}`);
    }
  };

  // ==================== 生命周期 ====================

  useEffect(() => {
    if (visible) {
      fetchSessions();
    }
  }, [visible, currentPage, statusFilter, dateRange]);

  // ==================== 渲染函数 ====================

  const getStatusTag = (status: string) => {
    const statusConfig = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      processing: { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const downloadScript = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    antMessage.success(`${filename} 下载成功`);
  };

  const columns: ColumnsType<MidsceneSession> = [
    {
      title: '会话ID',
      dataIndex: 'session_id',
      key: 'session_id',
      width: 120,
      render: (text: string) => (
        <Text code style={{ fontSize: 12 }}>
          {text.slice(-8)}
        </Text>
      ),
    },
    {
      title: '需求描述',
      dataIndex: 'user_requirement',
      key: 'user_requirement',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '文件数',
      dataIndex: 'file_count',
      key: 'file_count',
      width: 80,
      render: (count: number) => (
        <Tag icon={<FileTextOutlined />}>{count}</Tag>
      ),
    },
    {
      title: '处理时间',
      dataIndex: 'processing_time',
      key: 'processing_time',
      width: 100,
      render: (time?: number) => (
        time ? `${time.toFixed(1)}s` : '-'
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => (
        <Text style={{ fontSize: 12 }}>
          {dayjs(time).format('MM-DD HH:mm')}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => fetchSessionDetail(record.session_id)}
              loading={detailLoading}
            />
          </Tooltip>

          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个会话吗？"
              description="删除后无法恢复，包括所有相关文件和日志。"
              onConfirm={() => deleteSession(record.session_id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <>
      {/* 主模态框 */}
      <Modal
        title={
          <Space>
            <HistoryOutlined />
            <span>Midscene 生成历史</span>
          </Space>
        }
        open={visible}
        onCancel={onClose}
        width={1200}
        footer={null}
        destroyOnClose
      >
        {/* 筛选工具栏 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col flex="auto">
              <Space wrap>
                <Select
                  placeholder="状态筛选"
                  style={{ width: 120 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  allowClear
                >
                  <Option value="pending">等待中</Option>
                  <Option value="processing">处理中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="failed">失败</Option>
                </Select>

                <RangePicker
                  placeholder={['开始日期', '结束日期']}
                  value={dateRange}
                  onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
                  style={{ width: 240 }}
                />

                <Input
                  placeholder="搜索需求描述"
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: 200 }}
                />
              </Space>
            </Col>

            <Col>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchSessions}
                loading={loading}
              >
                刷新
              </Button>
            </Col>
          </Row>
        </Card>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={sessions}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            onChange: setCurrentPage,
            showSizeChanger: false,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          size="small"
        />
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>会话详情</span>
            {selectedSession && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {selectedSession.session.session_id}
              </Text>
            )}
          </Space>
        }
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={1000}
        footer={null}
        destroyOnClose
      >
        {selectedSession && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {/* 基本信息 */}
            <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="状态"
                    value={selectedSession.session.status}
                    valueRender={() => getStatusTag(selectedSession.session.status)}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="处理时间"
                    value={selectedSession.session.processing_time || 0}
                    suffix="秒"
                    precision={1}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Token消耗"
                    value={selectedSession.session.total_tokens || 0}
                  />
                </Col>
              </Row>

              <div style={{ marginTop: 16 }}>
                <Text strong>需求描述：</Text>
                <div style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
                  <Text>{selectedSession.session.user_requirement}</Text>
                </div>
              </div>
            </Card>

            {/* 生成的脚本 */}
            {(selectedSession.session.yaml_script || selectedSession.session.playwright_script) && (
              <Card
                title="生成的脚本"
                size="small"
                style={{ marginBottom: 16 }}
                extra={
                  <Space>
                    {selectedSession.session.yaml_script && (
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => downloadScript(
                          selectedSession.session.yaml_script!,
                          'midscene-test.yaml'
                        )}
                      >
                        YAML
                      </Button>
                    )}
                    {selectedSession.session.playwright_script && (
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => downloadScript(
                          selectedSession.session.playwright_script!,
                          'midscene-test.spec.ts'
                        )}
                      >
                        Playwright
                      </Button>
                    )}
                  </Space>
                }
              >
                <Text type="secondary">
                  脚本已生成，可点击上方按钮下载
                </Text>
              </Card>
            )}

            {/* 智能体执行日志 */}
            <Card title="智能体执行日志" size="small">
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {selectedSession.agent_logs.map((log) => (
                  <div
                    key={log.id}
                    style={{
                      padding: 12,
                      border: '1px solid #f0f0f0',
                      borderRadius: 6,
                      marginBottom: 8,
                      background: log.status === 'complete' ? '#f6ffed' :
                                 log.status === 'error' ? '#fff2f0' : '#f5f5f5'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Space>
                        <Text strong>{log.agent_name}</Text>
                        <Text type="secondary">-</Text>
                        <Text>{log.step}</Text>
                        {getStatusTag(log.status)}
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {log.processing_time ? `${log.processing_time.toFixed(1)}s` : ''}
                      </Text>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}
      </Modal>
    </>
  );
};

export default MidsceneHistory;
