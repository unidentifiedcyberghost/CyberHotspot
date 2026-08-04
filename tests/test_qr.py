from cyberhotspot.qr import wifi_payload


def test_qr_payload():
    value = wifi_payload("TestNet", "password123")
    assert value.startswith("WIFI:T:WPA;")
    assert "S:TestNet;" in value
