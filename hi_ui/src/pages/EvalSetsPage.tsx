import React, { useEffect, useState } from 'react';
import '../styles/hover.css';
import { api } from '../api/client';
import { EvalSet, BatchExecResponse } from '../types';
import { Link, useNavigate } from 'react-router-dom';
import { Table, Input, Button, Card, Skeleton, Space, Popconfirm, message, List, Collapse, Tooltip, Progress, Modal, Upload, Alert } from 'antd';
import { PlayCircleOutlined, DeleteOutlined, EditOutlined, UploadOutlined } from '@ant-design/icons';
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
  // import modal state
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [uploadFileList, setUploadFileList] = useState<any[]>([]);
  const [importName, setImportName] = useState('');
  const [importUploading, setImportUploading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importProgress, setImportProgress] = useState<number | null>(null);
  const [importProcessed, setImportProcessed] = useState<number | null>(null);
  const [importTotal, setImportTotal] = useState<number | null>(null);
  const [importActivity, setImportActivity] = useState<string[]>([]);
  const importPollRef = React.useRef<number | null>(null);

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

  // Creation of sets has been replaced by Excel import flow per UX change.

  // helper to open import modal with clean state
  const openImportModal = () => {
    setImportFile(null);
    setImportName('');
    setImportUploading(false);
    setImportError(null);
    setImportProgress(null);
    setImportProcessed(null);
    setImportTotal(null);
    setImportActivity([]);
    setUploadFileList([]);
    setImportModalVisible(true);
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
  { title: '序号', dataIndex: 'display_index', key: 'display_index', width: 80, render: (v: any, r: EvalSet) => (r.display_index && r.display_index > 0 ? r.display_index : r.id) },
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

  // auto-close import modal when progress hits 100
  useEffect(() => {
    if (importProgress === 100) {
      // clear polling if any
      if (importPollRef.current) {
        window.clearInterval(importPollRef.current);
        importPollRef.current = null;
      }
      setImportUploading(false);
      setImportModalVisible(false);
      setImportFile(null);
      setImportName('');
      setImportProgress(null);
      setImportProcessed(null);
      setImportTotal(null);
      setImportActivity([]);
      // refresh eval sets list
      load();
    }
  }, [importProgress]);

  return (
    <div className="page-container">
      <h2>评测集</h2>
  <Card className="page-card">
        <Space className="flex-between">
          <div>
            <Button type="primary" icon={<UploadOutlined />} onClick={() => openImportModal()}>导入评测集</Button>
          </div>
          <Button onClick={() => load()}>刷新</Button>
        </Space>
      </Card>

      {error && (
        <ErrorBanner message={error} type="error" durationMs={8000} onClose={() => setError(null)} />
      )}

      <Card className="page-card-hover" style={{ boxShadow: '0 4px 18px rgba(0,0,0,0.06)', borderRadius: 8 }} bodyStyle={{ padding: 12 }}>
        {loading ? (
          <div>
            <Skeleton active paragraph={{ rows: 3 }} />
            <Skeleton active paragraph={{ rows: 2 }} />
          </div>
        ) : (
          <Table
            rowKey="id"
            dataSource={sets}
            columns={columns}
            pagination={false}
            bordered
            size="middle"
            sticky={{ offsetHeader: 64 }}
            rowClassName={() => 'eval-row'}
          />
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
        {/* Import modal (migrated from standalone UploadExcelPage) */}
        <Modal
          title={<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <span>导入评测集（Excel）</span>
            {importTotal !== null ? (
              <span style={{ color: '#1890ff', fontWeight: 600 }}>{importProcessed ?? 0}/{importTotal}</span>
            ) : null}
          </div>}
          open={importModalVisible}
          onCancel={() => { if (!importUploading) { setImportModalVisible(false); setImportError(null); setImportProgress(null); } }}
          closable={!importUploading}
          footer={null}
          centered
          width={760}
          bodyStyle={{ padding: 20 }}
        >
          {/* Numeric progress indicator + small activity log (instead of a progress bar) */}
          {importTotal !== null && (
            <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ fontWeight: 600 }}>{importProcessed ?? 0} / {importTotal}</div>
              <div style={{ color: '#888' }}>{importUploading ? '正在导入...' : (importTotal !== null && importProcessed === importTotal ? '已完成' : '')}</div>
            </div>
          )}
          {importActivity.length > 0 && (
            <div style={{ marginBottom: 12, maxHeight: 120, overflow: 'auto', padding: 8, background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
              <List size="small" dataSource={importActivity} renderItem={item => <List.Item>{item}</List.Item>} />
            </div>
          )}
          <div>
            <Alert className="import-alert" type="info" showIcon style={{ marginBottom: 12 }} message={<strong>参考格式</strong>} description={<div>第一行为表头（会被忽略）；后续每行依次为：<b>content</b>（语料，必填）、<b>expected</b>（预期，选填）、<b>intent</b>（意图，选填）。<div style={{ marginTop:8 }}><a href="/import_template.xls" download>下载 Excel 模板</a></div></div>} />
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: 6 }}>评测集名称</label>
                <input disabled={importUploading} style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d9d9d9' }} value={importName} onChange={e => setImportName(e.target.value)} placeholder="填写评测集名称" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 6 }}>上传文件</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Upload
                    disabled={importUploading}
                    beforeUpload={(f: File) => { setImportFile(f); setUploadFileList([{ uid: '-1', name: f.name, status: 'done' }]); return false; }}
                    onRemove={() => { setImportFile(null); setUploadFileList([]); }}
                    fileList={uploadFileList}
                    maxCount={1}
                    accept=".xlsx,.xls"
                    showUploadList={false}
                  >
                    <Button icon={<UploadOutlined />} disabled={importUploading}>选择文件</Button>
                  </Upload>
                  {uploadFileList && uploadFileList.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ color: '#444', fontSize: 13, maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{uploadFileList[0].name}</span>
                      <Button type="link" size="small" onClick={() => { setImportFile(null); setUploadFileList([]); }} disabled={importUploading}>清除</Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {importError && <ErrorBanner message={importError} onClose={() => setImportError(null)} />}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
              <Button onClick={() => { setImportModalVisible(false); setImportError(null); setImportProgress(null); }} disabled={importUploading}>取消</Button>
              <Button type="primary" onClick={async () => {
                // submit import
                if (!importName) { setImportError('请填写评测集名称'); return; }
                if (!importFile) { setImportError('请选择文件'); return; }
                setImportUploading(true); setImportError(null);
                try {
                  const res: any = await api.uploadExcel(importFile, importName);
                  if (res && res.job_id) {
                    message.success('文件上传成功，开始后台导入');
                    const jobId = String(res.job_id);
                    const interval = window.setInterval(async () => {
                      try {
                        const st = await api.getJobStatus(jobId);
                        if (st.total && typeof st.processed === 'number') {
                          setImportProcessed(st.processed);
                          setImportTotal(st.total);
                          setImportProgress(Math.min(100, Math.round((st.processed / st.total) * 100)));
                          setImportActivity(prev => {
                            const msg = `已处理 ${st.processed}/${st.total}`;
                            const next = [msg, ...prev];
                            return next.slice(0, 6);
                          });
                        }
                        if (st.status === 'success') {
                          // ensure UI marks completion and triggers auto-close
                          setImportProgress(100);
                          setImportProcessed(st.processed ?? (st.total ?? 0));
                          setImportTotal(st.total ?? 0);
                          window.clearInterval(interval);
                          importPollRef.current = null;
                          message.success('导入完成');
                          setImportActivity(prev => [`导入完成: ${st.processed} 条`, ...prev].slice(0, 6));
                        }
                        if (st.status === 'failed') {
                          window.clearInterval(interval);
                          importPollRef.current = null;
                          setImportUploading(false);
                          setImportError('导入失败: ' + (st.errors ? st.errors.join(';') : '未知错误'));
                          setImportActivity(prev => [`导入失败: ${(st.errors && st.errors.length) ? st.errors.join(';') : '未知错误'}`, ...prev].slice(0, 6));
                        }
                      } catch (err: any) {
                        window.clearInterval(interval);
                        importPollRef.current = null;
                        setImportUploading(false);
                        setImportError('查询作业状态失败: ' + (err?.message || err));
                      }
                    }, 1500);
                    setImportActivity(['开始导入...', ...importActivity].slice(0, 6));
                    importPollRef.current = interval;
                  } else {
                    message.success('上传成功');
                    setImportModalVisible(false);
                    setImportFile(null);
                    setImportName('');
                    load();
                  }
                } catch (e: any) {
                  setImportError('上传失败: ' + (e?.message || e));
                } finally { setImportUploading(false); }
              }} disabled={importUploading}>{importUploading ? '上传中...' : '开始导入'}</Button>
            </div>
          {/* progress bar above already displays the status; avoid duplicate */}
          </div>
        </Modal>
        {/* auto-close handled by effect below */}
    </div>
  );
};

export default EvalSetsPage;
