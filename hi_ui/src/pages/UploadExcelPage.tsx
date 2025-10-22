import React, { useState } from 'react';
import { api } from '../api/client';
import { Upload, Button, message as antdMessage } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import ErrorBanner from '../components/ErrorBanner';
import { Progress } from 'antd';

const UploadExcelPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [progress, setProgress] = useState<number|null>(null);
  const submit = async () => {
    if (!file) { setError('请选择文件'); return; }
    setUploading(true); setError(null);
    try {
      const res: any = await api.uploadExcel(file);
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