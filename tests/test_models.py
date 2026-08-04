import pytest
from cyberhotspot.models import HotspotConfig


def test_valid_config():
    HotspotConfig("CyberHotspot", "12345678").validate()


@pytest.mark.parametrize("password", ["", "1234567"])
def test_short_password(password):
    with pytest.raises(ValueError):
        HotspotConfig("CyberHotspot", password).validate()


def test_ssid_limit():
    with pytest.raises(ValueError):
        HotspotConfig("x" * 33, "12345678").validate()
