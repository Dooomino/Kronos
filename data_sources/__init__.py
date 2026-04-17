"""
数据源管理包 - 提供统一的股票数据获取接口

支持多数据源自动切换,包括:
- AKShare (东方财富/新浪财经)
- BaoStock (无需注册,稳定可靠)
- Fallback (模拟数据,最后备选)
"""

from .base import DataSource
from .akshare_source import AKShareSource
from .baostock_source import BaoStockSource
from .fallback_source import FallbackSource
from .manager import DataSourceManager

__all__ = [
    'DataSource',
    'AKShareSource',
    'BaoStockSource',
    'FallbackSource',
    'DataSourceManager'
]
