import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Psychology,
  Security,
  Refresh,
} from '@mui/icons-material';

import MetricCard from '@/components/UI/MetricCard';
import PriceChart from '@/components/Charts/PriceChart';
import PerformanceChart from '@/components/Charts/PerformanceChart';
import RecentTrades from '@/components/Trading/RecentTrades';
import SystemStatus from '@/components/System/SystemStatus';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useTradingData } from '@/hooks/useTradingData';
import { Trade } from '@/types';
import { api } from '@/services/api';

const Dashboard: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  const [priceData, setPriceData] = useState<Array<{time: string; price: number}>>([]);
  const [tickerData, setTickerData] = useState<any>(null);
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1H');
  const { data: tradingData, isLoading, refetch } = useTradingData();
  const { lastMessage } = useWebSocket('ws://localhost:8000/ws');

  // 获取真实价格数据
  const fetchPriceData = async (timeframe: string = selectedTimeframe) => {
    try {
      console.log('开始获取价格图表数据...', timeframe);
      setIsLoadingPrice(true);
      const response = await api.get('/market/price-chart', {
        params: { symbol: 'BTC-USDT', timeframe: timeframe, limit: 24 }
      });
      
      console.log('价格图表数据响应:', response);
      
      if (response.data.success) {
        // 后端已经格式化了时间，直接使用
        const formattedData = response.data.data.map((candle: any) => ({
          time: candle.time,
          price: candle.price
        }));
        
        setPriceData(formattedData);
        console.log('价格图表数据设置成功:', formattedData);
      } else {
        console.error('价格图表API返回失败:', response.data.message);
      }
    } catch (error) {
      console.error('获取价格数据失败:', error);
    } finally {
      setIsLoadingPrice(false);
    }
  };

  // 获取实时价格数据
  const fetchTickerData = async () => {
    try {
      console.log('开始获取实时价格数据...');
      const response = await api.get('/market/ticker', {
        params: { symbol: 'BTC-USDT' }
      });
      
      console.log('价格数据响应:', response);
      
      if (response.data.success) {
        setTickerData(response.data.data);
        console.log('价格数据设置成功:', response.data.data);
      } else {
        console.error('API返回失败:', response.data.message);
      }
    } catch (error) {
      console.error('获取实时价格数据失败:', error);
    }
  };

  // 处理WebSocket实时数据更新
  useEffect(() => {
    if (lastMessage) {
      try {
        // 如果lastMessage是字符串，则解析JSON
        const message = typeof lastMessage === 'string' ? JSON.parse(lastMessage) : lastMessage;
        if (message.type === 'price_update' && message.symbol === 'BTC-USDT') {
          // 更新实时价格数据
          setTickerData(message.data);
          console.log('收到实时价格更新:', message.data);
        } else {
          // 处理其他WebSocket消息
          console.log('收到实时数据:', message);
          refetch();
        }
      } catch (error) {
        // 处理非JSON消息
        console.log('收到实时数据:', lastMessage);
        refetch();
      }
    }
  }, [lastMessage, refetch]);

  // 初始加载数据
  useEffect(() => {
    console.log('Dashboard组件加载，开始获取数据...');
    console.log('API baseURL:', process.env.REACT_APP_API_BASE_URL);
    fetchPriceData();
    fetchTickerData();
  }, [refreshKey]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    refetch();
    fetchPriceData();
    fetchTickerData();
  };

  // 处理时间框架切换
  const handleTimeframeChange = (timeframe: string) => {
    setSelectedTimeframe(timeframe);
    fetchPriceData(timeframe);
  };

  // 模拟数据
  const dashboardStats = {
    totalBalance: 125000,
    totalPnl: 8500,
    winRate: 68.5,
    activeStrategies: 3,
    totalTrades: 1247,
    riskLevel: 'medium',
    systemStatus: 'healthy' as const,
  };

  // 使用真实价格数据，如果没有则使用模拟数据
  const displayPriceData = priceData.length > 0 ? priceData : [
    { time: '09:00', price: 95000 },
    { time: '10:00', price: 95200 },
    { time: '11:00', price: 94800 },
    { time: '12:00', price: 95500 },
    { time: '13:00', price: 95800 },
    { time: '14:00', price: 96200 },
    { time: '15:00', price: 96000 },
  ];

  const performanceData = [
    { date: '2024-01-01', value: 100000 },
    { date: '2024-01-02', value: 101200 },
    { date: '2024-01-03', value: 99800 },
    { date: '2024-01-04', value: 102500 },
    { date: '2024-01-05', value: 104200 },
    { date: '2024-01-06', value: 103800 },
    { date: '2024-01-07', value: 105600 },
  ];

  const recentTrades: Trade[] = [
    {
      id: '1',
      tradeId: '1',
      strategyId: 'strategy-1',
      strategyVersion: '1.0.0',
      symbol: 'BTC-USDT',
      direction: 'BUY' as const,
      orderType: 'MARKET' as const,
      price: 95200,
      quantity: 0.1,
      amount: 9520,
      commission: 4.76,
      pnl: 150,
      status: 'FILLED' as const,
      timestamp: '2024-01-07 15:30:00',
      createdAt: '2024-01-07 15:30:00',
      updatedAt: '2024-01-07 15:30:00',
    },
    {
      id: '2',
      tradeId: '2',
      strategyId: 'strategy-1',
      strategyVersion: '1.0.0',
      symbol: 'BTC-USDT',
      direction: 'SELL' as const,
      orderType: 'MARKET' as const,
      price: 95800,
      quantity: 0.05,
      amount: 4790,
      commission: 2.395,
      pnl: -80,
      status: 'FILLED' as const,
      timestamp: '2024-01-07 14:15:00',
      createdAt: '2024-01-07 14:15:00',
      updatedAt: '2024-01-07 14:15:00',
    },
    {
      id: '3',
      tradeId: '3',
      strategyId: 'strategy-2',
      strategyVersion: '1.0.0',
      symbol: 'ETH-USDT',
      direction: 'BUY' as const,
      orderType: 'MARKET' as const,
      price: 3200,
      quantity: 2,
      amount: 6400,
      commission: 3.2,
      pnl: 200,
      status: 'FILLED' as const,
      timestamp: '2024-01-07 13:45:00',
      createdAt: '2024-01-07 13:45:00',
      updatedAt: '2024-01-07 13:45:00',
    },
  ];

  return (
    <Box>
      {/* 页面标题和操作 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            交易仪表板
          </Typography>
          <Typography variant="body2" color="text.secondary">
            实时监控您的交易策略和投资组合表现
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label="实时更新"
            color="success"
            size="small"
            sx={{ mr: 1 }}
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={isLoading}
          >
            刷新数据
          </Button>
        </Box>
      </Box>

      {/* 关键指标卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="总资产"
            value={dashboardStats.totalBalance}
            change={5.2}
            changeLabel="vs 昨日"
            icon={<AccountBalance />}
            color="primary"
            trend="up"
            subtitle="USDT"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="总盈亏"
            value={dashboardStats.totalPnl}
            change={12.8}
            changeLabel="vs 昨日"
            icon={<TrendingUp />}
            color="success"
            trend="up"
            subtitle="USDT"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="BTC价格"
            value={tickerData ? tickerData.last : 95000}
            change={tickerData ? tickerData.changePercent24h * 100 : 0}
            changeLabel="24h变化"
            icon={<TrendingUp />}
            color="info"
            trend={tickerData && tickerData.changePercent24h > 0 ? "up" : "down"}
            subtitle="USDT"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="胜率"
            value={`${dashboardStats.winRate}%`}
            progress={dashboardStats.winRate}
            icon={<Psychology />}
            color="info"
            subtitle="最近30天"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="活跃策略"
            value={dashboardStats.activeStrategies}
            icon={<Security />}
            color="warning"
            subtitle="运行中"
          />
        </Grid>
      </Grid>

      {/* 图表区域 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* 价格图表 */}
        <Grid item xs={12} lg={8}>
          <Card
            sx={{
              background: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  BTC-USDT 价格走势
                  {isLoadingPrice && (
                    <Chip 
                      label="加载中..." 
                      size="small" 
                      color="info" 
                      sx={{ ml: 2 }}
                    />
                  )}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip 
                    label="1H" 
                    size="small" 
                    color={selectedTimeframe === '1H' ? 'primary' : 'default'}
                    onClick={() => handleTimeframeChange('1H')}
                    sx={{ cursor: 'pointer' }}
                  />
                  <Chip 
                    label="4H" 
                    size="small" 
                    color={selectedTimeframe === '4H' ? 'primary' : 'default'}
                    onClick={() => handleTimeframeChange('4H')}
                    sx={{ cursor: 'pointer' }}
                  />
                  <Chip 
                    label="1D" 
                    size="small" 
                    color={selectedTimeframe === '1D' ? 'primary' : 'default'}
                    onClick={() => handleTimeframeChange('1D')}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
              </Box>
              <PriceChart data={displayPriceData} />
            </CardContent>
          </Card>
        </Grid>

        {/* 右侧状态面板 */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            {/* API连接状态 */}
            <Grid item xs={12}>
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
                    API连接
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          API连接
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          100%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={100}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: 'success.main',
                            borderRadius: 3,
                          },
                        }}
                      />
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          数据库
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          95%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={95}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: 'success.main',
                            borderRadius: 3,
                          },
                        }}
                      />
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          交易引擎
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          100%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={100}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: 'success.main',
                            borderRadius: 3,
                          },
                        }}
                      />
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          风险监控
                        </Typography>
                        <Typography variant="body2" color="warning.main">
                          85%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={85}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: 'warning.main',
                            borderRadius: 3,
                          },
                        }}
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* 最近事件 */}
            <Grid item xs={12}>
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
                    最近事件
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.primary">
                        策略执行成功
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        15:30
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.primary">
                        风险预警触发
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        15:25
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.primary">
                        数据同步完成
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        15:20
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.primary">
                        系统启动完成
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        15:15
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* 性能图表和交易记录 */}
      <Grid container spacing={3}>
        {/* 权益曲线 */}
        <Grid item xs={12} lg={6}>
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
                权益曲线
              </Typography>
              <PerformanceChart data={performanceData} />
            </CardContent>
          </Card>
        </Grid>

        {/* 最近交易 */}
        <Grid item xs={12} lg={6}>
          <RecentTrades trades={recentTrades} />
        </Grid>
      </Grid>

      {/* 风险指标 */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
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
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      最大回撤
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      3.2%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={32}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'warning.main',
                          borderRadius: 3,
                        },
                      }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      夏普比率
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      1.85
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={74}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'success.main',
                          borderRadius: 3,
                        },
                      }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      波动率
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      12.5%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={50}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'info.main',
                          borderRadius: 3,
                        },
                      }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      风险等级
                    </Typography>
                    <Chip
                      label="中等"
                      color="warning"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
