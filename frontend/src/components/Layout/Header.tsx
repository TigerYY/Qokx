import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Badge,
  Menu,
  MenuItem,
  Avatar,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);
  const [darkMode, setDarkMode] = useState(true);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setNotificationAnchor(null);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleThemeToggle = () => {
    setDarkMode(!darkMode);
  };

  return (
    <AppBar
      position="static"
      sx={{
        backgroundColor: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: 'none',
      }}
    >
      <Toolbar>
        {/* 菜单按钮 */}
        <IconButton
          edge="start"
          color="inherit"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        {/* 标题 */}
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            background: 'linear-gradient(135deg, #00D4AA 0%, #4DD4C1 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          YY自动交易系统 for OKX
        </Typography>

        {/* 系统状态 */}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
          <Chip
            label="运行中"
            color="success"
            size="small"
            sx={{ mr: 1 }}
          />
          <Typography variant="caption" color="text.secondary">
            BTC-USDT
          </Typography>
        </Box>

        {/* 操作按钮 */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {/* 刷新按钮 */}
          <Tooltip title="刷新数据">
            <IconButton color="inherit" onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          {/* 主题切换 */}
          <Tooltip title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}>
            <IconButton color="inherit" onClick={handleThemeToggle}>
              {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {/* 通知 */}
          <Tooltip title="通知">
            <IconButton
              color="inherit"
              onClick={handleNotificationMenuOpen}
            >
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* 用户菜单 */}
          <Tooltip title="用户菜单">
            <IconButton
              color="inherit"
              onClick={handleProfileMenuOpen}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                <AccountIcon />
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>

        {/* 用户菜单 */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              mt: 1,
            },
          }}
        >
          <MenuItem onClick={handleMenuClose}>
            <AccountIcon sx={{ mr: 2 }} />
            个人资料
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            设置
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            退出登录
          </MenuItem>
        </Menu>

        {/* 通知菜单 */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              mt: 1,
              minWidth: 300,
            },
          }}
        >
          <MenuItem onClick={handleMenuClose}>
            <Box>
              <Typography variant="body2" color="text.primary">
                策略执行成功
              </Typography>
              <Typography variant="caption" color="text.secondary">
                2分钟前
              </Typography>
            </Box>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <Box>
              <Typography variant="body2" color="text.primary">
                风险预警触发
              </Typography>
              <Typography variant="caption" color="text.secondary">
                5分钟前
              </Typography>
            </Box>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <Box>
              <Typography variant="body2" color="text.primary">
                系统更新完成
              </Typography>
              <Typography variant="caption" color="text.secondary">
                1小时前
              </Typography>
            </Box>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
