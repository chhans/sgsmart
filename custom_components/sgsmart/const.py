"""Constants for custom_components/sgsmart."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "sgsmart"
ATTRIBUTION = "Data provided by SG Smart (https://leddimapp.sg-as.com/)"

# API endpoints
BASE_URL = "https://leddimapp.sg-as.com"
LOGIN_ENDPOINT = "/sg/api/login2"
DEVICE_ENDPOINT = "/sg/api/download"

ROUTE_URL = "https://sgapps2.ideaslab.hk/sgroute/route-api/server"
