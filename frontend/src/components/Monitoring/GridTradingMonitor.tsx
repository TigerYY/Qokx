import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface GridLevel {
  level: number;
  price: number;
  quantity: number;
  order_type: 'buy' | 'sell';
  is_active: boolean;
  filled_quantity: number;
  avg_fill_price: number;
}

interface GridTradingState {
  current_price: number;
  total_position: number;
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_commission: number;
  active_orders: number;
  filled_orders: number;
  grid_levels: GridLevel[];
  last_update_time: string;
}

interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_commission: number;
  max_drawdown: number;
  current_position: number;
  active_grids: number;
  total_grids: number;
}

interface GridTradingMonitorProps {
  strategyId: string;
  symbol: string;
  onRefresh: () => void;
  onStart: () => void;
  onStop: () => void;
  onSettings: () => void;
}

const GridTradingMonitor: React.FC<GridTradingMonitorProps> = ({
  strategyId,
  symbol,
  onRefresh,
  onStart,
  onStop,
  onSettings,
}) => {
  const [state, setState] = useState<GridTradingState | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [expandedSections, setExpandedSections] = useState<string[]>(['overview']);
  const [selectedGridLevel, setSelectedGridLevel] = useState<GridLevel | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 模拟数据
  const mockState: GridTradingState = {
    current_price: 115851.5,
    total_position: 0.5,
    total_pnl: 1250.75,
    realized_pnl: 800.25,
    unrealized_pnl: 450.50,
    total_commission: 25.30,
    active_orders: 8,
    filled_orders: 12,
    grid_levels: [
      { level: 0, price: 115000, quantity: 0.1, order_type: 'buy', is_active: true, filled_quantity: 0, avg_fill_price: 0 },
      { level: 1, price: 115500, quantity: 0.1, order_type: 'buy', is_active: true, filled_quantity: 0, avg_fill_price: 0 },
      { level: 2, price: 116000, quantity: 0.1, order_type: 'sell', is_active: true, filled_quantity: 0, avg_fill_price: 0 },
      { level: 3, price: 116500, quantity: 0.1, order_type: 'sell', is_active: true, filled_quantity: 0, avg_fill_price: 0 },
      { level: 4, price: 117000, quantity: 0.1, order_type: 'sell', is_active: true, filled_quantity: 0, avg_fill_price: 0 },
    ],
    last_update_time: new Date().toISOString(),
  };

  const mockMetrics: PerformanceMetrics = {
    total_trades: 24,
    winning_trades: 16,
    losing_trades: 8,
    win_rate: 66.67,
    total_pnl: 1250.75,
    realized_pnl: 800.25,
    unrealized_pnl: 450.50,
    total_commission: 25.30,
    max_drawdown: 2.5,
    current_position: 0.5,
    active_grids: 8,
    total_grids: 10,
  };

  const mockPriceHistory = [
    { time: '09:00', price: 115200, pnl: 1200 },
    { time: '10:00', price: 115500, pnl: 1250 },
    { time: '11:00', price: 115800, pnl: 1300 },
    { time: '12:00', price: 115600, pnl: 1280 },
    { time: '13:00', price: 115900, pnl: 1320 },
    { time: '14:00', price: 115851.5, pnl: 1250.75 },
  ];

  useEffect(() => {
    // 模拟数据加载
    setState(mockState);
    setMetrics(mockMetrics);
    setPriceHistory(mockPriceHistory);
  }, []);

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      await onRefresh();
      // 模拟刷新延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
    } finally {
      setIsLoading(false);
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'success';
    if (pnl < 0) return 'error';
    return 'default';
  };

  const getGridStatusColor = (level: GridLevel) => {
    if (!level.is_active) return 'default';
    if (level.filled_quantity > 0) return 'success';
    return 'primary';
  };

  const renderOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              当前价格
            </Typography>
            <Typography variant="h4" component="div">
              ${state?.current_price.toLocaleString()}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <TrendingUpIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="body2" color="success.main">
                +2.5%
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              总盈亏
            </Typography>
            <Typography variant="h4" component="div" color={getPnLColor(state?.total_pnl || 0)}>
              ${state?.total_pnl.toLocaleString()}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <Typography variant="body2" color="textSecondary">
                已实现: ${state?.realized_pnl.toLocaleString()}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              当前持仓
            </Typography>
            <Typography variant="h4" component="div">
              {state?.total_position.toFixed(4)} {symbol.split('-')[0]}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <Typography variant="body2" color="textSecondary">
                价值: ${((state?.total_position || 0) * (state?.current_price || 0)).toLocaleString()}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              活跃网格
            </Typography>
            <Typography variant="h4" component="div">
              {metrics?.active_grids}/{metrics?.total_grids}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(metrics?.active_grids || 0) / (metrics?.total_grids || 1) * 100}
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderPerformanceMetrics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              交易统计
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography color="textSecondary">总交易数</Typography>
                <Typography variant="h6">{metrics?.total_trades}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">胜率</Typography>
                <Typography variant="h6" color="success.main">
                  {metrics?.win_rate.toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">盈利交易</Typography>
                <Typography variant="h6" color="success.main">
                  {metrics?.winning_trades}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">亏损交易</Typography>
                <Typography variant="h6" color="error.main">
                  {metrics?.losing_trades}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              风险指标
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography color="textSecondary">最大回撤</Typography>
                <Typography variant="h6" color="error.main">
                  {metrics?.max_drawdown.toFixed(2)}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">总手续费</Typography>
                <Typography variant="h6">
                  ${metrics?.total_commission.toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">已实现盈亏</Typography>
                <Typography variant="h6" color={getPnLColor(metrics?.realized_pnl || 0)}>
                  ${metrics?.realized_pnl.toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">未实现盈亏</Typography>
                <Typography variant="h6" color={getPnLColor(metrics?.unrealized_pnl || 0)}>
                  ${metrics?.unrealized_pnl.toFixed(2)}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderPriceChart = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          价格走势与盈亏
        </Typography>
        <Box sx={{ height: 300, mt: 2 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={priceHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="price"
                stroke="#8884d8"
                strokeWidth={2}
                name="价格"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="pnl"
                stroke="#82ca9d"
                strokeWidth={2}
                name="盈亏"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );

  const renderGridLevels = () => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">网格水平</Typography>
          <Typography variant="body2" color="textSecondary">
            当前价格: ${state?.current_price.toLocaleString()}
          </Typography>
        </Box>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>水平</TableCell>
                <TableCell>价格</TableCell>
                <TableCell>数量</TableCell>
                <TableCell>类型</TableCell>
                <TableCell>状态</TableCell>
                <TableCell>已成交</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {state?.grid_levels.map((level) => (
                <TableRow key={level.level}>
                  <TableCell>{level.level}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      ${level.price.toLocaleString()}
                      {level.price < (state?.current_price || 0) && level.order_type === 'buy' && (
                        <Chip
                          label="触发"
                          size="small"
                          color="success"
                          sx={{ ml: 1 }}
                        />
                      )}
                      {level.price > (state?.current_price || 0) && level.order_type === 'sell' && (
                        <Chip
                          label="触发"
                          size="small"
                          color="success"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>{level.quantity}</TableCell>
                  <TableCell>
                    <Chip
                      label={level.order_type.toUpperCase()}
                      size="small"
                      color={level.order_type === 'buy' ? 'success' : 'error'}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={level.is_active ? '活跃' : '已关闭'}
                      size="small"
                      color={getGridStatusColor(level)}
                    />
                  </TableCell>
                  <TableCell>
                    {level.filled_quantity > 0 ? (
                      <Box>
                        <Typography variant="body2">
                          {level.filled_quantity}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          @ ${level.avg_fill_price.toFixed(2)}
                        </Typography>
                      </Box>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="查看详情">
                      <IconButton
                        size="small"
                        onClick={() => setSelectedGridLevel(level)}
                      >
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );

  if (!state || !metrics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography>加载中...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* 操作栏 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          网格交易监控 - {symbol}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isLoading}
          >
            刷新
          </Button>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={onSettings}
          >
            设置
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={onStart}
            color="success"
          >
            启动
          </Button>
          <Button
            variant="contained"
            startIcon={<StopIcon />}
            onClick={onStop}
            color="error"
          >
            停止
          </Button>
        </Box>
      </Box>

      {/* 概览 */}
      <Accordion
        expanded={expandedSections.includes('overview')}
        onChange={() => handleSectionToggle('overview')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">概览</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {renderOverview()}
        </AccordionDetails>
      </Accordion>

      {/* 性能指标 */}
      <Accordion
        expanded={expandedSections.includes('performance')}
        onChange={() => handleSectionToggle('performance')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">性能指标</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {renderPerformanceMetrics()}
        </AccordionDetails>
      </Accordion>

      {/* 价格图表 */}
      <Accordion
        expanded={expandedSections.includes('chart')}
        onChange={() => handleSectionToggle('chart')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">价格走势</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {renderPriceChart()}
        </AccordionDetails>
      </Accordion>

      {/* 网格水平 */}
      <Accordion
        expanded={expandedSections.includes('grids')}
        onChange={() => handleSectionToggle('grids')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">网格水平</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {renderGridLevels()}
        </AccordionDetails>
      </Accordion>

      {/* 网格详情对话框 */}
      <Dialog
        open={!!selectedGridLevel}
        onClose={() => setSelectedGridLevel(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>网格详情</DialogTitle>
        <DialogContent>
          {selectedGridLevel && (
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography color="textSecondary">水平</Typography>
                <Typography variant="h6">{selectedGridLevel.level}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">价格</Typography>
                <Typography variant="h6">${selectedGridLevel.price.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">数量</Typography>
                <Typography variant="h6">{selectedGridLevel.quantity}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">类型</Typography>
                <Typography variant="h6">{selectedGridLevel.order_type.toUpperCase()}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">状态</Typography>
                <Chip
                  label={selectedGridLevel.is_active ? '活跃' : '已关闭'}
                  color={getGridStatusColor(selectedGridLevel)}
                />
              </Grid>
              <Grid item xs={6}>
                <Typography color="textSecondary">已成交</Typography>
                <Typography variant="h6">{selectedGridLevel.filled_quantity}</Typography>
              </Grid>
              {selectedGridLevel.filled_quantity > 0 && (
                <Grid item xs={12}>
                  <Typography color="textSecondary">平均成交价</Typography>
                  <Typography variant="h6">${selectedGridLevel.avg_fill_price.toFixed(2)}</Typography>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedGridLevel(null)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GridTradingMonitor;
