import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Security,
  Speed,
  Memory,
  Cloud,
} from '@mui/icons-material';

interface SystemStatusProps {
  status?: 'healthy' | 'warning' | 'error' | 'offline';
}

const SystemStatus: React.FC<SystemStatusProps> = ({ 
  status = 'healthy' 
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'offline':
        return 'default';
      default:
        return 'success';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'warning':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'error':
        return <Error sx={{ color: 'error.main' }} />;
      case 'offline':
        return <Error sx={{ color: 'text.secondary' }} />;
      default:
        return <CheckCircle sx={{ color: 'success.main' }} />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '系统正常';
      case 'warning':
        return '系统警告';
      case 'error':
        return '系统错误';
      case 'offline':
        return '系统离线';
      default:
        return '系统正常';
    }
  };

  // 模拟系统指标
  const systemMetrics = [
    {
      name: 'API连接',
      status: 'healthy',
      value: 100,
      icon: <Cloud />,
    },
    {
      name: '数据库',
      status: 'healthy',
      value: 95,
      icon: <Memory />,
    },
    {
      name: '交易引擎',
      status: 'healthy',
      value: 100,
      icon: <Speed />,
    },
    {
      name: '风险监控',
      status: 'warning',
      value: 85,
      icon: <Security />,
    },
  ];

  const recentEvents = [
    {
      time: '15:30',
      message: '策略执行成功',
      type: 'success',
    },
    {
      time: '15:25',
      message: '风险预警触发',
      type: 'warning',
    },
    {
      time: '15:20',
      message: '数据同步完成',
      type: 'success',
    },
    {
      time: '15:15',
      message: '系统启动完成',
      type: 'success',
    },
  ];

  return (
    <Card
      sx={{
        background: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 3,
        height: '100%',
      }}
    >
      <CardContent>
        {/* 系统状态 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            系统状态
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            {getStatusIcon(status)}
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {getStatusText(status)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                最后更新: 刚刚
              </Typography>
            </Box>
            <Chip
              label={getStatusText(status)}
              color={getStatusColor(status)}
              size="small"
              sx={{ ml: 'auto' }}
            />
          </Box>
        </Box>

        <Divider sx={{ mb: 3, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        {/* 系统指标 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
            系统指标
          </Typography>
          {systemMetrics.map((metric, index) => (
            <Box key={index} sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {metric.icon}
                  <Typography variant="body2" color="text.primary">
                    {metric.name}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {metric.value}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={metric.value}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: metric.status === 'healthy' ? 'success.main' : 'warning.main',
                    borderRadius: 3,
                  },
                }}
              />
            </Box>
          ))}
        </Box>

        <Divider sx={{ mb: 3, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        {/* 最近事件 */}
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
            最近事件
          </Typography>
          <List dense>
            {recentEvents.map((event, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: event.type === 'success' ? 'success.main' : 'warning.main',
                    }}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.primary">
                      {event.message}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {event.time}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemStatus;
