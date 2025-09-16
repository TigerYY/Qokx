import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Chip,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  PlayArrow,
  Stop,
  Refresh,
} from '@mui/icons-material';

import PriceChart from '@/components/Charts/PriceChart';
import RecentTrades from '@/components/Trading/RecentTrades';
import { Trade } from '@/types';
import { api } from '@/services/api';

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
      id={`trading-tabpanel-${index}`}
      aria-labelledby={`trading-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TradingInterface: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [isTrading, setIsTrading] = useState(false);
  const [orderType, setOrderType] = useState('market');
  const [direction, setDirection] = useState('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  
  // 实时数据状态
  const [priceData, setPriceData] = useState<Array<{ time: string; price: number }>>([]);
  const [tickerData, setTickerData] = useState<any>(null);
  const [isLoadingPrice, setIsLoadingPrice] = useState(false);

  // 获取价格图表数据
  const fetchPriceData = async () => {
    try {
      setIsLoadingPrice(true);
      console.log('Trading页面：开始获取价格数据...');
      const response = await api.get('/market/price-chart', {
        params: { 
          symbol: 'BTC-USDT', 
          timeframe: '1H', 
          limit: 24 
        }
      });
      
      console.log('Trading页面：价格数据响应:', response);
      
      if (response.data.success) {
        const formattedData = response.data.data.map((candle: any) => ({
          time: new Date(candle.time).toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          price: candle.price
        }));
        setPriceData(formattedData);
        console.log('Trading页面：价格数据设置成功:', formattedData);
      } else {
        console.error('Trading页面：API返回失败:', response.data.message);
        // 使用模拟数据作为后备
        setPriceData([
          { time: '09:00', price: 95000 },
          { time: '10:00', price: 95200 },
          { time: '11:00', price: 94800 },
          { time: '12:00', price: 95500 },
          { time: '13:00', price: 95800 },
          { time: '14:00', price: 96200 },
          { time: '15:00', price: 96000 },
        ]);
      }
    } catch (error) {
      console.error('Trading页面：获取价格数据失败:', error);
      // 使用模拟数据作为后备
      setPriceData([
        { time: '09:00', price: 95000 },
        { time: '10:00', price: 95200 },
        { time: '11:00', price: 94800 },
        { time: '12:00', price: 95500 },
        { time: '13:00', price: 95800 },
        { time: '14:00', price: 96200 },
        { time: '15:00', price: 96000 },
      ]);
    } finally {
      setIsLoadingPrice(false);
    }
  };

  // 获取实时价格数据
  const fetchTickerData = async () => {
    try {
      console.log('Trading页面：开始获取实时价格数据...');
      const response = await api.get('/market/ticker', {
        params: { symbol: 'BTC-USDT' }
      });
      
      console.log('Trading页面：价格数据响应:', response);
      
      if (response.data.success) {
        setTickerData(response.data.data);
        console.log('Trading页面：价格数据设置成功:', response.data.data);
      } else {
        console.error('Trading页面：API返回失败:', response.data.message);
      }
    } catch (error) {
      console.error('Trading页面：获取实时价格数据失败:', error);
    }
  };

  // 初始加载数据
  useEffect(() => {
    console.log('Trading页面：组件加载，开始获取数据...');
    console.log('API baseURL:', process.env.REACT_APP_API_BASE_URL);
    fetchPriceData();
    fetchTickerData();
  }, []);

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
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleStartTrading = () => {
    setIsTrading(true);
  };

  const handleStopTrading = () => {
    setIsTrading(false);
  };

  const handlePlaceOrder = () => {
    console.log('下单:', { orderType, direction, quantity, price });
  };

  const handleRefresh = () => {
    console.log('Trading页面：手动刷新数据...');
    fetchPriceData();
    fetchTickerData();
  };

  return (
    <Box>
      {/* 页面标题和操作 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            交易界面
          </Typography>
          <Typography variant="body2" color="text.secondary">
            实时交易和订单管理
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={isTrading ? '交易中' : '已停止'}
            color={isTrading ? 'success' : 'default'}
            sx={{ mr: 1 }}
          />
          {isTrading ? (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Stop />}
              onClick={handleStopTrading}
            >
              停止交易
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={handleStartTrading}
            >
              开始交易
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={isLoadingPrice}
          >
            刷新
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
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
                  BTC-USDT 实时价格
                  {tickerData && (
                    <Box component="span" sx={{ ml: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>
                        ${tickerData.last?.toLocaleString() || 'N/A'}
                      </Typography>
                      {tickerData.changePercent24h && (
                        <Chip 
                          label={`${(tickerData.changePercent24h * 100).toFixed(2)}%`}
                          size="small"
                          color={tickerData.changePercent24h >= 0 ? 'success' : 'error'}
                          icon={tickerData.changePercent24h >= 0 ? <TrendingUp /> : <TrendingDown />}
                        />
                      )}
                    </Box>
                  )}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label="1H" size="small" color="primary" />
                  <Chip label="4H" size="small" />
                  <Chip label="1D" size="small" />
                  {isLoadingPrice && <Chip label="加载中..." size="small" color="info" />}
                </Box>
              </Box>
              <PriceChart data={priceData} type="area" height={400} />
            </CardContent>
          </Card>
        </Grid>

        {/* 交易面板 */}
        <Grid item xs={12} lg={4}>
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
                快速交易
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>订单类型</InputLabel>
                  <Select
                    value={orderType}
                    label="订单类型"
                    onChange={(e) => setOrderType(e.target.value)}
                  >
                    <MenuItem value="market">市价单</MenuItem>
                    <MenuItem value="limit">限价单</MenuItem>
                    <MenuItem value="stop">止损单</MenuItem>
                  </Select>
                </FormControl>

                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Button
                    fullWidth
                    variant={direction === 'buy' ? 'contained' : 'outlined'}
                    color="success"
                    startIcon={<TrendingUp />}
                    onClick={() => setDirection('buy')}
                  >
                    买入
                  </Button>
                  <Button
                    fullWidth
                    variant={direction === 'sell' ? 'contained' : 'outlined'}
                    color="error"
                    startIcon={<TrendingDown />}
                    onClick={() => setDirection('sell')}
                  >
                    卖出
                  </Button>
                </Box>

                <TextField
                  fullWidth
                  label="数量"
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  sx={{ mb: 2 }}
                />

                {orderType !== 'market' && (
                  <TextField
                    fullWidth
                    label="价格"
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                )}

                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={handlePlaceOrder}
                  disabled={!quantity || (orderType !== 'market' && !price)}
                >
                  {direction === 'buy' ? '买入' : '卖出'} BTC
                </Button>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  账户信息
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    可用余额
                  </Typography>
                  <Typography variant="body2">
                    125,000 USDT
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    冻结余额
                  </Typography>
                  <Typography variant="body2">
                    2,500 USDT
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    总资产
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    127,500 USDT
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 交易记录和订单 */}
        <Grid item xs={12}>
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
                <Tab label="最近交易" />
                <Tab label="活跃订单" />
                <Tab label="历史订单" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <RecentTrades trades={recentTrades} />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  暂无活跃订单
                </Typography>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  暂无历史订单
                </Typography>
              </Box>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TradingInterface;
