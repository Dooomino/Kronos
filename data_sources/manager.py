"""
数据源管理器 - 实现多数据源优先级调度

按优先级依次尝试各个数据源,成功即返回
支持动态启用/禁用特定数据源
"""

from typing import Optional, List
import pandas as pd
import logging
from .base import DataSource
from .akshare_source import AKShareSource
from .baostock_source import BaoStockSource
from .fallback_source import FallbackSource

logger = logging.getLogger('StockPredictor')


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self, enabled_sources: Optional[List[str]] = None):
        """
        初始化数据源管理器
        
        Args:
            enabled_sources: 启用的数据源列表,默认为None(全部启用)
                           可选值: ['akshare', 'baostock', 'fallback']
        """
        # 创建所有数据源实例
        all_sources = [
            AKShareSource(priority=1),
            BaoStockSource(priority=2),
            FallbackSource(priority=999)
        ]
        
        # 根据配置过滤数据源
        if enabled_sources:
            self.sources = [
                source for source in all_sources
                if self._get_source_key(source) in enabled_sources
            ]
            logger.info(f"📊 已启用数据源: {enabled_sources}")
        else:
            self.sources = all_sources
            logger.info("📊 已启用所有数据源")
        
        # 按优先级排序
        self.sources.sort(key=lambda x: x.priority)
        
        logger.info(f"📊 数据源优先级: {[s.get_name() for s in self.sources]}")
    
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        """
        获取股票数据,按优先级尝试各个数据源
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
            **kwargs: 其他参数
            
        Returns:
            DataFrame或None
        """
        logger.info(f"🔄 开始获取 {stock_code} 数据 (adjust={adjust})")
        
        for source in self.sources:
            try:
                # 检查数据源是否可用
                if not source.is_available():
                    logger.warning(f"⚠️ {source.get_name()} 不可用,跳过")
                    continue
                
                logger.info(f"🔄 尝试数据源: {source.get_name()} (优先级:{source.priority})")
                
                # 获取数据
                df = source.fetch(stock_code, adjust, **kwargs)
                
                # 验证数据有效性
                if df is not None and not df.empty:
                    logger.info(f"✅ 成功从 {source.get_name()} 获取 {len(df)} 条数据")
                    
                    # 标准化数据结构
                    df = self._standardize_dataframe(df, stock_code)
                    
                    if df is not None:
                        return df
                    else:
                        logger.warning(f"⚠️ {source.get_name()} 数据标准化失败")
                else:
                    logger.warning(f"⚠️ {source.get_name()} 返回空数据")
                    
            except Exception as e:
                logger.warning(f"⚠️ {source.get_name()} 失败: {e}")
                continue
        
        # 所有数据源都失败
        logger.error(f"❌ 所有数据源都失败,无法获取 {stock_code} 的数据")
        return None
    
    def get_available_sources(self) -> List[str]:
        """
        获取可用的数据源名称列表
        
        Returns:
            数据源名称列表
        """
        return [source.get_name() for source in self.sources]
    
    def add_source(self, source: DataSource):
        """
        动态添加数据源
        
        Args:
            source: 数据源实例
        """
        self.sources.append(source)
        self.sources.sort(key=lambda x: x.priority)
        logger.info(f"✅ 已添加数据源: {source.get_name()} (优先级:{source.priority})")
    
    def remove_source(self, source_name: str) -> bool:
        """
        移除数据源
        
        Args:
            source_name: 数据源名称
            
        Returns:
            True表示成功移除, False表示未找到
        """
        for i, source in enumerate(self.sources):
            if source.get_name() == source_name:
                removed = self.sources.pop(i)
                logger.info(f"🗑️ 已移除数据源: {removed.get_name()}")
                return True
        
        logger.warning(f"⚠️ 未找到数据源: {source_name}")
        return False
    
    def _get_source_key(self, source: DataSource) -> str:
        """
        获取数据源的键名
        
        Args:
            source: 数据源实例
            
        Returns:
            键名字符串
        """
        class_name = source.__class__.__name__.lower()
        if 'akshare' in class_name:
            return 'akshare'
        elif 'baostock' in class_name:
            return 'baostock'
        elif 'fallback' in class_name:
            return 'fallback'
        return class_name
    
    def _standardize_dataframe(self, df: pd.DataFrame, stock_code: str) -> Optional[pd.DataFrame]:
        """
        标准化DataFrame结构,确保所有数据源输出一致
        
        Args:
            df: 原始DataFrame
            stock_code: 股票代码
            
        Returns:
            标准化后的DataFrame或None
        """
        try:
            # 确保必要的列存在
            required_columns = ['timestamps', 'open', 'high', 'low', 'close', 'volume']
            
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"❌ 缺少必要列: {col}")
                    return None
            
            # 添加缺失的列(如果有)
            if 'amount' not in df.columns:
                if 'close' in df.columns and 'volume' in df.columns:
                    df['amount'] = df['close'] * df['volume']
                else:
                    df['amount'] = 0.0
            
            if 'pct_chg' not in df.columns and len(df) > 1:
                df['pct_chg'] = df['close'].pct_change() * 100
            elif 'pct_chg' not in df.columns:
                df['pct_chg'] = 0.0
            
            # 确保数据类型正确
            df['timestamps'] = pd.to_datetime(df['timestamps'])
            df = df.sort_values('timestamps').reset_index(drop=True)
            
            # 添加股票代码(如果不存在)
            if 'stock_code' not in df.columns:
                df['stock_code'] = stock_code
            
            # 选择标准列
            standard_columns = [
                'timestamps', 'stock_code', 'open', 'high', 'low', 
                'close', 'volume', 'amount', 'pct_chg'
            ]
            available_columns = [col for col in standard_columns if col in df.columns]
            df = df[available_columns]
            
            logger.info(f"✅ 数据结构标准化完成: {len(df)} 条记录, {len(available_columns)} 个字段")
            return df
            
        except Exception as e:
            logger.error(f"❌ 数据标准化失败: {e}", exc_info=True)
            return None
