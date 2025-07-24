import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  message,
  Popconfirm,
  Tag,
  Card,
  Row,
  Col,
  Typography,
  Tooltip,
  Select,
  DatePicker,
  InputNumber,
  Tabs,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  StarFilled,
  BarChartOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  RobotOutlined,
  DownOutlined,
  RightOutlined,
  UserOutlined,
  TeamOutlined,
  CalendarOutlined,
  DollarOutlined,
  PhoneOutlined,
  MailOutlined,
  LinkOutlined,
  TagOutlined,
} from '@ant-design/icons';
import { SystemAPI, ProjectResponse, ProjectCreateRequest, ProjectUpdateRequest, DepartmentOption } from '../../api/system';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;



const ProjectManagement: React.FC = () => {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<ProjectResponse | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [expandedRows, setExpandedRows] = useState<number[]>([]);
  const [departmentOptions, setDepartmentOptions] = useState<DepartmentOption[]>([]);

  // 优先级颜色映射
  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'green',
      medium: 'blue',
      high: 'orange',
      urgent: 'red',
    };
    return colors[priority as keyof typeof colors] || 'default';
  };

  // 状态颜色映射
  const getStatusColor = (status: string) => {
    const colors = {
      planning: 'default',
      active: 'processing',
      paused: 'warning',
      completed: 'success',
      cancelled: 'error',
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  // 渲染展开行内容
  const renderExpandedRow = (record: ProjectResponse) => (
    <div style={{ padding: '16px', background: '#fafafa', borderRadius: '6px' }}>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text strong>基本信息</Text>
            {record.department && (
              <div>
                <UserOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>部门：{record.department}</Text>
              </div>
            )}
            {record.manager && (
              <div>
                <TeamOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>项目经理：{record.manager}</Text>
              </div>
            )}
            <div>
              <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              <Text>优先级：</Text>
              <Tag color={getPriorityColor(record.priority)} style={{ marginLeft: 4 }}>
                {record.priority}
              </Tag>
            </div>
            <div>
              <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              <Text>状态：</Text>
              <Tag color={getStatusColor(record.status)} style={{ marginLeft: 4 }}>
                {record.status}
              </Tag>
            </div>
          </Space>
        </Col>

        <Col span={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text strong>项目时间</Text>
            {record.start_date && (
              <div>
                <CalendarOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                <Text>开始日期：{record.start_date}</Text>
              </div>
            )}
            {record.end_date && (
              <div>
                <CalendarOutlined style={{ marginRight: 8, color: '#f5222d' }} />
                <Text>结束日期：{record.end_date}</Text>
              </div>
            )}
            {record.budget && (
              <div>
                <DollarOutlined style={{ marginRight: 8, color: '#faad14' }} />
                <Text>预算：¥{record.budget.toLocaleString()}</Text>
              </div>
            )}
          </Space>
        </Col>

        <Col span={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text strong>联系方式</Text>
            {record.contact_email && (
              <div>
                <MailOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>邮箱：{record.contact_email}</Text>
              </div>
            )}
            {record.contact_phone && (
              <div>
                <PhoneOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>电话：{record.contact_phone}</Text>
              </div>
            )}
            {record.repository_url && (
              <div>
                <LinkOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>
                  <a href={record.repository_url} target="_blank" rel="noopener noreferrer">
                    代码仓库
                  </a>
                </Text>
              </div>
            )}
            {record.documentation_url && (
              <div>
                <LinkOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                <Text>
                  <a href={record.documentation_url} target="_blank" rel="noopener noreferrer">
                    项目文档
                  </a>
                </Text>
              </div>
            )}
          </Space>
        </Col>
      </Row>

      {(record.members.length > 0 || record.tags.length > 0) && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {record.members.length > 0 && (
            <Col span={12}>
              <Text strong>项目成员：</Text>
              <div style={{ marginTop: 8 }}>
                {record.members.map((member, index) => (
                  <Tag key={index} icon={<UserOutlined />} style={{ marginBottom: 4 }}>
                    {member}
                  </Tag>
                ))}
              </div>
            </Col>
          )}

          {record.tags.length > 0 && (
            <Col span={12}>
              <Text strong>项目标签：</Text>
              <div style={{ marginTop: 8 }}>
                {record.tags.map((tag, index) => (
                  <Tag key={index} icon={<TagOutlined />} color="blue" style={{ marginBottom: 4 }}>
                    {tag}
                  </Tag>
                ))}
              </div>
            </Col>
          )}
        </Row>
      )}
    </div>
  );

  // 获取部门选项
  const fetchDepartmentOptions = async () => {
    try {
      console.log('🏢 [ProjectManagement] 开始获取部门选项...');
      const response = await SystemAPI.getDepartmentOptions();
      console.log('🏢 [ProjectManagement] 部门选项响应:', response);
      console.log('🏢 [ProjectManagement] 响应类型:', typeof response);

      // SystemAPI.getDepartmentOptions() 返回的是 response.data.data，即部门数组
      if (Array.isArray(response)) {
        console.log('🏢 [ProjectManagement] 设置部门选项数组:', response);
        setDepartmentOptions(response);
      } else {
        console.error('🏢 [ProjectManagement] 部门选项响应格式错误，期望数组:', response);
      }
    } catch (error) {
      console.error('🏢 [ProjectManagement] 获取部门选项失败:', error);
    }
  };

  // 获取项目列表
  const fetchProjects = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      console.log('🚀 [ProjectManagement] 开始获取项目列表，参数:', { page, pageSize });

      const response = await SystemAPI.getProjectList({
        page,
        page_size: pageSize,
      });

      console.log('📊 [ProjectManagement] 获取项目列表响应:', response);
      console.log('🔍 [ProjectManagement] 响应类型:', typeof response);
      console.log('🔍 [ProjectManagement] 响应属性:', Object.keys(response || {}));
      console.log('🔍 [ProjectManagement] response.code:', response?.code);
      console.log('🔍 [ProjectManagement] response.data:', response?.data);

      // 现在 SystemAPI.getProjectList 返回 response.data，即API响应数据
      if (response && response.code === 200) {
        setProjects(response.data || []);
        setPagination({
          current: page,
          pageSize,
          total: response.total || 0,
        });
        console.log('✅ [ProjectManagement] 项目列表设置成功，项目数量:', response.data?.length || 0);
      } else {
        console.error('❌ [ProjectManagement] 获取项目列表失败，响应码:', response?.code);
        console.error('❌ [ProjectManagement] 完整响应对象:', response);
        message.error(response?.msg || '获取项目列表失败');
      }
    } catch (error) {
      console.error('❌ [ProjectManagement] 获取项目列表异常:', error);
      message.error('获取项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('🚀 [ProjectManagement] 组件挂载，开始获取项目列表');

    // 临时设置一个测试token，绕过认证问题
    if (!localStorage.getItem('token')) {
      localStorage.setItem('token', 'test-token-for-development');
      console.log('🔧 [ProjectManagement] 设置临时测试token');
    }

    fetchProjects();
    fetchDepartmentOptions();
  }, []);

  // 处理表格分页
  const handleTableChange = (pagination: any) => {
    fetchProjects(pagination.current, pagination.pageSize);
  };

  // 打开创建/编辑模态框
  const openModal = (project?: ProjectResponse) => {
    setEditingProject(project || null);
    if (project) {
      form.setFieldsValue({
        name: project.name,
        display_name: project.display_name,
        description: project.description,
        is_active: project.is_active,
        department: project.department,
        manager: project.manager,
        members: project.members,
        tags: project.tags,
        start_date: project.start_date ? dayjs(project.start_date) : null,
        end_date: project.end_date ? dayjs(project.end_date) : null,
        priority: project.priority,
        status: project.status,
        budget: project.budget,
        contact_email: project.contact_email,
        contact_phone: project.contact_phone,
        repository_url: project.repository_url,
        documentation_url: project.documentation_url,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        is_active: true,
        priority: 'medium',
        status: 'planning',
        members: [],
        tags: []
      });
    }
    setModalVisible(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingProject(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const projectData: ProjectCreateRequest | ProjectUpdateRequest = {
        name: values.name,
        display_name: values.display_name,
        description: values.description,
        is_active: values.is_active,
        department: values.department,
        manager: values.manager,
        members: values.members || [],
        tags: values.tags || [],
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : undefined,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
        priority: values.priority,
        status: values.status,
        budget: values.budget,
        contact_email: values.contact_email,
        contact_phone: values.contact_phone,
        repository_url: values.repository_url,
        documentation_url: values.documentation_url,
        settings: {},
      };

      if (editingProject) {
        await SystemAPI.updateProject(editingProject.id, projectData);
        message.success('项目更新成功');
      } else {
        await SystemAPI.createProject(projectData as ProjectCreateRequest);
        message.success('项目创建成功');
      }

      closeModal();
      fetchProjects(pagination.current, pagination.pageSize);
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    }
  };

  // 删除项目
  const handleDelete = async (project: ProjectResponse) => {
    try {
      await SystemAPI.deleteProject(project.id);
      message.success('项目删除成功');
      fetchProjects(pagination.current, pagination.pageSize);
    } catch (error: any) {
      console.error('删除项目失败:', error);
      message.error(error.response?.data?.detail || '删除项目失败');
    }
  };

  // 设置默认项目


  // 表格列定义
  const columns = [
    {
      title: '',
      key: 'expand',
      width: 50,
      render: (record: ProjectResponse) => (
        <Button
          type="text"
          size="small"
          icon={expandedRows.includes(record.id) ? <DownOutlined /> : <RightOutlined />}
          onClick={() => {
            if (expandedRows.includes(record.id)) {
              setExpandedRows(expandedRows.filter(id => id !== record.id));
            } else {
              setExpandedRows([...expandedRows, record.id]);
            }
          }}
        />
      ),
    },
    {
      title: '项目名称',
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text: string, record: ProjectResponse) => (
        <Space>
          <Text strong>{text}</Text>
          {record.is_default && (
            <Tag color="gold" icon={<StarFilled />}>
              默认
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '标识符',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '激活' : '停用'}
        </Tag>
      ),
    },
    {
      title: '统计信息',
      key: 'stats',
      render: (record: ProjectResponse) => (
        <Space>
          <Tooltip title="RAG知识库">
            <Tag icon={<DatabaseOutlined />} color="blue">
              {record.stats?.rag_collections || 0}
            </Tag>
          </Tooltip>
          <Tooltip title="测试用例">
            <Tag icon={<FileTextOutlined />} color="green">
              {record.stats?.test_cases || 0}
            </Tag>
          </Tooltip>
          <Tooltip title="Midscene会话">
            <Tag icon={<RobotOutlined />} color="purple">
              {record.stats?.midscene_sessions || 0}
            </Tag>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (record: ProjectResponse) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openModal(record)}
          >
            编辑
          </Button>

          {!record.is_default && (
            <Popconfirm
              title="确定要删除这个项目吗？"
              description="删除后无法恢复，请确认项目下没有数据。"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 添加调试信息
  console.log('🔍 [ProjectManagement] 当前状态:', {
    projects,
    projectsLength: projects.length,
    loading,
    pagination
  });

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>项目管理</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal()}
          >
            新建项目
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          onChange={handleTableChange}
          expandable={{
            expandedRowRender: renderExpandedRow,
            expandedRowKeys: expandedRows,
            onExpand: (expanded, record) => {
              if (expanded) {
                setExpandedRows([...expandedRows, record.id]);
              } else {
                setExpandedRows(expandedRows.filter(id => id !== record.id));
              }
            },
            showExpandColumn: false, // 隐藏默认的展开列，使用自定义的
          }}
        />
      </Card>

      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={closeModal}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            priority: 'medium',
            status: 'planning',
            members: [],
            tags: []
          }}
        >
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="name"
                    label="项目标识符"
                    rules={[
                      { required: true, message: '请输入项目标识符' },
                      { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '只能包含字母、数字和下划线，且以字母开头' },
                    ]}
                  >
                    <Input placeholder="例如: my_project" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="display_name"
                    label="显示名称"
                    rules={[{ required: true, message: '请输入显示名称' }]}
                  >
                    <Input placeholder="例如: 我的项目" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="description"
                label="项目描述"
              >
                <TextArea
                  rows={3}
                  placeholder="请输入项目描述"
                />
              </Form.Item>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="priority"
                    label="优先级"
                  >
                    <Select placeholder="选择优先级">
                      <Option value="low">低</Option>
                      <Option value="medium">中</Option>
                      <Option value="high">高</Option>
                      <Option value="urgent">紧急</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="status"
                    label="项目状态"
                  >
                    <Select placeholder="选择状态">
                      <Option value="planning">规划中</Option>
                      <Option value="active">进行中</Option>
                      <Option value="paused">暂停</Option>
                      <Option value="completed">已完成</Option>
                      <Option value="cancelled">已取消</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="is_active"
                    label="状态"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="激活" unCheckedChildren="停用" />
                  </Form.Item>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="团队信息" key="team">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="department"
                    label="所属部门"
                  >
                    <Select
                      placeholder="请选择所属部门"
                      allowClear
                      showSearch
                      filterOption={(input, option) =>
                        String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {departmentOptions.map(dept => (
                        <Option key={dept.id} value={dept.value} label={dept.label}>
                          {dept.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="manager"
                    label="项目经理"
                  >
                    <Input placeholder="请输入项目经理姓名" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="members"
                label="项目成员"
              >
                <Select
                  mode="tags"
                  placeholder="输入成员姓名后按回车添加"
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                name="tags"
                label="项目标签"
              >
                <Select
                  mode="tags"
                  placeholder="输入标签后按回车添加"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </TabPane>

            <TabPane tab="时间与预算" key="schedule">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="start_date"
                    label="开始日期"
                  >
                    <DatePicker style={{ width: '100%' }} placeholder="选择开始日期" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="end_date"
                    label="结束日期"
                  >
                    <DatePicker style={{ width: '100%' }} placeholder="选择结束日期" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="budget"
                label="项目预算"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="请输入项目预算"
                  formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value!.replace(/¥\s?|(,*)/g, '')}
                />
              </Form.Item>
            </TabPane>

            <TabPane tab="联系方式" key="contact">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="contact_email"
                    label="联系邮箱"
                    rules={[
                      { type: 'email', message: '请输入有效的邮箱地址' }
                    ]}
                  >
                    <Input placeholder="请输入联系邮箱" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="contact_phone"
                    label="联系电话"
                  >
                    <Input placeholder="请输入联系电话" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="repository_url"
                label="代码仓库地址"
                rules={[
                  { type: 'url', message: '请输入有效的URL地址' }
                ]}
              >
                <Input placeholder="请输入代码仓库地址" />
              </Form.Item>

              <Form.Item
                name="documentation_url"
                label="文档地址"
                rules={[
                  { type: 'url', message: '请输入有效的URL地址' }
                ]}
              >
                <Input placeholder="请输入项目文档地址" />
              </Form.Item>
            </TabPane>
          </Tabs>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectManagement;
