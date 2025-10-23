import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EvalSet, BatchExecResponse } from '../types';
import { Link, useNavigate } from 'react-router-dom';
import { Table, Input, Button, Card, Skeleton, Space, Popconfirm, message, List, Collapse, Tooltip, Progress, Modal } from 'antd';
import { PlayCircleOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import ErrorBanner from '../components/ErrorBanner';

const { Search } = Input;

const EvalSetsPage: React.FC = () => {
  const [sets, setSets] = useState<EvalSet[]>([]);
  const [name, setName] = useState('');
  const [executingSetId, setExecutingSetId] = useState<number | null>(null);
  const [execResult, setExecResult] = useState<BatchExecResponse | null>(null);
  const [execModalVisible, setExecModalVisible] = useState(false);
  const [execProgress, setExecProgress] = useState(0);
  const [execRunning, setExecRunning] = useState(false);
  const progressTimerRef = React.useRef<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState<string>('');
  const [savingId, setSavingId] = useState<number | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await api.getEvalSets();
      setSets(data || []);
    } catch (e: any) {
      console.error('Failed to load eval sets', e);
      setError(String(e?.message || e || '加载评测集失败'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const create = async (value?: string) => {
    const n = value ?? name;
    if (!n) return;
    try {
      await api.createEvalSet(n);
      setName('');
      message.success('创建成功');
      load();
    } catch (e: any) {
      message.error('创建失败: ' + (e?.message || e));
    }
  };

  const del = async (id: number) => {
    try {
      await api.deleteEvalSet(id);
      message.success('已删除');
      load();
    } catch (e: any) {
      message.error('删除失败: ' + (e?.message || e));
    }
  };

  const executeBySet = async (id: number) => {
    // start async job and poll job status for real progress
    setExecutingSetId(id);
    setExecResult(null);
    setExecModalVisible(true);
    setExecProgress(0);
    setExecRunning(true);
    try {
      const { job_id } = await api.executeBySetAsync(id);
      // poll job status
      const poll = window.setInterval(async () => {
        try {
          const s = await api.getJobStatus(job_id);
          const total = s.total || 0;
          const processed = s.processed || 0;
          const percent = total > 0 ? Math.round((processed / total) * 100) : 0;
          setExecProgress(percent);
          if (s.status === 'success' || s.status === 'failed') {
            window.clearInterval(poll);
            setExecRunning(false);
            // fetch results summary from results endpoint
            try {
              const results = await api.listResultsBySet(id);
              const succeeded = results.length; // simplistic: number of results saved
              // total is known as total
              setExecResult({ total: total, succeeded: succeeded, failed: Math.max(0, total - succeeded), result_ids: results.map(r => r.id), errors: [], durations_ms: [] });
              setExecProgress(100);
              message.success(`集合 ${id} 执行完成`);
            } catch (e:any) {
              message.error('获取执行结果失败: ' + (e?.message || e));
            }
            setExecutingSetId(null);
          }
        } catch (err) {
          window.clearInterval(poll);
          setExecRunning(false);
          setExecModalVisible(false);
          message.error('轮询任务状态失败');
          setExecutingSetId(null);
        }
      }, 1000);
    } catch (e:any) {
      setExecRunning(false);
      setExecModalVisible(false);
      message.error('启动异步任务失败: ' + (e?.message || e));
      setExecutingSetId(null);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '名称', dataIndex: 'name', key: 'name', render: (v: string, r: EvalSet) => (
      editingId === r.id ? (
          <Input
            value={editingName}
            onChange={(e) => setEditingName(e.target.value)}
            onPressEnter={async () => {
              if (savingId === r.id) return;
              if (editingName.trim() === r.name.trim()) { setEditingId(null); setEditingName(''); return; }
              try {
                setSavingId(r.id);
                await api.patchEvalSet(r.id, { name: editingName });
                message.success('名称已更新');
                load();
              } catch (e: any) {
                message.error('更新失败: ' + (e?.message || e));
              } finally {
                setSavingId(null);
                setEditingId(null);
                setEditingName('');
              }
            }}
            onKeyDown={(e) => { if (e.key === 'Escape') { setEditingId(null); setEditingName(r.name); } }}
            onBlur={async () => {
              // save on blur
              if (savingId === r.id) return;
              if (editingName.trim() === r.name.trim()) { setEditingId(null); setEditingName(''); return; }
              try {
                setSavingId(r.id);
                await api.patchEvalSet(r.id, { name: editingName });
                message.success('名称已更新');
                load();
              } catch (e: any) {
                message.error('更新失败: ' + (e?.message || e));
              } finally {
                setSavingId(null);
                setEditingId(null);
                setEditingName('');
              }
            }}
            autoFocus
          />
        ) : (
        <Link to={`/set/${r.id}`}>{v}</Link>
      )
    ) },
    { title: '数量', dataIndex: 'count', key: 'count', width: 120 },
    { title: '操作', key: 'actions', width: 160, render: (_: any, rec: EvalSet) => (
      <Space>
        <Tooltip title={executingSetId === rec.id ? '执行中...' : '执行'}>
          <Button type="text" icon={<PlayCircleOutlined />} onClick={() => executeBySet(rec.id)} loading={executingSetId === rec.id} aria-label={`执行${rec.name}`} />
        </Tooltip>
        <Tooltip title="编辑">
          <Button type="text" icon={<EditOutlined />} onClick={() => { setEditingId(rec.id); setEditingName(rec.name); }} aria-label={`编辑${rec.name}`} />
        </Tooltip>
        <Tooltip title="删除">
          <Popconfirm title="确认删除?" onConfirm={() => del(rec.id)}>
            <Button type="text" danger icon={<DeleteOutlined />} aria-label={`删除${rec.name}`} />
          </Popconfirm>
        </Tooltip>
      </Space>
    ) }
  ];

  return (
    <div className="page-container">
      <h2>评测集</h2>
  <Card className="page-card">
        <Space className="flex-between">
          <Search placeholder="新评测集名称" enterButton="创建" value={name} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)} onSearch={create} className="search-max" />
          <Button onClick={() => load()}>刷新</Button>
        </Space>
      </Card>

      {error && (
        <ErrorBanner message={error} type="error" durationMs={8000} onClose={() => setError(null)} />
      )}

      <Card>
        {loading ? (
          <div>
            <Skeleton active paragraph={{ rows: 3 }} />
            <Skeleton active paragraph={{ rows: 2 }} />
          </div>
        ) : (
          <Table rowKey="id" dataSource={sets} columns={columns} pagination={false} />
        )}
      </Card>

      {execResult && (
    <Card className="page-card">
          <h3>执行结果</h3>
          <p>成功: {execResult.succeeded} / {execResult.total} 失败: {execResult.failed}</p>
          <p>耗时(ms): {execResult.durations_ms.join(', ')}</p>
          {execResult.errors.length > 0 && (
            <Collapse>
              <Collapse.Panel header={`错误列表 (${execResult.errors.length})`} key="errors">
                <List dataSource={execResult.errors} renderItem={item => <List.Item>{item}</List.Item>} />
              </Collapse.Panel>
            </Collapse>
          )}
          <Button onClick={()=>navigate(`/results/set/${executingSetId}`)}>查看最新结果</Button>
        </Card>
      )}
        <Modal title={execResult ? '执行完成' : '执行中'} open={execModalVisible} footer={null} onCancel={() => { if (!execRunning) setExecModalVisible(false); }} closable={!execRunning}>
          <div style={{ padding: 12 }}>
            <Progress percent={Math.round(execProgress)} status={execRunning ? 'active' : (execProgress === 100 ? 'success' : 'normal')} />
            {execResult && (
              <div style={{ marginTop: 12 }}>
                <p>成功: {execResult.succeeded} / {execResult.total} 失败: {execResult.failed}</p>
                {execResult.errors.length > 0 && <p style={{ color: '#d4380d' }}>错误: {execResult.errors.length} 条</p>}
                <div style={{ marginTop: 8 }}>
                  <Button type="primary" onClick={() => { setExecModalVisible(false); navigate(`/results/set/${execResult ? executingSetId : ''}`); }}>查看结果</Button>
                  <Button style={{ marginLeft: 8 }} onClick={() => setExecModalVisible(false)}>关闭</Button>
                </div>
              </div>
            )}
          </div>
        </Modal>
    </div>
  );
};

export default EvalSetsPage;
