"""Constants for the 西安天然气 integration."""

DOMAIN = "xian_gas"
NAME = "西安天然气"

CONF_USER_ID = "user_id"
CONF_CARD_ID = "card_id"
CONF_XIUZHENG = "xiuzheng"
CONF_TOKEN_S = "token_s"

DEFAULT_USER_ID = "oh2fKv_y8EklO9SBi_sMtTgGhlns"
DEFAULT_CARD_ID = "0842342294"
DEFAULT_TOKEN_S = "4cb8b5dba52130ac0ce23d5eeea64dca"
DEFAULT_XIUZHENG = 0

API_ENDPOINT = "http://wkf.qhgas.com/rs/WX/searchInvoice"

ATTR_PRICE = "price"
ATTR_BALANCE = "balance"
ATTR_USAGE_DAYS = "usage_days"
ATTR_DATA = "data"

from datetime import timedelta
SCAN_INTERVAL = timedelta(seconds=86400)  # 24 hours