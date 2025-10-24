import React, { useEffect, useState } from 'react';
import '../styles/hover.css';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { EvalData } from '../types';
import ErrorBanner from '../components/ErrorBanner';
import { message, Popconfirm, Button, Table, Form, Input, Space, Alert, Modal, InputNumber, Pagination, Tooltip, Card, Typography, Skeleton, Dropdown, Menu } from 'antd';
import { EditOutlined, DeleteOutlined, ArrowLeftOutlined, MoreOutlined, GlobalOutlined } from '@ant-design/icons';

const EvalDataPage: React.FC = () => {
  const { id } = useParams();
  const setId = Number(id);
  const [data, setData] = useState<EvalData[]>([]);
  
  const [error, setError] = useState<string | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [serverQuery, setServerQuery] = useState<string | undefined>(undefined);
  const [globalSearch, setGlobalSearch] = useState(false);
  const [evalSetName, setEvalSetName] = useState<string | null>(null);
  const navigate = useNavigate();
  const [showBack, setShowBack] = useState(false);
  const [jumpPage, setJumpPage] = useState<number | null>(null);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const load = async (q?: string, global?: boolean) => {
    try {
      const res = await api.listEvalData(setId, currentPage, pageSize, q, global);
      setData(res?.items || []);
      setTotal(res?.total || 0);
    } catch (e: any) {
      setError(String(e?.message || e || '加载失败'));
    }
  };

  // server-side data in `data`
  const filteredData = data;

  // Reload when setId, current page or page size changes
  useEffect(() => { if (setId) load(serverQuery, globalSearch); }, [setId, currentPage, pageSize, serverQuery, globalSearch]);

  useEffect(() => {
    let mounted = true;
    const loadSet = async () => {
      try {
        const s = await api.getEvalSet(setId);
        if (mounted) setEvalSetName(s?.name || null);
      } catch (e) {
        // ignore silently
      }
    };
    if (setId) loadSet();
    return () => { mounted = false; };
  }, [setId]);

  // trigger back button entrance animation after mount
  useEffect(() => {
    const t = setTimeout(() => setShowBack(true), 80);
    return () => clearTimeout(t);
  }, []);

  // clear jump input after navigation
  useEffect(() => { setJumpPage(null); }, [currentPage]);

  const openModal = () => { setIsModalVisible(true); };
  const closeModal = () => { setIsModalVisible(false); form.resetFields(); setError(null); };

  const onFinish = async (values: any) => {
    try {
      await api.createEvalData(setId, values);
      message.success('新增成功');
      load();
      closeModal();
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  };

  const openEditModal = (record: any) => {
    setEditingRecord(record);
    editForm.setFieldsValue({ content: record.content, intent: record.intent, expected: record.expected });
    setIsEditModalVisible(true);
  };

  const closeEditModal = () => {
    setIsEditModalVisible(false);
    setEditingRecord(null);
    editForm.resetFields();
    setError(null);
  };

  const onEditFinish = async (values: any) => {
    if (!editingRecord) return;
    try {
      await api.patchEvalData(setId, editingRecord.id, { content: values.content, intent: values.intent, expected: values.expected });
      message.success('更新成功');
      load();
      closeEditModal();
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  };

  const del = async (dataId: number) => {
    try {
      await api.deleteEvalData(setId, dataId);
      load();
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  };


  const columns = [
    { title: 'ID', dataIndex: 'corpus_id', key: 'corpus_id', width: 80 },
    { title: '内容', dataIndex: 'content', key: 'content', render: (_: any, record: any) => (
        <div style={{ maxWidth: 420, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={record.content}>{record.content}</div>
      ) },
    { title: '预期', dataIndex: 'expected', key: 'expected', render: (_: any, record: any) => (
        <div style={{ maxWidth: 420, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          <Tooltip title={record.expected || ''} placement="topLeft">
            <span style={{ color: '#666' }}>{record.expected}</span>
          </Tooltip>
        </div>
      ) },
    { title: '意图', dataIndex: 'intent', key: 'intent', width: 140, render: (_: any, record: any) => (
        <div style={{ maxWidth: 140, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={record.intent}>{record.intent}</div>
      ) },
    {
      title: '操作', key: 'actions', width: 140, render: (_: any, record: any) => {
        const menu = (
          <Menu onClick={({ key }) => handleRowAction(key as string, record)}>
            <Menu.Item key="copy_content">复制内容</Menu.Item>
            <Menu.Item key="copy_expected">复制预期</Menu.Item>
            <Menu.Item key="copy_intent">复制意图</Menu.Item>
          </Menu>
        );
        return (
          <Space>
            <Tooltip title="编辑">
              <Button type="text" icon={<EditOutlined />} onClick={() => openEditModal(record)} aria-label="编辑" />
            </Tooltip>
            <Popconfirm title="确认删除?" onConfirm={() => del(record.id)} okText="是" cancelText="否">
              <Tooltip title="删除">
                <Button type="text" danger icon={<DeleteOutlined />} aria-label="删除" />
              </Tooltip>
            </Popconfirm>
            <Dropdown overlay={menu} trigger={['click']} placement="bottomRight">
              <Button type="text" icon={<MoreOutlined />} aria-label="更多操作" />
            </Dropdown>
          </Space>
        );
      }
    }
  ];

  const handleRowAction = async (action: string, record: any) => {
    try {
      let text = '';
      if (action === 'copy_content') text = record.content || '';
      if (action === 'copy_expected') text = record.expected || '';
      if (action === 'copy_intent') text = record.intent || '';
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // fallback
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      message.success('已复制到剪贴板');
    } catch (e) {
      message.error('复制失败');
    }
  };

  return (
  <div className="page-container" style={{ position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/sets')} aria-label="返回" style={{ color: 'inherit', padding: 6, fontSize: 18 }} />
          <div style={{ marginLeft: 6, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontWeight: 600 }}>
                {evalSetName ? evalSetName : <span aria-hidden style={{ display: 'inline-block', width: 240, height: 20 }} />}
              </span>
            </h2>
            <div style={{ color: '#666', fontSize: 12 }}>共 {total} 条</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Input.Search placeholder="搜索内容 / 预期 / 意图" allowClear onSearch={(v) => { setServerQuery(v || undefined); setCurrentPage(1); }} onChange={(e) => setSearchQuery(e.target.value)} style={{ width: 300 }} />
          <Tooltip title={globalSearch ? '跨集搜索：已开启（在所有评测集中搜索）' : '跨集搜索：在当前评测集中搜索'}>
            <Button type="text" icon={<GlobalOutlined />} onClick={() => { setGlobalSearch(!globalSearch); setCurrentPage(1); }} aria-label="跨集搜索切换" style={{ color: globalSearch ? '#1890ff' : undefined }} />
          </Tooltip>
          <Space>
            <Button type="primary" onClick={openModal}>新增</Button>
          </Space>
        </div>
      </div>
      {/* 已移除顶部导入提示 */}

      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

  <Card className="page-card-hover" style={{ boxShadow: '0 4px 18px rgba(0,0,0,0.06)', borderRadius: 8 }} bodyStyle={{ padding: 12 }}>
        <Table
          rowKey="id"
          dataSource={filteredData}
          columns={columns}
          pagination={false}
          bordered
          size="middle"
          sticky={{ offsetHeader: 64 }}
          rowClassName={() => 'eval-row'}
        />
      </Card>

      

      <Modal title="编辑语料" open={isEditModalVisible} onCancel={closeEditModal} onOk={() => editForm.submit()} okText="保存" cancelText="取消" centered width={700}>
        <Form form={editForm} layout="vertical" onFinish={onEditFinish}>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请填写内容' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="expected" label="预期">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="intent" label="意图">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
        <Pagination current={currentPage} pageSize={pageSize} total={total} showSizeChanger={false} onChange={(page) => setCurrentPage(page)} />
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <InputNumber min={1} max={totalPages} value={jumpPage ?? undefined} onChange={(v: number | null) => setJumpPage(v)} />
          <Button onClick={() => { if (jumpPage !== null && jumpPage >= 1 && jumpPage <= totalPages) { setCurrentPage(jumpPage); } }}>跳转</Button>
          <Button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>跳到顶部</Button>
        </div>
      </div>

  <Modal title="新增语料" open={isModalVisible} onCancel={closeModal} onOk={() => form.submit()} okText="新增" cancelText="取消">
        <Alert className="import-alert" type="info" showIcon closable={false} style={{ marginBottom: 12 }} message={<span style={{ fontWeight: 600 }}>新增数据格式说明</span>} description={<div>请在表单中填写要新增的语料。字段：<b>content</b>（语料，必填），<b>expected</b>（期望，选填），<b>intent</b>（意图，选填）。</div>} />

        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请填写内容' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="expected" label="预期结果">
              <Input.TextArea rows={3} />
            </Form.Item>
          <Form.Item name="intent" label="意图">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EvalDataPage;
