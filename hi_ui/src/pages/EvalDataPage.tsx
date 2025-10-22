import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { EvalData } from '../types';
import ErrorBanner from '../components/ErrorBanner';
import { message, Popconfirm, Button, Table, Form, Input, Space } from 'antd';

const EvalDataPage: React.FC = () => {
  const { id } = useParams();
  const setId = Number(id);
  const [data, setData] = useState<EvalData[]>([]);
  const [content, setContent] = useState('');
  const [expected, setExpected] = useState('');
  const [intent, setIntent] = useState('');
  const [executingId, setExecutingId] = useState<number | null>(null);
  const [error, setError] = useState<string|null>(null);
  const load = async () => {
    try { setData(await api.listEvalData(setId)); } catch (e:any) { setError(String(e?.message || e || '加载失败')); }
  };
  useEffect(() => { if (setId) load(); }, [setId]);
  const create = async () => { if (!content) return; try { await api.createEvalData(setId, { content, expected, intent }); setContent(''); setExpected(''); setIntent(''); load(); } catch (e:any) { setError(String(e?.message||e)); } };
  const del = async (dataId: number) => { try { await api.deleteEvalData(setId, dataId); load(); } catch (e:any) { setError(String(e?.message||e)); } };
  const executeSingle = async (dataId: number) => {
    setExecutingId(dataId);
    try {
      await api.executeSingle(dataId);
      message.success('执行完成');
    } catch (e:any) {
      setError('执行失败: ' + (e?.message || e));
    } finally {
      setExecutingId(null);
    }
  };
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '内容', dataIndex: 'content', key: 'content' },
    { title: '预期', dataIndex: 'expected', key: 'expected' },
    { title: '意图', dataIndex: 'intent', key: 'intent', width: 140 },
    {
      title: '操作', key: 'actions', width: 260, render: (_: any, record: any) => (
        <Space>
          <Link to={`/results/data/${setId}/${record.corpus_id ?? record.id}`}>结果</Link>
          <Button size="small" disabled={!!executingId} onClick={() => executeSingle(record.id)}>{executingId === record.id ? '执行中...' : '执行'}</Button>
          <Popconfirm title="确认删除?" onConfirm={() => del(record.id)} okText="是" cancelText="否">
            <Button danger size="small">删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div className="page-container">
      <h2>评测数据 - 集合 {setId}</h2>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

      <Form layout="inline" className="form-inline" onFinish={create}>
  <Form.Item className="flex-item">
          <Input placeholder="语料" value={content} onChange={e => setContent(e.target.value)} />
        </Form.Item>
  <Form.Item className="flex-item">
          <Input placeholder="预期结果" value={expected} onChange={e => setExpected(e.target.value)} />
        </Form.Item>
  <Form.Item className="flex-item-small">
          <Input placeholder="意图" value={intent} onChange={e => setIntent(e.target.value)} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">新增</Button>
        </Form.Item>
        <Form.Item>
          <Button onClick={() => { /* intentional nav link kept */ }}> <Link to={`/results/set/${setId}`}>查看结果</Link> </Button>
        </Form.Item>
      </Form>

      <Table rowKey="id" dataSource={data} columns={columns} pagination={false} />
    </div>
  );
};
export default EvalDataPage;
