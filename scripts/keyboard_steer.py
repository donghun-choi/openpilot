#!/usr/bin/env python3
"""
Keyboard based lateral control using a Panda connected over USB.

Press 's' to request a small left steering torque and 'd' for right.
This uses the Kia K5/Hyundai LKAS11 message (0x340).
"""

import select
import sys
import termios
import tty
import time

BUS = 0
STEER_MAX = 1023
STEER_STEP = 300
PERIOD_S = 1 / 50  # 50Hz like openpilot


def checksum(data: bytes) -> int:
  """Simple checksum used on Hyundai LKAS11 messages."""
  return (0x100 - sum(data) % 0x100) % 0x100


def build_lkas11(torque: int, counter: int, steer_req: bool = True) -> bytes:
  """Construct an LKAS11 message with the desired steering torque.

  The layout is simplified for demonstration purposes and may need
  adjustments for specific vehicle models.
  """
  t = max(-STEER_MAX, min(STEER_MAX, torque))
  sign = 0 if t >= 0 else 1
  t = abs(t)

  data = bytearray(8)
  data[0] = (counter & 0xF) << 4
  if steer_req:
    data[0] |= 0x1

  data[1] = 0x00
  data[2] = ((t >> 8) & 0x7) | (sign << 3)
  data[3] = t & 0xFF
  data[4] = 0x00
  data[5] = 0x00
  data[6] = 0x00
  data[7] = checksum(data[:7])
  return bytes(data)


def read_key(timeout: float) -> str | None:
  """Return a pressed key or None if no key before timeout."""
  fd = sys.stdin.fileno()
  old = termios.tcgetattr(fd)
  try:
    tty.setcbreak(fd)
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
      return sys.stdin.read(1)
    return None
  finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main() -> None:
  from panda import Panda

  panda = Panda()
  counter = 0
  torque = 0
  print("Press 's' for left, 'd' for right, 'q' to quit")
  while True:
    key = read_key(PERIOD_S)
    if key == 's':
      torque = -STEER_STEP
    elif key == 'd':
      torque = STEER_STEP
    elif key == 'q':
      break
    elif key is not None:
      torque = 0

    msg = build_lkas11(torque, counter, steer_req=torque != 0)
    panda.can_send(0x340, msg, BUS)
    counter = (counter + 1) % 16
    time.sleep(PERIOD_S)


if __name__ == "__main__":
  main()
