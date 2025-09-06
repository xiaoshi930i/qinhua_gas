"""HTTP client for 西安天然气."""
import logging
from datetime import datetime
import aiohttp
import async_timeout
import json

from .const import API_ENDPOINT

_LOGGER = logging.getLogger(__name__)

class XianGasClient:
    """西安天然气 API client."""

    def __init__(self, user_id, card_id, xiuzheng, token_s):
        """Initialize the client."""
        self.user_id = user_id
        self.card_id = card_id
        self.xiuzheng = float(xiuzheng)
        self.token_s = token_s
        self.session = None

    async def async_get_data(self):
        """Get data from the API."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        payload = {"data":{"userId":self.user_id,"cardId":self.card_id},"tokenS":self.token_s}
        async with async_timeout.timeout(20):
            response = await self.session.post(
                API_ENDPOINT,
                data=json.dumps(payload, separators=(',', ':')),
                headers={"Content-Type": "application/json"}
            )
            
            response_json = await response.json()
            _LOGGER.info("API response: %s", response_json)
            
            cleaned_data = self._clean_invoice_data(response_json)
            _LOGGER.info("Cleaned data: %s", cleaned_data)
            
            gas_usage = self._calculate_gas_usage(cleaned_data)
            _LOGGER.info("Gas usage calculation result: %s", gas_usage)
            
            result = {
                "ranqi": gas_usage,
                "ranqidata": cleaned_data
            }
            
            _LOGGER.info("返回数据: %s", result)
            return result

    def _clean_invoice_data(self, original_data):
        """Clean the invoice data."""
        try:
            _LOGGER.info("Original data type: %s", type(original_data))
            
            # 处理字符串或对象
            if isinstance(original_data, str):
                try:
                    data = json.loads(original_data)
                    _LOGGER.info("Parsed JSON from string")
                except json.JSONDecodeError as e:
                    _LOGGER.error("Failed to parse JSON string: %s", e)
                    return []
            else:
                data = original_data
            
            # 检查数据结构
            if isinstance(data, dict) and "data" in data:
                _LOGGER.info("Found 'data' key in response")
                data = data.get("data", [])
            
            # 确保数据是列表类型
            if not isinstance(data, list):
                _LOGGER.warning("Data is not a list, type: %s", type(data))
                data = []
            
            cleaned_data = []
            for item in data:
                if not isinstance(item, dict):
                    _LOGGER.warning("Item is not a dictionary: %s", item)
                    continue
                    
                date_value = item.get("dt", "")
                cost_value = item.get("fee", 0)
                
                # 确保日期格式正确
                if not date_value:
                    _LOGGER.warning("Missing date value")
                    continue
                    
                if not self._is_valid_date_format(date_value):
                    _LOGGER.warning("Invalid date format: %s, expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS", date_value)
                    continue
                
                # 确保费用是数字
                try:
                    cost_value = float(cost_value)
                except (ValueError, TypeError):
                    _LOGGER.warning("Invalid cost value: %s", cost_value)
                    cost_value = 0
                
                cleaned_data.append({
                    "date": date_value,  # 交易日期
                    "cost": cost_value   # 开票金额
                })
            
            _LOGGER.info("Cleaned data count: %s", len(cleaned_data))
            return cleaned_data
        except Exception as err:
            _LOGGER.error("Error cleaning invoice data: %s", err)
            return []
            
    def _is_valid_date_format(self, date_str):
        """Check if the date string has a valid format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)."""
        try:
            # 尝试解析 YYYY-MM-DD 格式
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            try:
                # 尝试解析 YYYY-MM-DD HH:MM:SS 格式
                datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return True
            except ValueError:
                return False

    def _calculate_gas_usage(self, data):
        """Calculate gas usage statistics."""
        try:
            _LOGGER.info("Gas usage calculation data: %s", data)
            if not data:
                _LOGGER.warning("No data available to calculate gas usage")
                return None
            if len(data) < 2:
                _LOGGER.warning("Insufficient data to calculate gas usage, need at least 2 records, got %s", len(data))
                return None
                
            # 解析日期
            try:
                # 尝试解析日期，支持两种格式
                first_date_str = data[0]["date"]
                last_date_str = data[-1]["date"]
                
                # 解析第一个日期
                try:
                    first_date = datetime.strptime(first_date_str, "%Y-%m-%d")
                except ValueError:
                    first_date = datetime.strptime(first_date_str, "%Y-%m-%d %H:%M:%S")
                
                # 解析最后一个日期
                try:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                except ValueError:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d %H:%M:%S")
                
                _LOGGER.info("First date: %s, Last date: %s", first_date, last_date)
            except ValueError as e:
                _LOGGER.error("Date parsing error: %s. Date format should be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS", e)
                _LOGGER.error("First record date: %s, Last record date: %s", 
                             data[0].get("date", "missing"), data[-1].get("date", "missing"))
                return None
            
            # 计算天数差，向上取整
            s1 = (last_date - first_date).days
            s1 = abs(s1) if s1 != 0 else 1  # 确保不为零
            
            # 计算除第一条外所有记录的费用总和
            a = sum(float(item["cost"]) for item in data[1:])
            
            # 计算每日消耗
            c = a / s1
            
            # 计算从第一条记录到今天的天数
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            s2 = abs((today - first_date).days)
            
            # 计算剩余金额和可用天数
            b = float(data[0]["cost"]) + self.xiuzheng
            estimated_balance = b - (c * s2) + 10 + self.xiuzheng  # 加上10和调整参数
            estimated_usage_days = estimated_balance / c if c > 0 else 0
            
            return {
                "price": round(c, 2),
                "balance": round(estimated_balance, 2),
                "usage_days": int(estimated_usage_days),
                "data": data
            }
        except (ValueError, ZeroDivisionError) as err:
            _LOGGER.error("Error calculating gas usage: %s", err)
            return None

    async def async_close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None