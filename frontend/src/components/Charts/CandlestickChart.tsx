import React from 'react';
import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Bar,
  Line,
  Cell,
} from 'recharts';

interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
}

interface CandlestickChartProps {
  data: CandlestickData[];
  height?: number;
  showVolume?: boolean;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({ 
  data, 
  height = 400,
  showVolume = true
}) => {
  const formatPrice = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  const formatTime = (time: string) => {
    return time;
  };

  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toFixed(0);
  };

  // 计算价格范围
  const prices = data.flatMap(d => [d.open, d.high, d.low, d.close]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1;

  // 计算成交量范围
  const volumes = data.map(d => d.volume);
  const maxVolume = Math.max(...volumes);

  // 使用单一ComposedChart组件，以价格K线为主
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="time" 
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatTime}
        />
        <YAxis 
          yAxisId="price"
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatPrice}
          domain={[minPrice - padding, maxPrice + padding]}
          orientation="left"
        />
        {showVolume && (
          <YAxis 
            yAxisId="volume"
            stroke="#B0B0B0"
            fontSize={10}
            tickFormatter={formatVolume}
            domain={[0, maxVolume * 1.1]}
            orientation="right"
          />
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#FFFFFF',
          }}
          formatter={(value: number, name: string) => {
            if (name === 'volume') {
              return [formatVolume(value), '成交量'];
            }
            return [formatPrice(value), name];
          }}
          labelFormatter={(time: string) => `时间: ${time}`}
        />
        {/* 价格线图 - 主要显示 */}
        <Line
          yAxisId="price"
          type="monotone"
          dataKey="close"
          stroke="#00D4AA"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: '#00D4AA', strokeWidth: 2 }}
        />
        {/* 成交量柱状图 - 辅助显示 */}
        {showVolume && (
          <Bar
            yAxisId="volume"
            dataKey="volume"
            fill="#00D4AA"
            fillOpacity={0.3}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default CandlestickChart;