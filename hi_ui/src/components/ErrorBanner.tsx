import React, { useEffect } from 'react';
import { Alert } from 'antd';

type Props = {
  message: React.ReactNode;
  type?: 'error' | 'warning' | 'info' | 'success';
  durationMs?: number; // auto-dismiss after ms, 0 = never
  onClose?: () => void;
  className?: string;
};

const ErrorBanner: React.FC<Props> = ({ message, type = 'error', durationMs = 8000, onClose, className }) => {
  useEffect(() => {
    if (!durationMs || durationMs <= 0) return;
    const t = setTimeout(() => { onClose?.(); }, durationMs);
    return () => clearTimeout(t);
  }, [durationMs, onClose]);

  return (
    <div className={className} style={{ marginBottom: 12 }}>
      <Alert type={type} message={message} showIcon closable onClose={onClose} />
    </div>
  );
};

export default ErrorBanner;
