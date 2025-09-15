// 基础类型定义
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// 交易相关类型
export interface Trade extends BaseEntity {
  tradeId: string;
  strategyId: string;
  strategyVersion: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  orderType: 'MARKET' | 'LIMIT' | 'STOP';
  price: number;
  quantity: number;
  amount: number;
  commission: number;
  pnl: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  timestamp: string;
}

// 策略相关类型
export interface Strategy extends BaseEntity {
  strategyId: string;
  name: string;
  version: string;
  description: string;
  classPath: string;
  config: Record<string, any>;
  isActive: boolean;
  isTesting: boolean;
  status: 'DRAFT' | 'TESTING' | 'ACTIVE' | 'INACTIVE' | 'DEPRECATED';
}

export interface StrategyConfig {
  strategyId: string;
  configKey: string;
  configValue: any;
  configType: 'strategy' | 'risk' | 'system';
  description?: string;
  isActive: boolean;
}

// 性能指标类型
export interface PerformanceMetrics extends BaseEntity {
  strategyId: string;
  strategyVersion: string;
  date: string;
  totalReturn: number;
  dailyReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  avgWin: number;
  avgLoss: number;
}

// 市场数据类型
export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

export interface KlineData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// 风险相关类型
export interface RiskEvent extends BaseEntity {
  eventId: string;
  strategyId: string;
  eventType: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  data: Record<string, any>;
  isResolved: boolean;
  resolvedAt?: string;
}

export interface RiskMetrics {
  currentRiskLevel: string;
  maxDrawdown: number;
  volatility: number;
  var95: number;
  var99: number;
  sharpeRatio: number;
  sortinoRatio: number;
}

// A/B测试类型
export interface ABTest extends BaseEntity {
  testId: string;
  testName: string;
  strategyAId: string;
  strategyAVersion: string;
  strategyBId: string;
  strategyBVersion: string;
  trafficSplit: number;
  startDate: string;
  endDate?: string;
  status: 'RUNNING' | 'COMPLETED' | 'CANCELLED';
  results?: ABTestResults;
}

export interface ABTestResults {
  strategyAPerformance: Record<string, number>;
  strategyBPerformance: Record<string, number>;
  winner: 'A' | 'B' | 'TIE';
  confidenceLevel: number;
  statisticalSignificance: boolean;
  testDurationDays: number;
  totalTradesA: number;
  totalTradesB: number;
}

// 交易会话类型
export interface TradingSession extends BaseEntity {
  sessionId: string;
  strategyId: string;
  strategyVersion: string;
  status: 'RUNNING' | 'STOPPED' | 'ERROR';
  startTime: string;
  endTime?: string;
  initialCapital: number;
  finalCapital?: number;
  totalPnl: number;
  totalTrades: number;
}

// 系统配置类型
export interface SystemConfig extends BaseEntity {
  configKey: string;
  configValue: any;
  configType: 'system' | 'risk' | 'monitoring';
  description?: string;
  isActive: boolean;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'TRADE' | 'SIGNAL' | 'RISK' | 'PERFORMANCE' | 'SYSTEM';
  data: any;
  timestamp: string;
}

// 图表数据类型
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
  }[];
}

// 仪表板统计类型
export interface DashboardStats {
  totalBalance: number;
  totalPnl: number;
  winRate: number;
  activeStrategies: number;
  totalTrades: number;
  riskLevel: string;
  systemStatus: 'HEALTHY' | 'WARNING' | 'ERROR' | 'OFFLINE';
}

// 用户界面状态类型
export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: 'zh' | 'en';
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'SUCCESS' | 'WARNING' | 'ERROR' | 'INFO';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// 表单类型
export interface StrategyFormData {
  name: string;
  description: string;
  version: string;
  config: Record<string, any>;
}

export interface TradeFormData {
  symbol: string;
  direction: 'BUY' | 'SELL';
  orderType: 'MARKET' | 'LIMIT' | 'STOP';
  quantity: number;
  price?: number;
  stopPrice?: number;
}

// 筛选和排序类型
export interface FilterOptions {
  strategyId?: string;
  symbol?: string;
  status?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

// 分页类型
export interface PaginationOptions {
  page: number;
  limit: number;
  sort?: SortOptions;
  filter?: FilterOptions;
}
