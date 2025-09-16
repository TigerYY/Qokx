import React from 'react';
import {
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Bar,
  BarChart,
  Line,
  LineChart,
  Area,
  AreaChart,
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

  // 自定义K线渲染
  const CustomCandlestick = (props: any) => {
    const { payload, x, y, width, height } = props;
    if (!payload) return null;

    const { open, high, low, close } = payload;
    const isGreen = close >= open;
    const color = isGreen ? '#00D4AA' : '#FF6B6B';
    
    // 计算K线位置
    const bodyHeight = Math.abs(close - open) * (height / (maxPrice - minPrice + padding * 2));
    const bodyY = y + (maxPrice - Math.max(open, close)) * (height / (maxPrice - minPrice + padding * 2));
    const wickTop = y + (maxPrice - high) * (height / (maxPrice - minPrice + padding * 2));
    const wickBottom = y + (maxPrice - low) * (height / (maxPrice - minPrice + padding * 2));
    const centerX = x + width / 2;

    return (
      <g>
        {/* 上影线 */}
        <line
          x1={centerX}
          y1={wickTop}
          x2={centerX}
          y2={Math.min(bodyY, bodyY + bodyHeight)}
          stroke={color}
          strokeWidth={1}
        />
        {/* 下影线 */}
        <line
          x1={centerX}
          y1={Math.max(bodyY, bodyY + bodyHeight)}
          x2={centerX}
          y2={wickBottom}
          stroke={color}
          strokeWidth={1}
        />
        {/* K线实体 */}
        <rect
          x={x + width * 0.1}
          y={bodyY}
          width={width * 0.8}
          height={Math.max(bodyHeight, 1)}
          fill={isGreen ? color : 'transparent'}
          stroke={color}
          strokeWidth={1}
        />
        {/* 空心K线（下跌时） */}
        {!isGreen && (
          <rect
            x={x + width * 0.1}
            y={bodyY}
            width={width * 0.8}
            height={Math.max(bodyHeight, 1)}
            fill="transparent"
            stroke={color}
            strokeWidth={1}
          />
        )}
      </g>
    );
  };

  if (showVolume) {
    return (
      <div style={{ width: '100%', height: height }}>
        {/* 价格K线图 */}
        <div style={{ height: height * 0.7 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
                domain={[minPrice - padding, maxPrice + padding]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(26, 26, 26, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#FFFFFF',
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'close') {
                    return [formatPrice(value), '收盘价'];
                  }
                  return [formatPrice(value), name];
                }}
                labelFormatter={(time: string) => `时间: ${time}`}
              />
              {/* 使用自定义K线渲染 */}
              <Bar
                dataKey="close"
                shape={<CustomCandlestick />}
                fill="transparent"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        
        {/* 成交量图 */}
        <div style={{ height: height * 0.3 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis 
                dataKey="time" 
                stroke="#B0B0B0"
                fontSize={10}
                tickFormatter={formatTime}
              />
              <YAxis 
                stroke="#B0B0B0"
                fontSize={10}
                tickFormatter={formatVolume}
                domain={[0, maxVolume * 1.1]}
              />
              <Bar
                dataKey="volume"
                fill="#00D4AA"
                fillOpacity={0.6}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // 仅显示K线图（不含成交量）
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
          stroke="#B0B0B0"
          fontSize={12}
          tickFormatter={formatPrice}
          domain={[minPrice - padding, maxPrice + padding]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(26, 26, 26, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#FFFFFF',
          }}
          formatter={(value: number, name: string) => [formatPrice(value), name]}
          labelFormatter={(time: string) => `时间: ${time}`}
        />
        <Bar
          dataKey="close"
          shape={<CustomCandlestick />}
          fill="transparent"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default CandlestickChart;