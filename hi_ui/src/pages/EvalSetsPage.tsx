import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EvalSet, BatchExecResponse } from '../types';
import { Link, useNavigate } from 'react-router-dom';
import { Table, Input, Button, Card, Skeleton, Space, Popconfirm, message, List, Collapse } from 'antd';
import ErrorBanner from '../components/ErrorBanner';

const { Search } = Input;

const EvalSetsPage: React.FC = () => {
  const [sets, setSets] = useState<EvalSet[]>([]);
  const [name, setName] = useState('');
  const [executingSetId, setExecutingSetId] = useState<number | null>(null);
  const [execResult, setExecResult] = useState<BatchExecResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
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
    setExecutingSetId(id);
    setExecResult(null);
    try {
      const res: BatchExecResponse = await api.executeBySet(id);
      setExecResult(res);
      message.success(`集合 ${id} 执行完成`);
    } catch (e: any) {
      message.error('执行失败: ' + (e?.message || e));
    } finally {
      setExecutingSetId(null);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '名称', dataIndex: 'name', key: 'name', render: (v: string, r: EvalSet) => (<Link to={`/set/${r.id}`}>{v}</Link>) },
    { title: '数量', dataIndex: 'count', key: 'count', width: 120 },
    { title: '操作', key: 'actions', width: 300, render: (_: any, rec: EvalSet) => (
      <Space>
        <Button type="link" onClick={() => navigate(`/results/set/${rec.id}`)}>结果</Button>
        <Button disabled={!!executingSetId} onClick={() => executeBySet(rec.id)}>{executingSetId === rec.id ? '执行中...' : '执行'}</Button>
        <Popconfirm title="确认删除?" onConfirm={() => del(rec.id)}>
          <Button danger>删除</Button>
        </Popconfirm>
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
    </div>
  );
};

export default EvalSetsPage;
