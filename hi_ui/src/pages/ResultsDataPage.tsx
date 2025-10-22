import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import { EvalResult } from '../types';
import ErrorBanner from '../components/ErrorBanner';
import { Table, Button, Space } from 'antd';

const ResultsDataPage: React.FC = () => {
  const params = useParams();
  const setId = Number(params.setId);
  const corpusId = Number(params.corpusId);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const load = async () => {
    if (!setId || !corpusId) return;
    setLoading(true);
    try {
      setResults(await api.listResultsByData(setId, corpusId));
    } catch (e:any) {
      console.error('Failed to load results by data', e);
      setError(String(e?.message || e || '加载结果失败'));
    } finally { setLoading(false); }
  };
  useEffect(()=>{ load(); },[setId, corpusId]);
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '答案', dataIndex: 'actual_result', key: 'actual_result' },
    { title: '意图', dataIndex: 'actual_intent', key: 'actual_intent', width: 140 },
    { title: '分数', dataIndex: 'score', key: 'score', width: 100 },
    { title: 'KDB', dataIndex: 'kdb', key: 'kdb', width: 120 },
    { title: '版本', dataIndex: 'agent_version', key: 'agent_version', width: 120 },
    { title: '执行时间', dataIndex: 'exec_time', key: 'exec_time', width: 160 },
  ];

  return (
    <div>
  <h2>结果 - 集合 {setId} 数据 {corpusId}</h2>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      <Space className="list-margin">
        <Button onClick={load} disabled={loading}>{loading ? '刷新中...' : '刷新'}</Button>
      </Space>
      <Table rowKey="id" dataSource={results} columns={columns} pagination={false} />
    </div>
  );
};
export default ResultsDataPage;