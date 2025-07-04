# Panasonic Eolia For Homeassistant

Integrates Panasonic Eolia aircon units into homeassistant as `Climate` and `Temperature Sensor`

## Install

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dvcrn&repository=ha-panasonic-eolia&category=integration)

You can also install manually by copying the `custom_components` from this repository into your Home Assistant installation.

## Authentication

Either use a username/password pair, or a access_token/refresh_token pair

**Note**: For username/password, you currently need to disable 2fa/mfa as it's not implemented yet


## Development

Use the `docker-compose` file to spin up a dev container: `docker compose up`

Then add the "panasonic eolia" integration in homeassistant UI
