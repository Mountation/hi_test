import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ConfigInfo } from '../types';
import { message, Form, Input, Button, Space } from 'antd';
import ErrorBanner from '../components/ErrorBanner';

const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<ConfigInfo | null>(null);
  const [editing, setEditing] = useState<Partial<ConfigInfo>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const load = async () => { try { const c = await api.getConfig(); setConfig(c); setEditing(c); } catch (e:any) { setError('加载失败: ' + (e?.message || e));} };
  useEffect(()=>{ load(); },[]);
  const save = async () => {
    setSaving(true);
    try {
      await api.updateConfig(editing);
      await load();
      message.success('保存成功');
    } catch (e:any) { setError('保存失败: ' + (e?.message || e)); } finally { setSaving(false); }
  };
  if (!config) return <div><h2>配置</h2><p>加载中...</p></div>;
  return (
    <div>
      <h2>配置管理</h2>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
  <Form layout="vertical" className="form-max">
        <Form.Item label="URL">
          <Input value={editing.url || ''} onChange={e => setEditing(prev => ({ ...prev, url: e.target.value }))} />
        </Form.Item>
        <Form.Item label="API KEY">
          <Input value={editing.api_key || ''} onChange={e => setEditing(prev => ({ ...prev, api_key: e.target.value }))} />
        </Form.Item>
        <Form.Item label="Hotline">
          <Input value={editing.hotline || ''} onChange={e => setEditing(prev => ({ ...prev, hotline: e.target.value }))} />
        </Form.Item>
        <Form.Item label="Userphone">
          <Input value={editing.userphone || ''} onChange={e => setEditing(prev => ({ ...prev, userphone: e.target.value }))} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" onClick={save} disabled={saving}>{saving ? '保存中...' : '保存'}</Button>
            <Button onClick={load} disabled={saving}>刷新</Button>
          </Space>
        </Form.Item>
      </Form>
  <p className="muted-note">配置文件路径: {config.path || '未知'} (修改后后端已自动重新加载)</p>
    </div>
  );
};
export default ConfigPage;