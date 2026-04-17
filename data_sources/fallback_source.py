"""
Fallback数据源 - 模拟数据生成器

当所有真实数据源都失败时使用,基于真实价格生成模拟数据
仅用于测试和演示,预测结果可能不准确
"""

from typing import Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from .base import DataSource

logger = logging.getLogger('StockPredictor')


class FallbackSource(DataSource):
    """Fallback模拟数据源实现"""
    
    # 真实股票参考价格
    REAL_STOCK_REFERENCES = {
        '600580': {'name': '卧龙电驱', 'current_price': 38.54, 'range': (30.0, 50.0)},
        '300207': {'name': '欣旺达', 'current_price': 33.79, 'range': (28.0, 45.0)},
        '000001': {'name': '平安银行', 'current_price': 12.50, 'range': (10.0, 16.0)},
    }
    
    def __init__(self, priority: int = 999):
        """
        初始化Fallback数据源
        
        Args:
            priority: 优先级,默认为999(最低,仅作为最后备选)
        """
        super().__init__(priority=priority)
    
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        """
        生成模拟股票数据
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型(此参数对模拟数据无效)
            
        Returns:
            DataFrame或None
        """
        try:
            logger.warning(f"⚠️ [Fallback] 所有API失败,生成模拟数据用于测试")
            
            # 获取股票参考信息
            stock_info = self.REAL_STOCK_REFERENCES.get(stock_code, {
                'name': f'股票{stock_code}',
                'current_price': 20.0,
                'range': (15.0, 30.0)
            })
            
            # 生成最近1年的交易日数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            dates = pd.bdate_range(start=start_date, end=end_date, freq='B')
            
            np.random.seed(42)
            n_points = len(dates)
            current_price = stock_info['current_price']
            min_price, max_price = stock_info['range']
            
            # 反向生成价格序列
            prices = [current_price]
            for i in range(1, n_points):
                volatility = 0.02
                historical_return = np.random.normal(-0.0002, volatility)
                prev_price = prices[0] * (1 + historical_return)
                prev_price = max(min_price * 0.9, min(max_price * 1.1, prev_price))
                prices.insert(0, prev_price)
            
            # 生成OHLC数据
            stock_data = []
            for i, date in enumerate(dates):
                close_price = prices[i]
                daily_volatility = abs(np.random.normal(0, 0.015))
                open_price = close_price * (1 + np.random.normal(0, 0.005))
                high_price = max(open_price, close_price) * (1 + daily_volatility)
                low_price = min(open_price, close_price) * (1 - daily_volatility)
                
                high_price = max(open_price, close_price, low_price, high_price)
                low_price = min(open_price, close_price, high_price, low_price)
                
                volume = int(abs(np.random.normal(1500000, 400000)))
                amount = volume * close_price
                
                pct_chg = ((close_price - prices[i-1]) / prices[i-1]) * 100 if i > 0 else 0
                
                stock_data.append({
                    'timestamps': date,
                    'stock_code': stock_code,
                    'open': round(open_price, 2),
                    'close': round(close_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'volume': volume,
                    'amount': round(amount, 2),
                    'pct_chg': round(pct_chg, 2)
                })
            
            df = pd.DataFrame(stock_data)
            
            logger.warning(f"⚠️ [Fallback] 已生成 {len(df)} 条模拟数据(仅供参考)")
            print("⚠️ 注意:使用的是模拟数据,预测结果可能不准确!")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ [Fallback] 生成失败: {e}", exc_info=True)
            return None
    
    def get_name(self) -> str:
        """获取数据源名称"""
        return "Fallback(模拟数据)"
    
    def is_available(self) -> bool:
        """
        检查数据源是否可用
        Fallback总是可用
        """
        return True
