"""
AKShare数据源 - 基于爬虫的免费数据接口

支持两个子接口:
- 东方财富 (主接口)
- 新浪财经 (备用接口)

特点:
- 完全免费,无需注册
- 数据更新及时
- 但可能因网站改版而失效
"""

from typing import Optional
import pandas as pd
import time
import random
import logging
from .base import DataSource

logger = logging.getLogger('StockPredictor')


class AKShareSource(DataSource):
    """AKShare数据源实现"""
    
    def __init__(self, priority: int = 1, max_retries: int = 3):
        """
        初始化AKShare数据源
        
        Args:
            priority: 优先级,默认为1(最高)
            max_retries: 最大重试次数
        """
        super().__init__(priority=priority)
        self.max_retries = max_retries
    
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        """
        从AKShare获取股票数据,优先使用东方财富,失败则尝试新浪
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
            
        Returns:
            DataFrame或None
        """
        # 先尝试东方财富
        df = self._fetch_from_eastmoney(stock_code, adjust)
        if df is not None and not df.empty:
            return df
        
        # 东方财富失败,尝试新浪
        logger.info(f"🔄 [AKShare] 东方财富失败,尝试新浪财经...")
        df = self._fetch_from_sina(stock_code, adjust)
        
        return df
    
    def get_name(self) -> str:
        """获取数据源名称"""
        return "AKShare"
    
    def _fetch_from_eastmoney(self, stock_code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """
        从东方财富获取数据
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
            
        Returns:
            DataFrame或None
        """
        try:
            import akshare as ak
        except ImportError:
            logger.error("❌ [AKShare] 未安装akshare库,请使用 pip install akshare 安装")
            return None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"📡 [AKShare-东方财富] 正在获取 {stock_code}... (尝试 {attempt}/{self.max_retries})")
                
                # 添加随机延迟
                if attempt > 1:
                    base_delay = 3 * attempt
                    jitter = random.uniform(0.5, 2.0)
                    delay = base_delay + jitter
                    logger.info(f"⏳ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(0.5, 1.5))
                
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    adjust=adjust,
                    start_date="20200101",
                    end_date="20261231"
                )
                
                if df is None or df.empty:
                    logger.warning(f"❌ [AKShare-东方财富] 未获取到数据")
                    if attempt < self.max_retries:
                        continue
                    return None
                
                # 列映射
                column_mapping = {
                    '日期': 'timestamps',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '涨跌幅': 'pct_chg'
                }
                
                actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
                df = df.rename(columns=actual_mapping)
                
                if 'timestamps' not in df.columns:
                    logger.error("❌ [AKShare-东方财富] 缺少必要列")
                    return None
                
                df['timestamps'] = pd.to_datetime(df['timestamps'])
                df = df.sort_values('timestamps').reset_index(drop=True)
                
                logger.info(f"✅ [AKShare-东方财富] 成功获取 {len(df)} 条数据")
                return df
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ [AKShare-东方财富] 失败 (尝试 {attempt}/{self.max_retries}): {error_msg}")
                
                if 'Connection' in error_msg or 'RemoteDisconnected' in error_msg:
                    logger.warning("💡 [AKShare-东方财富] 网络问题,将重试...")
                elif '403' in error_msg or 'Forbidden' in error_msg:
                    logger.warning("💡 [AKShare-东方财富] IP可能被限制")
                    return None  # 403不需要重试
                
                if attempt < self.max_retries:
                    continue
                return None
        
        return None
    
    def _fetch_from_sina(self, stock_code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """
        从新浪财经获取数据(备用)
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
            
        Returns:
            DataFrame或None
        """
        try:
            import akshare as ak
        except ImportError:
            return None
        
        try:
            logger.info(f"📡 [AKShare-新浪] 正在获取 {stock_code}...")
            time.sleep(1)  # 延迟避免请求过快
            
            # 使用新浪接口
            df = ak.stock_zh_a_daily(symbol=stock_code, adjust=adjust)
            
            if df is None or df.empty:
                logger.warning("❌ [AKShare-新浪] 未获取到数据")
                return None
            
            # 列映射
            column_mapping = {
                'date': 'timestamps',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'volume'
            }
            
            actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=actual_mapping)
            
            if 'timestamps' not in df.columns:
                logger.error("❌ [AKShare-新浪] 缺少必要列")
                return None
            
            df['timestamps'] = pd.to_datetime(df['timestamps'])
            df = df.sort_values('timestamps').reset_index(drop=True)
            
            # 计算成交额(如果缺失)
            if 'amount' not in df.columns and 'close' in df.columns and 'volume' in df.columns:
                df['amount'] = df['close'] * df['volume']
            
            logger.info(f"✅ [AKShare-新浪] 成功获取 {len(df)} 条数据")
            return df
            
        except Exception as e:
            logger.error(f"❌ [AKShare-新浪] 失败: {e}")
            return None
