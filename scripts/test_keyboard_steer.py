import keyboard_steer as ks


def test_build_lkas11_checksum():
  msg = ks.build_lkas11(100, 0)
  assert len(msg) == 8
  assert msg[-1] == ks.checksum(msg[:-1])
