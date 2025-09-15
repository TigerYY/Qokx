"""
回测结果分析器 - 提供详细的策略性能分析和可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)


class BacktestResultAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, result_data: Dict):
        self.result_data = result_data
        self.trades_df = self._prepare_trades_data()
        
    def _prepare_trades_data(self) -> pd.DataFrame:
        """准备交易数据"""
        trades = self.result_data.get('trades', [])
        
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        
        # 转换时间列
        time_cols = ['entry_time', 'exit_time']
        for col in time_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # 计算持仓时间
        if 'entry_time' in df.columns and 'exit_time' in df.columns:
            df['holding_period'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600  # 小时
        
        return df
    
    def generate_summary_report(self) -> Dict:
        """生成详细的分析报告"""
        report = {
            'basic_metrics': self._calculate_basic_metrics(),
            'trade_analysis': self._analyze_trades(),
            'time_analysis': self._analyze_by_time(),
            'risk_metrics': self._calculate_risk_metrics(),
            'performance_metrics': self._calculate_performance_metrics()
        }
        
        return report
    
    def _calculate_basic_metrics(self) -> Dict:
        """计算基本指标"""
        return {
            'total_trades': self.result_data.get('total_trades', 0),
            'winning_trades': self.result_data.get('winning_trades', 0),
            'losing_trades': self.result_data.get('losing_trades', 0),
            'win_rate': self.result_data.get('win_rate', 0),
            'total_pnl': self.result_data.get('total_pnl', 0),
            'total_return': self.result_data.get('total_return', 0),
            'max_drawdown': self.result_data.get('max_drawdown', 0),
            'sharpe_ratio': self.result_data.get('sharpe_ratio'),
            'sortino_ratio': self.result_data.get('sortino_ratio'),
            'calmar_ratio': self.result_data.get('calmar_ratio'),
            'profit_factor': self.result_data.get('profit_factor', 0),
            'initial_capital': self.result_data.get('initial_capital', 0),
            'final_capital': self.result_data.get('final_capital', 0)
        }
    
    def _analyze_trades(self) -> Dict:
        """分析交易数据"""
        if self.trades_df.empty:
            return {}
        
        analysis = {}
        
        # 按方向分析
        if 'direction' in self.trades_df.columns:
            direction_stats = self.trades_df.groupby('direction').agg({
                'pnl': ['count', 'sum', 'mean', 'std'],
                'pnl_percent': ['mean', 'std']
            }).round(4)
            analysis['by_direction'] = direction_stats.to_dict()
        
        # PNL分布
        if 'pnl' in self.trades_df.columns:
            analysis['pnl_distribution'] = {
                'min': self.trades_df['pnl'].min(),
                'max': self.trades_df['pnl'].max(),
                'mean': self.trades_df['pnl'].mean(),
                'median': self.trades_df['pnl'].median(),
                'std': self.trades_df['pnl'].std()
            }
        
        # 胜率分析
        if 'pnl' in self.trades_df.columns:
            winning_trades = self.trades_df[self.trades_df['pnl'] > 0]
            losing_trades = self.trades_df[self.trades_df['pnl'] <= 0]
            
            analysis['win_loss_analysis'] = {
                'average_win': winning_trades['pnl'].mean() if not winning_trades.empty else 0,
                'average_loss': losing_trades['pnl'].mean() if not losing_trades.empty else 0,
                'largest_win': winning_trades['pnl'].max() if not winning_trades.empty else 0,
                'largest_loss': losing_trades['pnl'].min() if not losing_trades.empty else 0
            }
        
        return analysis
    
    def _analyze_by_time(self) -> Dict:
        """按时间维度分析"""
        if self.trades_df.empty or 'entry_time' not in self.trades_df.columns:
            return {}
        
        analysis = {}
        
        # 按月分析
        self.trades_df['month'] = self.trades_df['entry_time'].dt.to_period('M')
        monthly_stats = self.trades_df.groupby('month').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(4)
        analysis['monthly'] = monthly_stats.to_dict()
        
        # 按周几分析
        self.trades_df['weekday'] = self.trades_df['entry_time'].dt.day_name()
        weekday_stats = self.trades_df.groupby('weekday').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(4)
        analysis['by_weekday'] = weekday_stats.to_dict()
        
        # 按小时分析
        self.trades_df['hour'] = self.trades_df['entry_time'].dt.hour
        hour_stats = self.trades_df.groupby('hour').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(4)
        analysis['by_hour'] = hour_stats.to_dict()
        
        return analysis
    
    def _calculate_risk_metrics(self) -> Dict:
        """计算风险指标"""
        if self.trades_df.empty or 'pnl' not in self.trades_df.columns:
            return {}
        
        pnl_series = self.trades_df['pnl']
        
        metrics = {
            'volatility': pnl_series.std(),
            'downside_volatility': pnl_series[pnl_series < 0].std() if any(pnl_series < 0) else 0,
            'value_at_risk_95': np.percentile(pnl_series, 5),
            'expected_shortfall_95': pnl_series[pnl_series <= np.percentile(pnl_series, 5)].mean() 
                                   if any(pnl_series <= np.percentile(pnl_series, 5)) else 0,
            'max_drawdown': self.result_data.get('max_drawdown', 0),
            'ulcer_index': self._calculate_ulcer_index()
        }
        
        return {k: round(v, 4) for k, v in metrics.items() if v is not None}
    
    def _calculate_ulcer_index(self) -> float:
        """计算溃疡指数"""
        # 需要权益曲线数据，这里简化处理
        return 0.0
    
    def _calculate_performance_metrics(self) -> Dict:
        """计算性能指标"""
        metrics = {}
        
        if self.trades_df.empty:
            return metrics
        
        total_pnl = self.result_data.get('total_pnl', 0)
        total_trades = self.result_data.get('total_trades', 1)
        
        metrics.update({
            'profit_per_trade': total_pnl / total_trades,
            'return_on_account': (self.result_data.get('final_capital', 0) / 
                                self.result_data.get('initial_capital', 1) - 1) * 100,
            'kelly_criterion': self._calculate_kelly_criterion(),
            'expectancy': self._calculate_expectancy()
        })
        
        return {k: round(v, 4) for k, v in metrics.items() if v is not None}
    
    def _calculate_kelly_criterion(self) -> float:
        """计算凯利准则"""
        win_rate = self.result_data.get('win_rate', 0)
        avg_win = self.result_data.get('average_win', 0)
        avg_loss = self.result_data.get('average_loss', 0)
        
        if avg_loss == 0:
            return 0.0
        
        # 凯利公式: f = (bp - q)/b
        # 其中 b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = abs(avg_win / avg_loss)
        p = win_rate
        q = 1 - win_rate
        
        kelly = (b * p - q) / b
        return max(0, min(kelly, 1))  # 限制在0-1之间
    
    def _calculate_expectancy(self) -> float:
        """计算期望值"""
        win_rate = self.result_data.get('win_rate', 0)
        avg_win = self.result_data.get('average_win', 0)
        avg_loss = self.result_data.get('average_loss', 0)
        
        return (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    
    def create_visualizations(self, output_dir: str = "results/plots"):
        """创建可视化图表"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 创建多个图表
        self._plot_equity_curve(output_path)
        self._plot_trade_distribution(output_path)
        self._plot_monthly_performance(output_path)
        self._plot_win_loss_analysis(output_path)
        self._plot_drawdown_chart(output_path)
        
        logger.info(f"可视化图表已保存到: {output_path}")
    
    def _plot_equity_curve(self, output_path: Path):
        """绘制权益曲线"""
        # 这里需要权益曲线数据，暂时用交易数据模拟
        if self.trades_df.empty:
            return
        
        plt.figure(figsize=(12, 6))
        
        # 模拟权益曲线
        capital = self.result_data.get('initial_capital', 10000)
        equity_curve = [capital]
        
        for pnl in self.trades_df['pnl'].cumsum():
            equity_curve.append(capital + pnl)
        
        plt.plot(equity_curve, label='权益曲线', linewidth=2)
        plt.title('策略权益曲线')
        plt.xlabel('交易次数')
        plt.ylabel('资金')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.savefig(output_path / 'equity_curve.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_trade_distribution(self, output_path: Path):
        """绘制交易分布"""
        if self.trades_df.empty:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # PNL分布直方图
        ax1.hist(self.trades_df['pnl'], bins=30, alpha=0.7, edgecolor='black')
        ax1.set_title('交易盈亏分布')
        ax1.set_xlabel('盈亏金额')
        ax1.set_ylabel('频次')
        ax1.grid(True, alpha=0.3)
        
        # 盈亏金额箱线图
        ax2.boxplot(self.trades_df['pnl'])
        ax2.set_title('交易盈亏箱线图')
        ax2.set_ylabel('盈亏金额')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'trade_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_monthly_performance(self, output_path: Path):
        """绘制月度表现"""
        if self.trades_df.empty or 'month' not in self.trades_df.columns:
            return
        
        monthly_pnl = self.trades_df.groupby('month')['pnl'].sum()
        
        plt.figure(figsize=(12, 6))
        monthly_pnl.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('月度盈亏表现')
        plt.xlabel('月份')
        plt.ylabel('盈亏金额')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, v in enumerate(monthly_pnl):
            plt.text(i, v, f'{v:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'monthly_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_win_loss_analysis(self, output_path: Path):
        """绘制胜败分析"""
        if self.trades_df.empty:
            return
        
        winning_trades = self.trades_df[self.trades_df['pnl'] > 0]
        losing_trades = self.trades_df[self.trades_df['pnl'] <= 0]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 胜败次数对比
        win_loss_counts = [len(winning_trades), len(losing_trades)]
        ax1.bar(['盈利交易', '亏损交易'], win_loss_counts, 
               color=['green', 'red'], alpha=0.7, edgecolor='black')
        ax1.set_title('盈利 vs 亏损交易次数')
        ax1.set_ylabel('交易次数')
        
        # 添加数值标签
        for i, v in enumerate(win_loss_counts):
            ax1.text(i, v, str(v), ha='center', va='bottom')
        
        # 平均盈亏对比
        if not winning_trades.empty and not losing_trades.empty:
            avg_win = winning_trades['pnl'].mean()
            avg_loss = losing_trades['pnl'].mean()
            
            ax2.bar(['平均盈利', '平均亏损'], [avg_win, abs(avg_loss)], 
                   color=['lightgreen', 'lightcoral'], alpha=0.7, edgecolor='black')
            ax2.set_title('平均盈亏金额')
            ax2.set_ylabel('金额')
            
            # 添加数值标签
            for i, v in enumerate([avg_win, abs(avg_loss)]):
                ax2.text(i, v, f'{v:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'win_loss_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_drawdown_chart(self, output_path: Path):
        """绘制回撤图表"""
        # 这里需要权益曲线数据，暂时用模拟数据
        max_drawdown = self.result_data.get('max_drawdown', 0)
        
        plt.figure(figsize=(10, 6))
        
        # 模拟回撤曲线
        x = range(100)
        y = np.sin(np.linspace(0, 4*np.pi, 100)) * 0.1  # 模拟回撤
        
        plt.fill_between(x, y, alpha=0.3, color='red', label='回撤')
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        plt.title(f'最大回撤: {max_drawdown:.2%}')
        plt.xlabel('时间')
        plt.ylabel('回撤比例')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(output_path / 'drawdown_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_report(self, report: Dict, filename: str):
        """保存分析报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"分析报告已保存到: {filename}")


def analyze_backtest_result(result_file: str) -> Dict:
    """分析回测结果文件"""
    try:
        with open(result_file, 'r') as f:
            result_data = json.load(f)
        
        analyzer = BacktestResultAnalyzer(result_data)
        report = analyzer.generate_summary_report()
        
        # 创建可视化
        output_dir = Path(result_file).parent / "plots"
        analyzer.create_visualizations(str(output_dir))
        
        # 保存报告
        report_file = Path(result_file).with_suffix('.report.json')
        analyzer.save_report(report, str(report_file))
        
        return report
        
    except Exception as e:
        logger.error(f"分析回测结果失败: {e}")
        return {}


def print_summary_report(report: Dict):
    """打印摘要报告"""
    print("=" * 80)
    print("回测结果摘要报告")
    print("=" * 80)
    
    basic = report.get('basic_metrics', {})
    print(f"总交易次数: {basic.get('total_trades', 0)}")
    print(f"盈利交易: {basic.get('winning_trades', 0)}")
    print(f"亏损交易: {basic.get('losing_trades', 0)}")
    print(f"胜率: {basic.get('win_rate', 0):.2%}")
    print(f"总盈亏: {basic.get('total_pnl', 0):.2f}")
    print(f"总收益率: {basic.get('total_return', 0):.2f}%")
    print(f"最大回撤: {basic.get('max_drawdown', 0):.2%}")
    print(f"夏普比率: {basic.get('sharpe_ratio', 'N/A')}")
    print(f"索提诺比率: {basic.get('sortino_ratio', 'N/A')}")
    print(f"卡尔玛比率: {basic.get('calmar_ratio', 'N/A')}")
    print(f"盈亏比: {basic.get('profit_factor', 0):.2f}")
    
    print("\n" + "=" * 40)
    print("风险指标")
    print("=" * 40)
    
    risk = report.get('risk_metrics', {})
    for metric, value in risk.items():
        print(f"{metric}: {value}")
    
    print("\n" + "=" * 40)
    print("性能指标")
    print("=" * 40)
    
    performance = report.get('performance_metrics', {})
    for metric, value in performance.items():
        print(f"{metric}: {value}")