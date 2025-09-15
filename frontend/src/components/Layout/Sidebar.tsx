import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Psychology as StrategyIcon,
  TrendingUp as TradingIcon,
  Security as RiskIcon,
  Settings as SettingsIcon,
  AccountBalance as BalanceIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant?: 'permanent' | 'persistent' | 'temporary';
}

const menuItems = [
  {
    text: '仪表板',
    icon: <DashboardIcon />,
    path: '/dashboard',
    badge: null,
  },
  {
    text: '策略管理',
    icon: <StrategyIcon />,
    path: '/strategies',
    badge: '3',
  },
  {
    text: '交易界面',
    icon: <TradingIcon />,
    path: '/trading',
    badge: null,
  },
  {
    text: '风险监控',
    icon: <RiskIcon />,
    path: '/risk',
    badge: '2',
  },
  {
    text: '系统设置',
    icon: <SettingsIcon />,
    path: '/settings',
    badge: null,
  },
];

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant = 'persistent' }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleItemClick = (path: string) => {
    navigate(path);
    if (variant === 'temporary') {
      onClose();
    }
  };

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: open ? 280 : 80,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: open ? 280 : 80,
          boxSizing: 'border-box',
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
          transition: 'width 0.3s ease',
          overflowX: 'hidden',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Logo */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            mb: 3,
            px: 1,
          }}
        >
          <BalanceIcon
            sx={{
              fontSize: 32,
              color: 'primary.main',
              mr: open ? 2 : 0,
            }}
          />
          {open && (
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #00D4AA 0%, #4DD4C1 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              YY交易系统 for OKX
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        {/* 菜单项 */}
        <List>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            
            return (
              <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  onClick={() => handleItemClick(item.path)}
                  sx={{
                    borderRadius: 2,
                    mx: 1,
                    py: 1.5,
                    px: 2,
                    backgroundColor: isActive
                      ? 'rgba(0, 212, 170, 0.1)'
                      : 'transparent',
                    border: isActive
                      ? '1px solid rgba(0, 212, 170, 0.3)'
                      : '1px solid transparent',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 212, 170, 0.05)',
                      border: '1px solid rgba(0, 212, 170, 0.2)',
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color: isActive ? 'primary.main' : 'text.secondary',
                      transition: 'color 0.2s ease',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  
                  {open && (
                    <>
                      <ListItemText
                        primary={item.text}
                        sx={{
                          '& .MuiListItemText-primary': {
                            fontWeight: isActive ? 600 : 500,
                            color: isActive ? 'primary.main' : 'text.primary',
                            fontSize: '0.875rem',
                          },
                        }}
                      />
                      {item.badge && (
                        <Chip
                          label={item.badge}
                          size="small"
                          sx={{
                            height: 20,
                            fontSize: '0.75rem',
                            backgroundColor: 'error.main',
                            color: 'white',
                            '& .MuiChip-label': {
                              px: 1,
                            },
                          }}
                        />
                      )}
                    </>
                  )}
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>

        {/* 系统状态 */}
        {open && (
          <Box
            sx={{
              mt: 4,
              p: 2,
              backgroundColor: 'rgba(0, 212, 170, 0.05)',
              borderRadius: 2,
              border: '1px solid rgba(0, 212, 170, 0.2)',
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              系统状态
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: 'success.main',
                  mr: 1,
                }}
              />
              <Typography variant="body2" color="text.primary">
                运行正常
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              最后更新: 刚刚
            </Typography>
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;
