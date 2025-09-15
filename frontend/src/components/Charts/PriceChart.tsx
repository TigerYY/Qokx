import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface PriceChartProps {
  data: Array<{
    time: string;
    price: number;
  }>;
  type?: 'line' | 'area';
  height?: number;
}

const PriceChart: React.FC<PriceChartProps> = ({ 
  data, 
  type = 'area',
  height = 300 
}) => {
  const formatPrice = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  const formatTime = (time: string) => {
    return time;
  };

  if (type === 'area') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#00D4AA" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis 
            dataKey="time" 
            stroke="#B0B0B0"
            fontSize={12}
            tickFormatter={formatTime}
          />
          <YAxis 
            stroke="#B0B0B0"
            fontSize={12}
            tickFormatter={formatPrice}
            domain={['dataMin - 100', 'dataMax + 100']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              color: '#FFFFFF',
            }}
            formatter={(value: number) => [formatPrice(value), '价格']}
            labelFormatter={(time: string) => `时间: ${time}`}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#00D4AA"
            strokeWidth={2}
            fill="url(#priceGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="time" 
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatTime}
        />
        <YAxis 
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatPrice}
          domain={['dataMin - 100', 'dataMax + 100']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#FFFFFF',
          }}
          formatter={(value: number) => [formatPrice(value), '价格']}
          labelFormatter={(time: string) => `时间: ${time}`}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#00D4AA"
          strokeWidth={2}
          dot={{ fill: '#00D4AA', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#00D4AA', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PriceChart;
