# BGW320 Home Assistant Integration

Tracks devices connected to your AT&T BGW320 router as Home Assistant device trackers. Each Wi-Fi client appears as a device under the router hub, with a presence entity (`home`/`not_home`) that reflects its current connection status.

## Installation

### Manual

Copy the `custom_components/bgw320` directory into your Home Assistant `custom_components` folder:

```
config/
└── custom_components/
    └── bgw320/
        └── __init__.py
        └── manifest.json
        └── ...
```

Restart Home Assistant, then go to **Settings → Devices & Services → Add Integration** and search for **BGW320**.

Enter your router's IP address (default: `192.168.1.254`) and click **Submit**.
