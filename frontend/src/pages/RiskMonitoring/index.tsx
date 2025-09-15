import React, { useState } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Warning,
  Error,
  CheckCircle,
  Security,
  TrendingDown,
  Speed,
  Refresh,
} from '@mui/icons-material';

import MetricCard from '@/components/UI/MetricCard';
import DataTable from '@/components/UI/DataTable';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`risk-tabpanel-${index}`}
      aria-labelledby={`risk-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RiskMonitoring: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  // 模拟风险数据
  const riskMetrics = {
    currentRiskLevel: 'medium',
    maxDrawdown: 3.2,
    volatility: 12.5,
    var95: 2.1,
    var99: 3.8,
    sharpeRatio: 1.85,
    sortinoRatio: 2.1,
  };

  const riskEvents = [
    {
      id: '1',
      eventType: 'HIGH_DRAWDOWN',
      severity: 'HIGH',
      message: '最大回撤超过阈值',
      strategyId: 'signal_fusion_strategy',
      timestamp: '2024-01-07 15:30:00',
      isResolved: false,
    },
    {
      id: '2',
      eventType: 'LOW_LIQUIDITY',
      severity: 'MEDIUM',
      message: '市场流动性不足',
      strategyId: 'market_state_strategy',
      timestamp: '2024-01-07 14:15:00',
      isResolved: true,
    },
    {
      id: '3',
      eventType: 'API_ERROR',
      severity: 'LOW',
      message: 'API连接异常',
      strategyId: 'grid_trading_strategy',
      timestamp: '2024-01-07 13:45:00',
      isResolved: true,
    },
  ];

  const riskLimits = [
    {
      name: '最大回撤',
      current: 3.2,
      limit: 5.0,
      unit: '%',
      status: 'warning',
    },
    {
      name: '单日损失',
      current: 1.8,
      limit: 3.0,
      unit: '%',
      status: 'normal',
    },
    {
      name: '仓位集中度',
      current: 25.5,
      limit: 30.0,
      unit: '%',
      status: 'normal',
    },
    {
      name: '杠杆倍数',
      current: 1.2,
      limit: 2.0,
      unit: 'x',
      status: 'normal',
    },
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return <Error sx={{ color: 'error.main' }} />;
      case 'MEDIUM':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'LOW':
        return <CheckCircle sx={{ color: 'info.main' }} />;
      default:
        return <CheckCircle sx={{ color: 'text.secondary' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'danger':
        return 'error';
      default:
        return 'default';
    }
  };

  // 风险事件表格列定义
  const eventColumns = [
    {
      id: 'severity',
      label: '严重程度',
      minWidth: 100,
      format: (value: string) => (
        <Chip
          label={value}
          color={getSeverityColor(value)}
          size="small"
          icon={getSeverityIcon(value)}
        />
      ),
    },
    {
      id: 'eventType',
      label: '事件类型',
      minWidth: 150,
      format: (value: string) => (
        <Typography variant="body2">
          {value.replace(/_/g, ' ')}
        </Typography>
      ),
    },
    {
      id: 'message',
      label: '描述',
      minWidth: 200,
    },
    {
      id: 'strategyId',
      label: '策略ID',
      minWidth: 150,
    },
    {
      id: 'timestamp',
      label: '时间',
      minWidth: 150,
    },
    {
      id: 'isResolved',
      label: '状态',
      minWidth: 100,
      format: (value: boolean) => (
        <Chip
          label={value ? '已解决' : '未解决'}
          color={value ? 'success' : 'warning'}
          size="small"
        />
      ),
    },
  ];

  return (
    <Box>
      {/* 页面标题和操作 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            风险监控
          </Typography>
          <Typography variant="body2" color="text.secondary">
            实时监控交易风险和系统状态
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
        >
          刷新数据
        </Button>
      </Box>

      {/* 风险概览卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="风险等级"
            value={riskMetrics.currentRiskLevel.toUpperCase()}
            icon={<Security />}
            color="warning"
            subtitle="当前风险水平"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="最大回撤"
            value={`${riskMetrics.maxDrawdown}%`}
            icon={<TrendingDown />}
            color="error"
            subtitle="历史最大回撤"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="夏普比率"
            value={riskMetrics.sharpeRatio.toFixed(2)}
            icon={<Speed />}
            color="success"
            subtitle="风险调整收益"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="VaR (95%)"
            value={`${riskMetrics.var95}%`}
            icon={<Warning />}
            color="info"
            subtitle="在险价值"
          />
        </Grid>
      </Grid>

      {/* 风险限制监控 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                风险限制监控
              </Typography>
              {riskLimits.map((limit, index) => (
                <Box key={index} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.primary">
                      {limit.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {limit.current}{limit.unit} / {limit.limit}{limit.unit}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(limit.current / limit.limit) * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getStatusColor(limit.status) === 'success' ? 'success.main' : 
                                       getStatusColor(limit.status) === 'warning' ? 'warning.main' : 'error.main',
                        borderRadius: 4,
                      },
                    }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      使用率: {((limit.current / limit.limit) * 100).toFixed(1)}%
                    </Typography>
                    <Chip
                      label={limit.status === 'normal' ? '正常' : limit.status === 'warning' ? '警告' : '危险'}
                      color={getStatusColor(limit.status)}
                      size="small"
                    />
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                风险指标
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="波动率"
                    secondary={`${riskMetrics.volatility}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="VaR (99%)"
                    secondary={`${riskMetrics.var99}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Sortino比率"
                    secondary={riskMetrics.sortinoRatio.toFixed(2)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="最大连续亏损"
                    secondary="5笔"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="平均持仓时间"
                    secondary="2.5小时"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 风险事件和告警 */}
      <Card
        sx={{
          background: 'rgba(26, 26, 26, 0.8)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
        }}
      >
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="风险事件" />
            <Tab label="活跃告警" />
            <Tab label="历史告警" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <DataTable
            columns={eventColumns}
            data={riskEvents}
            page={0}
            rowsPerPage={10}
            totalRows={riskEvents.length}
            onPageChange={() => {}}
            onRowsPerPageChange={() => {}}
            loading={false}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 3 }}>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>风险预警:</strong> 最大回撤已达到 3.2%，接近 5% 的限制阈值。
              </Typography>
            </Alert>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>系统提示:</strong> 建议降低仓位或调整风险参数。
              </Typography>
            </Alert>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">
              暂无历史告警记录
            </Typography>
          </Box>
        </TabPanel>
      </Card>
    </Box>
  );
};

export default RiskMonitoring;
