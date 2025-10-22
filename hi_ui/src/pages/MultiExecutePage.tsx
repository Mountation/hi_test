import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EvalSet, MultiSetExecResponse } from '../types';
import { message, InputNumber, Button, List, Checkbox, Card, Space, Collapse } from 'antd';
import ErrorBanner from '../components/ErrorBanner';

const MultiExecutePage: React.FC = () => {
  const [sets, setSets] = useState<EvalSet[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [globalConcurrency, setGlobalConcurrency] = useState<number | ''>('');
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<MultiSetExecResponse | null>(null);
  const [error, setError] = useState<string|null>(null);
  const load = async () => { try { setSets(await api.getEvalSets()); } catch (e:any) { setError(String(e?.message||e)); } };
  useEffect(()=>{ load(); },[]);
  const toggle = (id:number) => setSelected(prev => prev.includes(id) ? prev.filter(x=>x!==id) : [...prev, id]);
  const execute = async () => {
    if (selected.length === 0) { setError('请选择至少一个评测集'); return; }
    setExecuting(true); setResult(null);
    try {
      const res: MultiSetExecResponse = await api.executeBySets(selected, globalConcurrency === '' ? undefined : Number(globalConcurrency));
      setResult(res);
    } catch (e:any) {
      setError('执行失败: ' + (e?.message || e));
    } finally {
      setExecuting(false);
    }
  };
  return (
    <div>
      <h2>多评测集执行</h2>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
  <Space className="form-inline">
        <span>全局并发:</span>
  <InputNumber className="input-number" min={1} value={globalConcurrency === '' ? undefined : globalConcurrency} onChange={(v:any) => setGlobalConcurrency(v === undefined ? '' : Number(v))} />
        <Button disabled={executing} type="primary" onClick={execute}>{executing ? '执行中...' : '开始执行'}</Button>
        <Button onClick={load} disabled={executing}>刷新集合</Button>
      </Space>

  <List grid={{ gutter: 8, column: 1 }} className="list-margin" dataSource={sets} renderItem={s => (
        <List.Item>
          <Card>
            <Checkbox checked={selected.includes(s.id)} onChange={() => toggle(s.id)}>{s.id} - {s.name} (数量 {s.count})</Checkbox>
          </Card>
        </List.Item>
      )} />

      {result && (
  <Card className="page-card result-card">
          <h3>总体结果</h3>
          <p>总计: {result.overall_total} 成功: {result.overall_succeeded} 失败: {result.overall_failed}</p>
          {result.sets.map(st => (
            <Collapse key={st.eval_set_id} className="collapse-margin">
              <Collapse.Panel header={`集合 ${st.eval_set_id} 成功 ${st.succeeded}/${st.total} 失败 ${st.failed}`} key={String(st.eval_set_id)}>
                <p>耗时(ms): {st.durations_ms.join(', ')}</p>
                {st.errors.length > 0 && <List dataSource={st.errors} renderItem={e => <List.Item>{e}</List.Item>} />}
              </Collapse.Panel>
            </Collapse>
          ))}
        </Card>
      )}
    </div>
  );
};
export default MultiExecutePage;