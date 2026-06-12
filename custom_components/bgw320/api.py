"""BGW320 router API client."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

import aiohttp


class BGW320CannotConnect(Exception):
    """Raised when the router is unreachable or returns an unexpected response."""


@dataclass
class BGW320RouterInfo:
    """System information about the BGW320 router."""

    mac: str
    manufacturer: str
    model: str


@dataclass
class BGW320Device:
    """A device known to the BGW320 router."""

    mac: str
    hostname: str | None = field(default=None)
    ip_address: str | None = field(default=None)
    connection_type: str = field(default="")
    status: str = field(default="off")

    @property
    def is_wifi(self) -> bool:
        """Return True if this device is connected over Wi-Fi."""
        return self.connection_type.startswith("Wi-Fi")

    @property
    def is_connected(self) -> bool:
        """Return True if the router considers this device active."""
        return self.status == "on"


class _DeviceParser(HTMLParser):
    """Parse the BGW320 /cgi-bin/devices.ha page into BGW320Device objects."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.devices: list[BGW320Device] = []
        self._current: dict[str, str] = {}
        self._in_th = False
        self._in_td = False
        self._in_pre = False
        self._th_buf = ""
        self._td_buf = ""
        self._pre_buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "th":
            self._in_th = True
            self._th_buf = ""
        elif tag == "td":
            self._in_td = True
            self._td_buf = ""
        elif tag == "pre":
            self._in_pre = True
            self._pre_buf = ""
        elif tag == "br" and self._in_pre:
            self._pre_buf += "\n"
        elif tag == "hr" and "reshr" in (attrs_dict.get("class") or ""):
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self._in_th = False
        elif tag == "pre":
            self._in_pre = False
            self._store(self._th_buf.strip(), self._pre_buf.strip())
        elif tag == "td":
            self._in_td = False
            value = self._td_buf.strip()
            if value:
                self._store(self._th_buf.strip(), value)

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self._pre_buf += data
        elif self._in_td:
            self._td_buf += data
        elif self._in_th:
            self._th_buf += data

    def _store(self, key: str, value: str) -> None:
        if not key or not value:
            return
        if key == "MAC Address":
            self._current["mac"] = value.lower()
        elif key == "IPv4 Address / Name":
            ip, _, name = value.partition("/")
            self._current["ip_address"] = ip.strip() or None
            self._current["hostname"] = name.strip() or None
        elif key == "Name" and "hostname" not in self._current:
            self._current["hostname"] = value
        elif key == "Status":
            self._current["status"] = value
        elif key == "Connection Type":
            self._current["connection_type"] = value.split("\n")[0].strip()

    def _flush(self) -> None:
        if mac := self._current.get("mac"):
            self.devices.append(
                BGW320Device(
                    mac=mac,
                    hostname=self._current.get("hostname"),
                    ip_address=self._current.get("ip_address"),
                    connection_type=self._current.get("connection_type", ""),
                    status=self._current.get("status", "off"),
                )
            )
        self._current = {}

    def close(self) -> None:
        self._flush()
        super().close()


class _SysinfoParser(HTMLParser):
    """Parse the BGW320 /cgi-bin/sysinfo.ha page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._data: dict[str, str] = {}
        self._in_th = False
        self._in_td = False
        self._current_key = ""
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "th":
            self._in_th = True
            self._buf = ""
        elif tag == "td":
            self._in_td = True
            self._buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self._in_th = False
            self._current_key = self._buf.strip()
        elif tag == "td":
            self._in_td = False
            value = self._buf.strip()
            if self._current_key and value:
                self._data[self._current_key] = value
                self._current_key = ""

    def handle_data(self, data: str) -> None:
        if self._in_th or self._in_td:
            self._buf += data

    @property
    def router_info(self) -> BGW320RouterInfo | None:
        mac = self._data.get("MAC Address")
        manufacturer = self._data.get("Manufacturer")
        model = self._data.get("Model Number")
        if mac and manufacturer and model:
            return BGW320RouterInfo(mac=mac, manufacturer=manufacturer, model=model)
        return None


class BGW320Router:
    """Client for the BGW320 router web interface."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._devices_url = f"http://{host}/cgi-bin/devices.ha"
        self._sysinfo_url = f"http://{host}/cgi-bin/sysinfo.ha"

    async def get_router_info(self) -> BGW320RouterInfo:
        """Fetch and parse system information from the router."""
        try:
            async with self._session.get(self._sysinfo_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise BGW320CannotConnect(f"Unexpected HTTP {resp.status}")
                html = await resp.text(encoding="windows-1252")
        except aiohttp.ClientError as err:
            raise BGW320CannotConnect(str(err)) from err

        parser = _SysinfoParser()
        parser.feed(html)
        parser.close()

        info = parser.router_info
        if info is None:
            raise BGW320CannotConnect("Could not parse router info from sysinfo.ha")
        return info

    async def get_devices(self) -> list[BGW320Device]:
        """Fetch and parse the device list from the router."""
        try:
            async with self._session.get(self._devices_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise BGW320CannotConnect(f"Unexpected HTTP {resp.status}")
                html = await resp.text(encoding="windows-1252")
        except aiohttp.ClientError as err:
            raise BGW320CannotConnect(str(err)) from err

        parser = _DeviceParser()
        parser.feed(html)
        parser.close()
        return parser.devices

    async def get_wifi_devices(self) -> list[BGW320Device]:
        """Return only devices connected over Wi-Fi."""
        return [d for d in await self.get_devices() if d.is_wifi]
