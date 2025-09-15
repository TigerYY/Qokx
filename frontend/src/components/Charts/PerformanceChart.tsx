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
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';

interface PerformanceChartProps {
  data: Array<{
    date: string;
    value: number;
  }>;
  height?: number;
  showReferenceLine?: boolean;
  referenceValue?: number;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ 
  data, 
  height = 300,
  showReferenceLine = true,
  referenceValue = 100000
}) => {
  const formatValue = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toLocaleString()}`;
  };

  const formatDate = (date: string) => {
    return format(new Date(date), 'MM/dd');
  };

  // 计算收益率
  const calculateReturn = (current: number, initial: number) => {
    return ((current - initial) / initial) * 100;
  };

  const initialValue = data[0]?.value || referenceValue;
  const currentValue = data[data.length - 1]?.value || referenceValue;
  const totalReturn = calculateReturn(currentValue, initialValue);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="performanceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={totalReturn >= 0 ? "#00D4AA" : "#FF6B6B"} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={totalReturn >= 0 ? "#00D4AA" : "#FF6B6B"} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="date" 
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatDate}
        />
        <YAxis 
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatValue}
          domain={['dataMin - 1000', 'dataMax + 1000']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#FFFFFF',
          }}
          formatter={(value: number, name: string) => [
            formatValue(value), 
            '权益'
          ]}
          labelFormatter={(date: string) => `日期: ${formatDate(date)}`}
        />
        {showReferenceLine && (
          <ReferenceLine 
            y={referenceValue} 
            stroke="#B0B0B0" 
            strokeDasharray="5 5"
            strokeOpacity={0.5}
          />
        )}
        <Area
          type="monotone"
          dataKey="value"
          stroke={totalReturn >= 0 ? "#00D4AA" : "#FF6B6B"}
          strokeWidth={2}
          fill="url(#performanceGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default PerformanceChart;
