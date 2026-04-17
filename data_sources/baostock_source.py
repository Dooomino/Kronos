"""
BaoStock数据源 - 稳定可靠的A股数据接口

特点:
- 无需注册,完全免费
- 数据经过清洗,很少出现缺失或错误
- 适合长线策略回测(日线级别)
- 不提供实时行情,主要是历史数据
"""

from typing import Optional
import pandas as pd
import logging
from .base import DataSource

logger = logging.getLogger('StockPredictor')


class BaoStockSource(DataSource):
    """BaoStock数据源实现"""
    
    def __init__(self, priority: int = 2):
        """
        初始化BaoStock数据源
        
        Args:
            priority: 优先级,默认为2(次于AKShare)
        """
        super().__init__(priority=priority)
        self._logged_in = False
    
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        """
        从BaoStock获取股票数据
        
        Args:
            stock_code: 股票代码 (如: 600580)
            adjust: 复权类型 (qfq=前复权, hfq=后复权, 空字符串=不复权)
            
        Returns:
            DataFrame或None
        """
        try:
            import baostock as bs
        except ImportError:
            logger.error("❌ [BaoStock] 未安装baostock库,请使用 pip install baostock 安装")
            return None
        
        try:
            logger.info(f"📡 [BaoStock] 正在获取 {stock_code}...")
            
            # 登录系统
            if not self._login():
                logger.error("❌ [BaoStock] 登录失败")
                return None
            
            # 根据市场添加前缀
            full_code = self._format_stock_code(stock_code)
            logger.info(f"📡 [BaoStock] 查询代码: {full_code}")
            
            # 获取上市日期
            list_date = self._get_list_date(full_code)
            if not list_date:
                logger.warning(f"⚠️ [BaoStock] 无法获取 {stock_code} 的上市日期,使用默认起始日期")
                list_date = "2020-01-01"
            else:
                logger.info(f"📅 [BaoStock] 上市日期: {list_date}")
            
            # 映射复权类型
            # BaoStock: 1=后复权, 2=前复权, 3=不复权
            adjust_flag_map = {
                "qfq": "2",   # 前复权
                "hfq": "1",   # 后复权
                "": "3"       # 不复权
            }
            adjust_flag = adjust_flag_map.get(adjust, "2")
            
            # 获取K线数据
            rs = bs.query_history_k_data_plus(
                full_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=list_date,
                end_date="",  # 空表示到今天
                frequency="d",
                adjustflag=adjust_flag
            )
            
            if rs.error_code != '0':
                logger.error(f"❌ [BaoStock] 查询失败: {rs.error_msg}")
                self._logout()
                return None
            
            # 解析数据
            data_list = []
            while (rs.error_code == '0') and rs.next():
                data_list.append(rs.get_row_data())
            
            # 登出系统
            self._logout()
            
            if not data_list:
                logger.warning(f"⚠️ [BaoStock] 未获取到 {stock_code} 的数据")
                return None
            
            # 创建DataFrame
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 数据类型转换
            df = self._convert_types(df)
            
            # 重命名列以匹配标准格式
            df = self._rename_columns(df)
            
            # 添加股票代码
            df['stock_code'] = stock_code
            
            # 清理无效数据
            df = df.dropna(subset=['timestamps', 'close'])
            df = df.sort_values('timestamps').reset_index(drop=True)
            
            logger.info(f"✅ [BaoStock] 成功获取 {len(df)} 条数据")
            logger.info(f"📅 [BaoStock] 时间范围: {df['timestamps'].min()} 到 {df['timestamps'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ [BaoStock] 获取失败: {e}", exc_info=True)
            self._logout()
            return None
    
    def get_name(self) -> str:
        """获取数据源名称"""
        return "BaoStock"
    
    def _login(self) -> bool:
        """
        登录BaoStock系统
        
        Returns:
            True表示成功, False表示失败
        """
        if self._logged_in:
            return True
        
        try:
            import baostock as bs
            lg = bs.login()
            
            if lg.error_code != '0':
                logger.error(f"❌ [BaoStock] 登录失败: {lg.error_msg}")
                return False
            
            self._logged_in = True
            logger.debug("✅ [BaoStock] 登录成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ [BaoStock] 登录异常: {e}")
            return False
    
    def _logout(self):
        """登出BaoStock系统"""
        if self._logged_in:
            try:
                import baostock as bs
                bs.logout()
                self._logged_in = False
                logger.debug("✅ [BaoStock] 已登出")
            except Exception as e:
                logger.warning(f"⚠️ [BaoStock] 登出异常: {e}")
    
    def _format_stock_code(self, stock_code: str) -> str:
        """
        格式化股票代码,添加市场前缀
        
        Args:
            stock_code: 原始股票代码
            
        Returns:
            带市场前缀的代码 (如: sh.600580 或 sz.000001)
        """
        # 根据首位判断市场
        if stock_code.startswith(('6', '9')):
            # 上海交易所
            return f"sh.{stock_code}"
        elif stock_code.startswith(('0', '3')):
            # 深圳交易所
            return f"sz.{stock_code}"
        else:
            # 默认深圳
            logger.warning(f"⚠️ [BaoStock] 未知市场代码 {stock_code}, 假设为深圳市场")
            return f"sz.{stock_code}"
    
    def _get_list_date(self, full_code: str) -> Optional[str]:
        """
        获取股票上市日期
        
        Args:
            full_code: 带市场前缀的股票代码
            
        Returns:
            上市日期字符串 (YYYY-MM-DD) 或 None
        """
        try:
            import baostock as bs
            
            rs = bs.query_stock_basic(code=full_code)
            
            if rs.error_code != '0':
                logger.warning(f"⚠️ [BaoStock] 获取基本信息失败: {rs.error_msg}")
                return None
            
            # 解析结果
            while (rs.error_code == '0') and rs.next():
                row_data = rs.get_row_data()
                if len(row_data) > 2:
                    list_date = row_data[2]  # 上市日期在第3个字段
                    if list_date and list_date != '':
                        return list_date
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ [BaoStock] 获取上市日期异常: {e}")
            return None
    
    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        转换DataFrame列的数据类型
        
        Args:
            df: 原始DataFrame
            
        Returns:
            转换后的DataFrame
        """
        # 转换日期
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # 转换数值列
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重命名列以匹配标准格式
        
        Args:
            df: 原始DataFrame
            
        Returns:
            重命名后的DataFrame
        """
        column_mapping = {
            'date': 'timestamps',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'turn': 'turnover',
            'pctChg': 'pct_chg'
        }
        
        # 只重命名存在的列
        actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=actual_mapping)
        
        return df
