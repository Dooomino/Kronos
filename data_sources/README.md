# 数据源管理模块

## 概述

本模块提供统一的股票数据获取接口,支持多数据源自动切换,确保数据获取的稳定性和可靠性。

## 架构设计

```
data_sources/
├── __init__.py          # 包初始化,导出统一接口
├── base.py              # 数据源基类,定义标准接口
├── akshare_source.py    # AKShare数据源(东方财富+新浪)
├── baostock_source.py   # BaoStock数据源(稳定可靠)
├── fallback_source.py   # 模拟数据生成器(最后备选)
└── manager.py           # 数据源管理器,实现优先级调度
```

## 数据源优先级

系统按以下优先级依次尝试各个数据源:

1. **AKShare** (优先级: 1)
   - 子接口: 东方财富(主) → 新浪财经(备)
   - 特点: 完全免费,数据更新及时
   - 适用: 实时行情、分钟级数据
   
2. **BaoStock** (优先级: 2)
   - 特点: 无需注册,数据经过清洗,非常稳定
   - 适用: 历史回测、日线级别数据
   - 限制: 不提供实时行情

3. **Fallback** (优先级: 999)
   - 特点: 基于真实价格生成模拟数据
   - 适用: 测试和演示
   - 警告: 预测结果可能不准确

## 使用方法

### 基本用法

```python
from data_sources import DataSourceManager

# 创建管理器(默认启用所有数据源)
manager = DataSourceManager()

# 获取股票数据
df = manager.fetch("600580", adjust="qfq")

if df is not None:
    print(f"成功获取 {len(df)} 条数据")
    print(df.head())
else:
    print("所有数据源都失败")
```

### 指定启用的数据源

```python
# 只使用AKShare和BaoStock,禁用Fallback
manager = DataSourceManager(enabled_sources=['akshare', 'baostock'])

# 只使用BaoStock
manager = DataSourceManager(enabled_sources=['baostock'])
```

### 动态添加/移除数据源

```python
from data_sources import BaoStockSource

manager = DataSourceManager()

# 添加自定义数据源
custom_source = BaoStockSource(priority=1)
manager.add_source(custom_source)

# 移除数据源
manager.remove_source("Fallback(模拟数据)")
```

## 数据格式

所有数据源返回的DataFrame包含以下标准列:

| 列名 | 说明 | 类型 |
|------|------|------|
| timestamps | 日期时间 | datetime |
| stock_code | 股票代码 | str |
| open | 开盘价 | float |
| high | 最高价 | float |
| low | 最低价 | float |
| close | 收盘价 | float |
| volume | 成交量 | int |
| amount | 成交额 | float |
| pct_chg | 涨跌幅 | float |

## 复权类型

- `qfq`: 前复权 (默认)
- `hfq`: 后复权
- `""`: 不复权

## 如何添加新数据源

### 步骤1: 创建数据源类

```python
from data_sources.base import DataSource
from typing import Optional
import pandas as pd

class MyCustomSource(DataSource):
    def __init__(self, priority: int = 10):
        super().__init__(priority=priority)
    
    def fetch(self, stock_code: str, adjust: str = "qfq", **kwargs) -> Optional[pd.DataFrame]:
        # 实现数据获取逻辑
        # 返回标准化的DataFrame或None
        pass
    
    def get_name(self) -> str:
        return "MyCustomSource"
```

### 步骤2: 注册到管理器

在 `manager.py` 的 `__init__` 方法中添加:

```python
all_sources = [
    AKShareSource(priority=1),
    BaoStockSource(priority=2),
    MyCustomSource(priority=10),  # 新增
    FallbackSource(priority=999)
]
```

### 步骤3: 更新__init__.py

```python
from .my_custom_source import MyCustomSource

__all__ = [
    'DataSource',
    'AKShareSource',
    'BaoStockSource',
    'MyCustomSource',  # 新增
    'FallbackSource',
    'DataSourceManager'
]
```

## 常见问题

### Q1: 为什么AKShare经常失败?

A: AKShare基于爬虫,可能因以下原因失败:
- 网站改版导致接口变化
- IP被限制访问频率
- 网络连接问题

解决方案: 系统会自动切换到BaoStock,建议保持网络通畅。

### Q2: BaoStock需要注册吗?

A: 不需要。BaoStock完全免费,无需注册即可使用。

### Q3: 如何选择合适的数据源?

A: 建议策略:
- **实盘交易**: AKShare (实时性好)
- **历史回测**: BaoStock (数据稳定)
- **开发测试**: Fallback (无需网络)
- **生产环境**: 全部启用,让系统自动选择

### Q4: 缓存机制如何工作?

A: 
- 交易时间内: 使用1小时内的缓存
- 非交易时间: 使用24小时内的缓存
- 缓存文件位置: `cache/{stock_code}_{adjust}.csv`

### Q5: 如何禁用某个数据源?

A: 
```python
# 方法1: 初始化时指定
manager = DataSourceManager(enabled_sources=['akshare', 'baostock'])

# 方法2: 运行时移除
manager.remove_source("Fallback(模拟数据)")
```

## 依赖要求

确保已安装以下库:

```bash
pip install akshare>=1.12.0
pip install baostock>=0.8.8
pip install pandas>=2.2.2
pip install numpy
```

## 日志说明

模块使用项目统一的日志系统 (`StockPredictor` logger),日志级别:

- `INFO`: 正常操作流程
- `WARNING`: 数据源切换、降级等
- `ERROR`: 数据获取失败、异常

日志文件位置: `logs/stock_predictor_{date}.log`

## 最佳实践

1. **始终检查返回值**: `fetch()` 可能返回 `None`
2. **启用多个数据源**: 提高成功率
3. **合理使用缓存**: 减少重复请求
4. **关注日志输出**: 了解数据源状态
5. **定期更新依赖**: 保持数据源稳定性

## 扩展建议

未来可以考虑添加的数据源:

- **iTick**: 覆盖全球市场,提供WebSocket实时推送
- **Efinance**: 接口简单,专注A股/美股
- **Tushare Pro**: 数据规范,社区生态好(需积分)
- **Yahoo Finance**: 美股数据最全(yfinance库)

## 技术支持

如有问题,请查看:
- 项目日志: `logs/` 目录
- 示例代码: `examples/` 目录
- 主程序: `main.py`
