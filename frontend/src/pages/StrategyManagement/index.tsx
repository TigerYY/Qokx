import React, { useState } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Psychology as StrategyIcon,
  TrendingUp as PerformanceIcon,
  Security as RiskIcon,
} from '@mui/icons-material';

import DataTable from '@/components/UI/DataTable';
import MetricCard from '@/components/UI/MetricCard';
import { useStrategies, useStartStrategy, useStopStrategy } from '@/hooks/useTradingData';

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
      id={`strategy-tabpanel-${index}`}
      aria-labelledby={`strategy-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const StrategyManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const { data: strategies, isLoading } = useStrategies();
  const startStrategyMutation = useStartStrategy();
  const stopStrategyMutation = useStopStrategy();

  // 模拟数据
  const mockStrategies = [
    {
      id: '1',
      name: '信号融合策略',
      version: '1.0.0',
      description: '基于多时间框架信号融合的交易策略',
      status: 'active',
      isActive: true,
      isTesting: false,
      totalReturn: 12.5,
      sharpeRatio: 1.85,
      maxDrawdown: 3.2,
      winRate: 68.5,
      totalTrades: 1247,
      created: '2024-01-01',
      updated: '2024-01-07',
    },
    {
      id: '2',
      name: '市场状态检测策略',
      version: '1.1.0',
      description: '自动识别市场状态并调整交易参数',
      status: 'testing',
      isActive: false,
      isTesting: true,
      totalReturn: 8.3,
      sharpeRatio: 1.42,
      maxDrawdown: 5.1,
      winRate: 62.1,
      totalTrades: 892,
      created: '2024-01-03',
      updated: '2024-01-07',
    },
    {
      id: '3',
      name: '网格交易策略',
      version: '0.9.0',
      description: '在价格区间内进行网格化买卖',
      status: 'inactive',
      isActive: false,
      isTesting: false,
      totalReturn: 5.7,
      sharpeRatio: 0.98,
      maxDrawdown: 7.8,
      winRate: 58.3,
      totalTrades: 456,
      created: '2024-01-05',
      updated: '2024-01-06',
    },
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, strategy: any) => {
    setAnchorEl(event.currentTarget);
    setSelectedStrategy(strategy);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedStrategy(null);
  };

  const handleStartStrategy = (strategyId: string) => {
    startStrategyMutation.mutate({ strategyId });
    handleMenuClose();
  };

  const handleStopStrategy = (strategyId: string) => {
    stopStrategyMutation.mutate(strategyId);
    handleMenuClose();
  };

  const handleEditStrategy = (strategy: any) => {
    setSelectedStrategy(strategy);
    setEditDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteStrategy = (strategyId: string | undefined) => {
    if (!strategyId) {
      console.warn('无法删除策略：ID 未定义');
      return;
    }
    // 实现删除策略逻辑
    console.log('删除策略:', strategyId);
    handleMenuClose();
  };

  // 表格列定义
  const columns = [
    {
      id: 'name',
      label: '策略名称',
      minWidth: 150,
      format: (value: string, row: any) => (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {value}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            v{row?.version || 'N/A'}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'description',
      label: '描述',
      minWidth: 200,
      format: (value: string) => (
        <Typography variant="body2" color="text.secondary" noWrap>
          {value}
        </Typography>
      ),
    },
    {
      id: 'status',
      label: '状态',
      minWidth: 100,
      align: 'center' as const,
      format: (value: string) => {
        const getStatusColor = (status: string) => {
          switch (status) {
            case 'active':
              return 'success';
            case 'testing':
              return 'warning';
            case 'inactive':
              return 'default';
            default:
              return 'default';
          }
        };
        const getStatusText = (status: string) => {
          switch (status) {
            case 'active':
              return '运行中';
            case 'testing':
              return '测试中';
            case 'inactive':
              return '已停止';
            default:
              return '未知';
          }
        };
        return (
          <Chip
            label={getStatusText(value)}
            color={getStatusColor(value)}
            size="small"
          />
        );
      },
    },
    {
      id: 'totalReturn',
      label: '总收益',
      minWidth: 100,
      align: 'right' as const,
      format: (value: number) => (
        <Typography
          variant="body2"
          color={value >= 0 ? 'success.main' : 'error.main'}
          sx={{ fontWeight: 600 }}
        >
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </Typography>
      ),
    },
    {
      id: 'sharpeRatio',
      label: '夏普比率',
      minWidth: 100,
      align: 'right' as const,
      format: (value: number) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {value.toFixed(2)}
        </Typography>
      ),
    },
    {
      id: 'winRate',
      label: '胜率',
      minWidth: 80,
      align: 'right' as const,
      format: (value: number) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {value.toFixed(1)}%
        </Typography>
      ),
    },
    {
      id: 'totalTrades',
      label: '交易次数',
      minWidth: 100,
      align: 'right' as const,
      format: (value: number) => (
        <Typography variant="body2">
          {value.toLocaleString()}
        </Typography>
      ),
    },
  ];

  return (
    <Box>
      {/* 页面标题和操作 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            策略管理
          </Typography>
          <Typography variant="body2" color="text.secondary">
            管理和监控您的交易策略
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          创建策略
        </Button>
      </Box>

      {/* 策略概览卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="总策略数"
            value={mockStrategies.length}
            icon={<StrategyIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="运行中"
            value={mockStrategies.filter(s => s.status === 'active').length}
            icon={<PlayIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="测试中"
            value={mockStrategies.filter(s => s.status === 'testing').length}
            icon={<PerformanceIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="平均收益"
            value={`${(mockStrategies.reduce((sum, s) => sum + s.totalReturn, 0) / mockStrategies.length).toFixed(1)}%`}
            icon={<PerformanceIcon />}
            color="info"
          />
        </Grid>
      </Grid>

      {/* 策略列表 */}
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
            <Tab label="所有策略" />
            <Tab label="运行中" />
            <Tab label="测试中" />
            <Tab label="已停止" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <DataTable
            columns={columns}
            data={mockStrategies}
            page={0}
            rowsPerPage={10}
            totalRows={mockStrategies.length}
            onPageChange={() => {}}
            onRowsPerPageChange={() => {}}
            actions={{
              view: (row) => console.log('查看策略:', row),
              edit: (row) => handleEditStrategy(row),
              delete: (row) => handleDeleteStrategy(row?.id),
            }}
            loading={isLoading}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <DataTable
            columns={columns}
            data={mockStrategies.filter(s => s.status === 'active')}
            page={0}
            rowsPerPage={10}
            totalRows={mockStrategies.filter(s => s.status === 'active').length}
            onPageChange={() => {}}
            onRowsPerPageChange={() => {}}
            actions={{
              view: (row) => console.log('查看策略:', row),
              edit: (row) => handleEditStrategy(row),
              delete: (row) => handleDeleteStrategy(row?.id),
            }}
            loading={isLoading}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <DataTable
            columns={columns}
            data={mockStrategies.filter(s => s.status === 'testing')}
            page={0}
            rowsPerPage={10}
            totalRows={mockStrategies.filter(s => s.status === 'testing').length}
            onPageChange={() => {}}
            onRowsPerPageChange={() => {}}
            actions={{
              view: (row) => console.log('查看策略:', row),
              edit: (row) => handleEditStrategy(row),
              delete: (row) => handleDeleteStrategy(row?.id),
            }}
            loading={isLoading}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <DataTable
            columns={columns}
            data={mockStrategies.filter(s => s.status === 'inactive')}
            page={0}
            rowsPerPage={10}
            totalRows={mockStrategies.filter(s => s.status === 'inactive').length}
            onPageChange={() => {}}
            onRowsPerPageChange={() => {}}
            actions={{
              view: (row) => console.log('查看策略:', row),
              edit: (row) => handleEditStrategy(row),
              delete: (row) => handleDeleteStrategy(row?.id),
            }}
            loading={isLoading}
          />
        </TabPanel>
      </Card>

      {/* 操作菜单 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        {selectedStrategy?.status === 'active' ? (
          <MenuItem onClick={() => handleStopStrategy(selectedStrategy.id)}>
            <StopIcon sx={{ mr: 1 }} />
            停止策略
          </MenuItem>
        ) : (
          <MenuItem onClick={() => handleStartStrategy(selectedStrategy?.id)}>
            <PlayIcon sx={{ mr: 1 }} />
            启动策略
          </MenuItem>
        )}
        <MenuItem onClick={() => handleEditStrategy(selectedStrategy)}>
          <EditIcon sx={{ mr: 1 }} />
          编辑策略
        </MenuItem>
        <MenuItem onClick={() => handleDeleteStrategy(selectedStrategy?.id)}>
          <DeleteIcon sx={{ mr: 1 }} />
          删除策略
        </MenuItem>
      </Menu>

      {/* 创建策略对话框 */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <DialogTitle>创建新策略</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="策略名称"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="描述"
                variant="outlined"
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="版本"
                variant="outlined"
                defaultValue="1.0.0"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>策略类型</InputLabel>
                <Select
                  label="策略类型"
                  defaultValue="signal_fusion"
                >
                  <MenuItem value="signal_fusion">信号融合策略</MenuItem>
                  <MenuItem value="market_state">市场状态检测</MenuItem>
                  <MenuItem value="grid_trading">网格交易</MenuItem>
                  <MenuItem value="dca">定投策略</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="创建后立即启动"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>
            取消
          </Button>
          <Button variant="contained" onClick={() => setCreateDialogOpen(false)}>
            创建
          </Button>
        </DialogActions>
      </Dialog>

      {/* 编辑策略对话框 */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <DialogTitle>编辑策略</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="策略名称"
                variant="outlined"
                defaultValue={selectedStrategy?.name}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="描述"
                variant="outlined"
                multiline
                rows={3}
                defaultValue={selectedStrategy?.description}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="版本"
                variant="outlined"
                defaultValue={selectedStrategy?.version}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>状态</InputLabel>
                <Select
                  label="状态"
                  defaultValue={selectedStrategy?.status}
                >
                  <MenuItem value="active">运行中</MenuItem>
                  <MenuItem value="testing">测试中</MenuItem>
                  <MenuItem value="inactive">已停止</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            取消
          </Button>
          <Button variant="contained" onClick={() => setEditDialogOpen(false)}>
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategyManagement;
