"""Constants for Proxmox Mail Gateway integration."""

DOMAIN = "pmg"

CONF_REALM = "realm"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_STATS_DAYS = "stats_days"

DEFAULT_PORT = 8006
DEFAULT_VERIFY_SSL = True
DEFAULT_SCAN_INTERVAL = 300  # seconds
DEFAULT_STATS_DAYS = 1

ATTRIBUTION = "Data provided by Proxmox Mail Gateway"

COOKIE_NAME = "PMGAuthCookie"

SERVICE_REBOOT = "reboot"
SERVICE_SHUTDOWN = "shutdown"
