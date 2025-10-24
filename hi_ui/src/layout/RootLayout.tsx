import React from 'react';
import { Layout, Menu, theme } from 'antd';
import { DatabaseOutlined, DashboardOutlined, ThunderboltOutlined, SettingOutlined, UploadOutlined, ExperimentOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';

const { Sider, Header, Content, Footer } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/sets', icon: <DatabaseOutlined />, label: '评测集' },
  { key: '/multi-execute', icon: <ThunderboltOutlined />, label: '多集合执行' },
  { key: '/config', icon: <SettingOutlined />, label: '配置' },
];

export const RootLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" collapsible>
        <div style={{ height: 48, margin: 16, display:'flex', alignItems:'center', justifyContent:'center', color: '#fff', fontWeight:600, letterSpacing:1 }}>AI Eval</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname.startsWith('/set/') ? '/sets' : location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: 'linear-gradient(90deg,#001f3f,#003b7a,#0056b3)', color: '#fff', display:'flex', alignItems:'center', gap:16 }}>
          <ExperimentOutlined style={{ fontSize:24 }} />
          <span style={{ fontSize:18, fontWeight:500 }}>AI 评测控制台</span>
        </Header>
        <Content style={{ margin: '16px', overflow:'auto' }}>
          <div style={{ padding: 24, background: token.colorBgContainer, borderRadius: 8, boxShadow:'0 4px 16px rgba(0,0,0,0.25)' }}>
            {children}
          </div>
        </Content>
        <Footer style={{ textAlign:'center' }}>AI Eval ©2025 创新加速 · 版本 v0.1.0</Footer>
      </Layout>
    </Layout>
  );
};

export default RootLayout;