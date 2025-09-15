import React, { useState } from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';

import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      {/* 侧边栏 */}
      <Sidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        variant={isMobile ? 'temporary' : 'permanent'}
      />
      
      {/* 主内容区域 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          width: isMobile ? '100%' : sidebarOpen ? 'calc(100% - 280px)' : 'calc(100% - 80px)',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {/* 顶部导航栏 */}
        <Header onMenuClick={handleSidebarToggle} />
        
        {/* 页面内容 */}
        <Box
          sx={{
            flexGrow: 1,
            padding: theme.spacing(3),
            background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
