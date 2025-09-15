"""
历史数据加载器 - 用于回测验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import os
import json
import aiohttp
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoricalDataLoader:
    """历史数据加载器"""
    
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def load_data(self, symbol: str, timeframes: List[str], 
                      start_date: datetime, end_date: datetime,
                      source: str = "local") -> Dict[str, pd.DataFrame]:
        """加载历史数据"""
        data = {}
        
        for timeframe in timeframes:
            try:
                if source == "local":
                    df = await self._load_from_local(symbol, timeframe, start_date, end_date)
                elif source == "api":
                    df = await self._load_from_api(symbol, timeframe, start_date, end_date)
                else:
                    raise ValueError(f"未知数据源: {source}")
                
                if df is not None and not df.empty:
                    data[timeframe] = df
                    logger.info(f"加载 {symbol} {timeframe} 数据: {len(df)} 条记录")
                else:
                    logger.warning(f"未找到 {symbol} {timeframe} 数据")
                    
            except Exception as e:
                logger.error(f"加载 {symbol} {timeframe} 数据失败: {e}")
                continue
        
        return data
    
    async def _load_from_local(self, symbol: str, timeframe: str, 
                             start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """从本地文件加载数据"""
        filename = self.data_dir / f"{symbol}_{timeframe}.csv"
        
        if not filename.exists():
            logger.warning(f"本地数据文件不存在: {filename}")
            return None
        
        try:
            df = pd.read_csv(filename)
            
            # 确保时间戳列存在
            if 'timestamp' not in df.columns:
                logger.error(f"数据文件缺少timestamp列: {filename}")
                return None
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"数据文件缺少 {col} 列: {filename}")
                    return None
            
            # 过滤时间范围
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            # 确保数据按时间排序
            df.sort_index(inplace=True)
            
            # 添加volume列如果不存在
            if 'volume' not in df.columns:
                df['volume'] = 0.0
            
            return df
            
        except Exception as e:
            logger.error(f"读取本地数据文件失败 {filename}: {e}")
            return None
    
    async def _load_from_api(self, symbol: str, timeframe: str, 
                           start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """从API加载数据"""
        try:
            # 这里可以集成各种数据API，如Binance、OKX等
            # 目前先返回None，需要根据实际API实现
            logger.warning("API数据加载功能尚未实现")
            return None
            
        except Exception as e:
            logger.error(f"从API加载数据失败: {e}")
            return None
    
    async def download_data(self, symbol: str, timeframes: List[str], 
                          start_date: datetime, end_date: datetime):
        """下载历史数据"""
        logger.info(f"开始下载 {symbol} 历史数据: {start_date} - {end_date}")
        
        for timeframe in timeframes:
            try:
                df = await self._download_timeframe_data(symbol, timeframe, start_date, end_date)
                if df is not None and not df.empty:
                    await self._save_data(symbol, timeframe, df)
                    logger.info(f"下载完成 {symbol} {timeframe}: {len(df)} 条记录")
                
            except Exception as e:
                logger.error(f"下载 {symbol} {timeframe} 数据失败: {e}")
                continue
    
    async def _download_timeframe_data(self, symbol: str, timeframe: str, 
                                     start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """下载特定时间框架数据"""
        # 这里可以实现具体的数据下载逻辑
        # 目前先返回空DataFrame，需要根据实际数据源实现
        logger.warning("数据下载功能尚未实现")
        return pd.DataFrame()
    
    async def _save_data(self, symbol: str, timeframe: str, df: pd.DataFrame):
        """保存数据到文件"""
        filename = self.data_dir / f"{symbol}_{timeframe}.csv"
        
        # 重置索引以便保存时间戳
        df_to_save = df.reset_index()
        df_to_save.to_csv(filename, index=False)
        logger.info(f"数据已保存: {filename}")
    
    def generate_sample_data(self, symbol: str, timeframes: List[str], 
                           start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """生成示例数据用于测试"""
        logger.info(f"生成示例数据: {symbol} {timeframes}")
        
        data = {}
        
        for timeframe in timeframes:
            df = self._generate_timeframe_sample_data(timeframe, start_date, end_date)
            if df is not None:
                data[timeframe] = df
                
                # 保存示例数据
                filename = self.data_dir / f"{symbol}_{timeframe}_sample.csv"
                df_to_save = df.reset_index()
                df_to_save.to_csv(filename, index=False)
                logger.info(f"示例数据已保存: {filename}")
        
        return data
    
    def _generate_timeframe_sample_data(self, timeframe: str, 
                                      start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """生成特定时间框架的示例数据"""
        # 根据时间框架确定时间间隔
        timeframe_intervals = {
            '1m': timedelta(minutes=1),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1),
        }
        
        if timeframe not in timeframe_intervals:
            logger.error(f"不支持的时间框架: {timeframe}")
            return pd.DataFrame()
        
        interval = timeframe_intervals[timeframe]
        
        # 生成时间序列
        current_time = start_date
        timestamps = []
        
        while current_time <= end_date:
            timestamps.append(current_time)
            current_time += interval
        
        # 生成随机价格数据
        np.random.seed(42)  # 固定随机种子以便结果可重现
        n_periods = len(timestamps)
        
        # 初始价格
        initial_price = 50000.0
        
        # 生成随机游走价格
        returns = np.random.normal(0.0001, 0.02, n_periods)
        prices = initial_price * np.exp(np.cumsum(returns))
        
        # 生成OHLCV数据
        data = []
        
        for i, timestamp in enumerate(timestamps):
            price = prices[i]
            
            # 生成合理的OHLC值
            open_price = price * (1 + np.random.normal(0, 0.001))
            high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.005)))
            close_price = price
            volume = np.random.lognormal(10, 2)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """验证数据质量"""
        if not data:
            logger.error("数据为空")
            return False
        
        for timeframe, df in data.items():
            if df.empty:
                logger.error(f"{timeframe} 数据为空")
                return False
            
            # 检查缺失值
            if df.isnull().any().any():
                logger.warning(f"{timeframe} 数据包含缺失值")
                
            # 检查时间间隔一致性
            time_diff = df.index.to_series().diff().dropna()
            if len(time_diff.unique()) > 1:
                logger.warning(f"{timeframe} 时间间隔不一致")
            
            # 检查价格合理性
            if (df['close'] <= 0).any():
                logger.error(f"{timeframe} 包含非正价格")
                return False
        
        return True
    
    def get_data_info(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """获取数据统计信息"""
        info = {}
        
        for timeframe, df in data.items():
            timeframe_info = {
                'start_date': df.index.min(),
                'end_date': df.index.max(),
                'num_records': len(df),
                'price_range': (df['close'].min(), df['close'].max()),
                'avg_volume': df['volume'].mean(),
                'data_quality': 'good'
            }
            
            # 检查数据质量
            if df.isnull().any().any():
                timeframe_info['data_quality'] = 'has_nulls'
            
            info[timeframe] = timeframe_info
        
        return info


# 工具函数
def convert_csv_to_dataframe(csv_file: str) -> pd.DataFrame:
    """转换CSV文件为DataFrame"""
    try:
        df = pd.read_csv(csv_file)
        
        # 自动检测时间戳列
        timestamp_cols = ['timestamp', 'time', 'date', 'datetime']
        timestamp_col = None
        
        for col in timestamp_cols:
            if col in df.columns:
                timestamp_col = col
                break
        
        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df.set_index(timestamp_col, inplace=True)
        else:
            logger.warning("未找到时间戳列，使用默认索引")
        
        # 确保OHLC列存在
        ohlc_mapping = {
            'open': ['open', 'o'],
            'high': ['high', 'h'],
            'low': ['low', 'l'],
            'close': ['close', 'c']
        }
        
        for standard_col, possible_cols in ohlc_mapping.items():
            if standard_col not in df.columns:
                for col in possible_cols:
                    if col in df.columns:
                        df[standard_col] = df[col]
                        break
        
        return df
        
    except Exception as e:
        logger.error(f"转换CSV文件失败 {csv_file}: {e}")
        return pd.DataFrame()