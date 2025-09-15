import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Visibility,
} from '@mui/icons-material';

interface Trade {
  id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  pnl: number;
  timestamp: string;
}

interface RecentTradesProps {
  trades: Trade[];
  maxRows?: number;
}

const RecentTrades: React.FC<RecentTradesProps> = ({ 
  trades, 
  maxRows = 5 
}) => {
  const formatPrice = (price: number) => {
    return `$${price.toLocaleString()}`;
  };

  const formatQuantity = (quantity: number) => {
    return quantity.toFixed(4);
  };

  const formatPnl = (pnl: number) => {
    const formatted = pnl >= 0 ? `+$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
    return formatted;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDirectionIcon = (direction: 'BUY' | 'SELL') => {
    return direction === 'BUY' ? (
      <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
    ) : (
      <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
    );
  };

  const getDirectionColor = (direction: 'BUY' | 'SELL') => {
    return direction === 'BUY' ? 'success' : 'error';
  };

  const getPnlColor = (pnl: number) => {
    return pnl >= 0 ? 'success.main' : 'error.main';
  };

  const displayedTrades = trades.slice(0, maxRows);

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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            最近交易
          </Typography>
          <Tooltip title="查看所有交易">
            <IconButton size="small" color="primary">
              <Visibility fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {displayedTrades.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">
              暂无交易记录
            </Typography>
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    方向
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    交易对
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    价格
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    数量
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    盈亏
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 600, py: 1 }}>
                    时间
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {displayedTrades.map((trade) => (
                  <TableRow
                    key={trade.id}
                    sx={{
                      '&:hover': {
                        backgroundColor: 'rgba(0, 212, 170, 0.05)',
                      },
                    }}
                  >
                    <TableCell sx={{ py: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getDirectionIcon(trade.direction)}
                        <Chip
                          label={trade.direction}
                          size="small"
                          color={getDirectionColor(trade.direction)}
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell sx={{ color: 'text.primary', py: 1 }}>
                      {trade.symbol}
                    </TableCell>
                    <TableCell sx={{ color: 'text.primary', py: 1 }}>
                      {formatPrice(trade.price)}
                    </TableCell>
                    <TableCell sx={{ color: 'text.primary', py: 1 }}>
                      {formatQuantity(trade.quantity)}
                    </TableCell>
                    <TableCell 
                      sx={{ 
                        color: getPnlColor(trade.pnl), 
                        fontWeight: 600,
                        py: 1 
                      }}
                    >
                      {formatPnl(trade.pnl)}
                    </TableCell>
                    <TableCell sx={{ color: 'text.secondary', py: 1 }}>
                      {formatTime(trade.timestamp)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {trades.length > maxRows && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              还有 {trades.length - maxRows} 条交易记录
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentTrades;
