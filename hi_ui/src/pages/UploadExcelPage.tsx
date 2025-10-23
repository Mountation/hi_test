import React, { useState } from 'react';
import { api } from '../api/client';
import { Upload, Button, message as antdMessage } from 'antd';
import { Alert } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import ErrorBanner from '../components/ErrorBanner';
import { Progress } from 'antd';

const UploadExcelPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [progress, setProgress] = useState<number|null>(null);
  const submit = async () => {
    if (!name) { setError('请填写评测集名称'); return; }
    if (!file) { setError('请选择文件'); return; }
    setUploading(true); setError(null);
    try {
      const res: any = await api.uploadExcel(file, name);
      // If backend returns job_id, poll its status
      if (res && res.job_id) {
        antdMessage.success('文件上传成功，开始后台导入');
        const jobId = String(res.job_id);
        let stopped = false;
        const interval = setInterval(async () => {
          try {
            const st = await api.getJobStatus(jobId);
            if (st.total && typeof st.processed === 'number') {
              // update progress
              setProgress(Math.min(100, Math.round((st.processed / st.total) * 100)));
            }
            if (st.status === 'success') {
              clearInterval(interval);
              stopped = true;
              antdMessage.success('导入完成');
            }
            if (st.status === 'failed') {
              clearInterval(interval);
              stopped = true;
              setError('导入失败: ' + (st.errors ? st.errors.join(';') : '未知错误'));
            }
          } catch (err:any) {
            clearInterval(interval);
            stopped = true;
            setError('查询作业状态失败: ' + (err?.message || err));
          }
        }, 1500);
      } else {
        antdMessage.success('上传成功');
      }
    } catch (e:any) {
      setError('上传失败: ' + (e?.message || e));
    } finally { setUploading(false); }
  };
  const beforeUpload = (f: File) => {
    setFile(f);
    return false; // prevent auto upload
  };
  return (
    <div>
      <h2>Excel 导入评测数据</h2>
      <Alert className="import-alert" type="info" showIcon closable style={{ marginBottom: 12 }} message={<strong>导入说明（Excel 格式）</strong>} description={<div>第一行为表头（会被忽略）；后续每行列依次为：<b>content</b>（语料），<b>expected</b>（期望，可选），<b>intent</b>（意图，可选）。<div style={{ marginTop:8 }}><a href="/import_template.xls" download>下载 Excel 模板（可直接用 Excel 打开）</a></div></div>} />
      <div style={{ marginBottom: 12 }}>
        <label>评测集名称: </label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="填写评测集名称" />
      </div>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      <Upload beforeUpload={beforeUpload} maxCount={1} accept=".xlsx,.xls">
        <Button icon={<UploadOutlined />}>选择文件</Button>
      </Upload>
  <Button onClick={submit} disabled={uploading} className="compact-button">{uploading ? '上传中...' : '上传'}</Button>
  {progress !== null && <div style={{ marginTop: 12 }}><Progress percent={progress} /></div>}
  <p className="muted-note">Excel 第一行为表头，需包含必要列 (如 content, expected, intent 等)。</p>
    </div>
  );
};
export default UploadExcelPage;