"""Config flow for 西安天然气 integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    NAME,
    CONF_USER_ID,
    CONF_CARD_ID,
    CONF_XIUZHENG,
    CONF_TOKEN_S,
    DEFAULT_USER_ID,
    DEFAULT_CARD_ID,
    DEFAULT_XIUZHENG,
    DEFAULT_TOKEN_S,
)
from .http_client import XianGasClient

_LOGGER = logging.getLogger(__name__)

class XianGasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 西安天然气."""

    VERSION = 1
    
    async def async_step_import(self, import_info=None) -> FlowResult:
        """Handle import from configuration."""
        return await self.async_step_user(import_info)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            client = XianGasClient(
                user_input[CONF_USER_ID],
                user_input[CONF_CARD_ID],
                user_input[CONF_XIUZHENG],
                user_input[CONF_TOKEN_S],
            )

            try:
                result = await client.async_get_data()
                await client.async_close()
                
                if result:
                    return self.async_create_entry(
                        title=f"{NAME} - {user_input[CONF_CARD_ID]}",
                        data=user_input,
                    )
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USER_ID, default=DEFAULT_USER_ID): str,
                    vol.Required(CONF_CARD_ID, default=DEFAULT_CARD_ID): str,
                    vol.Required(CONF_XIUZHENG, default=DEFAULT_XIUZHENG): vol.Coerce(float),
                    vol.Required(CONF_TOKEN_S, default=DEFAULT_TOKEN_S): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return XianGasOptionsFlowHandler(config_entry)


class XianGasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # 确保修正值是浮点数
            if CONF_XIUZHENG in user_input:
                try:
                    user_input[CONF_XIUZHENG] = float(user_input[CONF_XIUZHENG])
                except (ValueError, TypeError):
                    user_input[CONF_XIUZHENG] = DEFAULT_XIUZHENG
            
            _LOGGER.info("更新配置选项，修正值: %s", user_input.get(CONF_XIUZHENG))
            return self.async_create_entry(title="", data=user_input)

        # 优先从 options 中获取值，如果没有则从 data 中获取
        user_id = self.config_entry.options.get(
            CONF_USER_ID, 
            self.config_entry.data.get(CONF_USER_ID, DEFAULT_USER_ID)
        )
        card_id = self.config_entry.options.get(
            CONF_CARD_ID, 
            self.config_entry.data.get(CONF_CARD_ID, DEFAULT_CARD_ID)
        )
        xiuzheng = self.config_entry.options.get(
            CONF_XIUZHENG, 
            self.config_entry.data.get(CONF_XIUZHENG, DEFAULT_XIUZHENG)
        )
        token_s = self.config_entry.options.get(
            CONF_TOKEN_S, 
            self.config_entry.data.get(CONF_TOKEN_S, DEFAULT_TOKEN_S)
        )
        
        _LOGGER.info("显示配置表单，当前修正值: %s", xiuzheng)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USER_ID, default=user_id): str,
                    vol.Required(CONF_CARD_ID, default=card_id): str,
                    vol.Required(CONF_XIUZHENG, default=xiuzheng): vol.Coerce(float),
                    vol.Required(CONF_TOKEN_S, default=token_s): str,
                }
            ),
        )
