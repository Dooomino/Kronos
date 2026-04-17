"""
数据源基类 - 定义统一的数据源接口

所有具体数据源必须继承此类并实现相应方法
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, priority: int = 999):
        """
        初始化数据源
        
        Args:
            priority: 优先级,数字越小优先级越高
        """
        self.priority = priority
    
    @abstractmethod
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            stock_code: 股票代码 (如: 600580)
            adjust: 复权类型 (qfq=前复权, hfq=后复权, 空字符串=不复权)
            **kwargs: 其他参数
            
        Returns:
            DataFrame包含以下列:
            - timestamps: 日期时间
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额 (可选)
            - pct_chg: 涨跌幅 (可选)
            
            如果获取失败返回 None
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取数据源名称
        
        Returns:
            数据源名称字符串
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查数据源是否可用
        
        Returns:
            True表示可用, False表示不可用
        """
        # 默认实现: 假设总是可用
        # 子类可以重写此方法以实现更复杂的可用性检查
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(priority={self.priority})"
