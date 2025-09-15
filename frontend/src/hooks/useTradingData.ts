import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

// 交易数据相关类型
interface TradingData {
  dashboardStats: {
    totalBalance: number;
    totalPnl: number;
    winRate: number;
    activeStrategies: number;
    totalTrades: number;
    riskLevel: string;
    systemStatus: string;
  };
  recentTrades: any[];
  performanceData: any[];
  priceData: any[];
}

// 获取交易数据
export const useTradingData = () => {
  return useQuery({
    queryKey: ['tradingData'],
    queryFn: async (): Promise<TradingData> => {
      const response = await api.get('/trading/dashboard');
      return response.data;
    },
    refetchInterval: 30000, // 30秒自动刷新
    staleTime: 10000, // 10秒内认为数据是新鲜的
  });
};

// 获取交易记录
export const useTrades = (params?: {
  page?: number;
  limit?: number;
  strategyId?: string;
  symbol?: string;
  startDate?: string;
  endDate?: string;
}) => {
  return useQuery({
    queryKey: ['trades', params],
    queryFn: async () => {
      const response = await api.get('/trading/trades', { params });
      return response.data;
    },
    placeholderData: (previousData) => previousData,
  });
};

// 获取策略列表
export const useStrategies = () => {
  return useQuery({
    queryKey: ['strategies'],
    queryFn: async () => {
      const response = await api.get('/strategies');
      return response.data;
    },
  });
};

// 获取策略详情
export const useStrategy = (strategyId: string) => {
  return useQuery({
    queryKey: ['strategy', strategyId],
    queryFn: async () => {
      const response = await api.get(`/strategies/${strategyId}`);
      return response.data;
    },
    enabled: !!strategyId,
  });
};

// 获取性能指标
export const usePerformanceMetrics = (strategyId?: string, days?: number) => {
  return useQuery({
    queryKey: ['performance', strategyId, days],
    queryFn: async () => {
      const response = await api.get('/trading/performance', {
        params: { strategyId, days },
      });
      return response.data;
    },
  });
};

// 获取市场数据
export const useMarketData = (symbol: string, timeframe: string = '1h') => {
  return useQuery({
    queryKey: ['marketData', symbol, timeframe],
    queryFn: async () => {
      const response = await api.get('/market/data', {
        params: { symbol, timeframe },
      });
      return response.data;
    },
    refetchInterval: 5000, // 5秒自动刷新
  });
};

// 启动策略
export const useStartStrategy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { strategyId: string; version?: string; config?: any }) => {
      const response = await api.post('/strategies/start', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
      queryClient.invalidateQueries({ queryKey: ['tradingData'] });
    },
  });
};

// 停止策略
export const useStopStrategy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (strategyId: string) => {
      const response = await api.post(`/strategies/${strategyId}/stop`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
      queryClient.invalidateQueries({ queryKey: ['tradingData'] });
    },
  });
};

// 更新策略配置
export const useUpdateStrategyConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: {
      strategyId: string;
      configKey: string;
      configValue: any;
    }) => {
      const response = await api.put('/strategies/config', data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['strategy', variables.strategyId] });
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
  });
};

// 创建A/B测试
export const useCreateABTest = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: {
      testName: string;
      strategyAId: string;
      strategyAVersion: string;
      strategyBId: string;
      strategyBVersion: string;
      trafficSplit: number;
      durationDays: number;
    }) => {
      const response = await api.post('/ab-tests', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ab-tests'] });
    },
  });
};

// 获取A/B测试列表
export const useABTests = () => {
  return useQuery({
    queryKey: ['ab-tests'],
    queryFn: async () => {
      const response = await api.get('/ab-tests');
      return response.data;
    },
  });
};

// 获取风险事件
export const useRiskEvents = (params?: {
  page?: number;
  limit?: number;
  severity?: string;
  strategyId?: string;
}) => {
  return useQuery({
    queryKey: ['riskEvents', params],
    queryFn: async () => {
      const response = await api.get('/risk/events', { params });
      return response.data;
    },
  });
};

// 获取系统配置
export const useSystemConfig = () => {
  return useQuery({
    queryKey: ['systemConfig'],
    queryFn: async () => {
      const response = await api.get('/system/config');
      return response.data;
    },
  });
};

// 更新系统配置
export const useUpdateSystemConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: {
      configKey: string;
      configValue: any;
    }) => {
      const response = await api.put('/system/config', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemConfig'] });
    },
  });
};
