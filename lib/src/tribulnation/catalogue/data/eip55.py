"""EIP-55 address checksumming, with a self-contained Keccak-256.

Keccak-256 is not `hashlib.sha3_256`: Ethereum uses the original Keccak padding
(`0x01`) rather than NIST SHA-3's (`0x06`), so the stdlib cannot be used here.
The implementation below is written out in full to keep this package's runtime
dependencies at `pydantic` and `lazy-loader` -- pulling in a crypto library so
that a data repository can validate its own address casing is a poor trade.

References:
  - [EIP-55](https://eips.ethereum.org/EIPS/eip-55)
"""
import re
from typing_extensions import Final

_ADDRESS: Final = re.compile(r'^0x[0-9a-fA-F]{40}$')
_ROUND_CONSTANTS: Final = [
  0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
  0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
  0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
  0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
  0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
  0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_ROTATIONS: Final = [
  [0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61],
  [28, 55, 25, 21, 56], [27, 20, 39, 8, 14],
]
_MASK: Final = (1 << 64) - 1

def _rotl(value: int, shift: int) -> int:
  """Rotate a 64-bit lane left."""
  return ((value << shift) | (value >> (64 - shift))) & _MASK

def _permute(lanes: list[list[int]]) -> None:
  """Apply the 24-round Keccak-f[1600] permutation in place."""
  for rc in _ROUND_CONSTANTS:
    parity = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
    for x in range(5):
      d = parity[(x - 1) % 5] ^ _rotl(parity[(x + 1) % 5], 1)
      for y in range(5):
        lanes[x][y] ^= d
    rotated = [[0] * 5 for _ in range(5)]
    for x in range(5):
      for y in range(5):
        rotated[y][(2 * x + 3 * y) % 5] = _rotl(lanes[x][y], _ROTATIONS[x][y])
    for x in range(5):
      for y in range(5):
        lanes[x][y] = rotated[x][y] ^ ((~rotated[(x + 1) % 5][y]) & rotated[(x + 2) % 5][y] & _MASK)
    lanes[0][0] ^= rc

def keccak256(data: bytes) -> bytes:
  """Keccak-256 digest of `data`, as used by Ethereum."""
  rate = 136
  padded = bytearray(data)
  padded.append(0x01)
  while len(padded) % rate != 0:
    padded.append(0x00)
  padded[-1] |= 0x80
  lanes = [[0] * 5 for _ in range(5)]
  for offset in range(0, len(padded), rate):
    block = padded[offset:offset + rate]
    for i in range(rate // 8):
      lane = int.from_bytes(block[i * 8:(i + 1) * 8], 'little')
      lanes[i % 5][i // 5] ^= lane
    _permute(lanes)
  out = bytearray()
  for i in range(4):
    out += lanes[i % 5][i // 5].to_bytes(8, 'little')
  return bytes(out)

def checksum(address: str) -> str:
  """Return `address` in its EIP-55 checksummed form.

  Args:
    address: A `0x`-prefixed 20-byte hex address, in any casing.

  Raises:
    ValueError: The string is not a well-formed hex address.
  """
  if not _ADDRESS.match(address):
    raise ValueError(f'not a 20-byte hex address: {address!r}')
  body = address[2:].lower()
  digest = keccak256(body.encode()).hex()
  return '0x' + ''.join(c.upper() if c.isalpha() and int(digest[i], 16) >= 8 else c for i, c in enumerate(body))

def is_checksummed(address: str) -> bool:
  """Whether `address` is already in its exact EIP-55 checksummed form."""
  try:
    return checksum(address) == address
  except ValueError:
    return False
