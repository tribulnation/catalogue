"""Correlation keys: the strings both sides of one cross-chain movement carry.

A protocol entry (`data/protocols/<id>.json`) defines its key template and typed fields.
Formatting and parsing both go through the canonical text form of each field type, so
two independent writers of the same movement always produce the same string.
"""

import re
from typing_extensions import Collection, Mapping, get_args

from .schema import Correlation, CorrelationFieldType, Protocol

FIELD_TYPES: tuple[CorrelationFieldType, ...] = get_args(CorrelationFieldType)
FIELD_NAME = re.compile(r'^[a-z][a-z0-9_]*$')
LITERAL = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
PLACEHOLDER = re.compile(r'^\{([^{}]*)\}$')
_INT = re.compile(r'^-?(?:0|[1-9][0-9]*)$')
_UINT = re.compile(r'^(?:0|[1-9][0-9]*)$')
_HEX = re.compile(r'^0x[0-9a-f]+$')
_STRING = re.compile(r'^[^:\s]+$')

Segment = tuple[str, str | None]
"""`(literal, None)` for a literal segment, `('', field)` for a placeholder"""


class CorrelationError(ValueError):
  """A correlation key or its fields do not match any catalogue protocol entry."""


def template_segments(correlation: Correlation) -> list[Segment]:
  """Split a key template into its segments after the namespace.

  Raises:
    CorrelationError: A segment is neither a `{field}` placeholder nor a kebab-case literal.
  """
  _, *rest = correlation['key'].split(':')
  segments: list[Segment] = []
  for part in rest:
    if (m := PLACEHOLDER.fullmatch(part)) is not None:
      segments.append(('', m.group(1)))
    elif LITERAL.fullmatch(part):
      segments.append((part, None))
    else:
      raise CorrelationError(
        f'Template segment "{part}" is neither a {{field}} placeholder nor a kebab-case literal'
      )
  return segments


def template_errors(id: str, protocol: Protocol) -> list[str]:
  """Problems with a protocol's correlation template, as messages (empty when valid)."""
  correlation = protocol['correlation']
  namespace = correlation['key'].split(':')[0]
  errors: list[str] = []
  if namespace != id:
    errors.append(f'key "{correlation["key"]}" must start with the protocol id "{id}:"')
  try:
    segments = template_segments(correlation)
  except CorrelationError as e:
    return [*errors, str(e)]
  placeholders = [field for _, field in segments if field is not None]
  if not placeholders:
    errors.append(f'key "{correlation["key"]}" has no placeholders')
  if len(set(placeholders)) != len(placeholders):
    errors.append(f'key "{correlation["key"]}" repeats a placeholder')
  if set(placeholders) != set(correlation['fields']):
    errors.append(
      f'key placeholders {sorted(set(placeholders))} differ from fields {sorted(correlation["fields"])}'
    )
  for name, type in correlation['fields'].items():
    if not FIELD_NAME.fullmatch(name):
      errors.append(f'field "{name}" must be snake_case')
    if type not in FIELD_TYPES:
      errors.append(
        f'field "{name}" has unknown type "{type}". Must be one of {FIELD_TYPES}'
      )
  return errors


def canonical(
  value: object, type: CorrelationFieldType, *, networks: Collection[str]
) -> str:
  """The canonical text of a field value.

  Args:
    value: `int` for `int`/`uint`, `str` or `bytes` for `hex`, `str` otherwise. A
      base-10 `str` is also accepted for `int`/`uint`, and a `hex` string in any case.
    type: The field's declared type.
    networks: Catalogue platform ids, for the `network` type.

  Raises:
    CorrelationError: The value is not of the declared type.
  """
  if type in ('int', 'uint'):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
      raise CorrelationError(f'expected {type}, got {value!r}')
    text = str(value)
    if not _INT.fullmatch(text) or (type == 'uint' and not _UINT.fullmatch(text)):
      raise CorrelationError(f'expected {type}, got {value!r}')
    return text
  if type == 'hex':
    if isinstance(value, bytes):
      return '0x' + value.hex()
    if isinstance(value, str) and _HEX.fullmatch(text := value.lower()):
      return text
    raise CorrelationError(f'expected 0x-prefixed hex, got {value!r}')
  if not isinstance(value, str) or not _STRING.fullmatch(value):
    raise CorrelationError(f'expected {type} without ":" or whitespace, got {value!r}')
  if type == 'network' and value not in networks:
    raise CorrelationError(f'unknown catalogue network "{value}"')
  return value


def format_key(
  id: str,
  protocol: Protocol,
  fields: Mapping[str, object],
  *,
  networks: Collection[str],
) -> str:
  """Build the correlation key of `protocol` from its field values.

  Raises:
    CorrelationError: Missing, extra or mistyped fields.
  """
  declared = protocol['correlation']['fields']
  if missing := sorted(set(declared) - set(fields)):
    raise CorrelationError(f'"{id}" key is missing fields {missing}')
  if extra := sorted(set(fields) - set(declared)):
    raise CorrelationError(f'"{id}" key has unknown fields {extra}')
  parts = [id]
  for literal, field in template_segments(protocol['correlation']):
    if field is None:
      parts.append(literal)
    else:
      try:
        parts.append(canonical(fields[field], declared[field], networks=networks))
      except CorrelationError as e:
        raise CorrelationError(f'"{id}" field "{field}": {e}') from None
  return ':'.join(parts)


def parse_key(
  key: str, protocols: Mapping[str, Protocol], *, networks: Collection[str]
) -> tuple[str, dict[str, int | str]]:
  """Split a correlation key into its protocol id and field values (`int` for `int`/`uint` fields, `str` otherwise).

  Raises:
    CorrelationError: Unknown namespace, wrong segment count, a literal mismatch, or a
      field value not in canonical form.
  """
  id, *parts = key.split(':')
  protocol = protocols.get(id)
  if protocol is None:
    raise CorrelationError(f'Unknown correlation namespace "{id}" in "{key}"')
  segments = template_segments(protocol['correlation'])
  if len(parts) != len(segments):
    raise CorrelationError(
      f'"{key}" does not match template "{protocol["correlation"]["key"]}"'
    )
  declared = protocol['correlation']['fields']
  fields: dict[str, int | str] = {}
  for part, (literal, field) in zip(parts, segments):
    if field is None:
      if part != literal:
        raise CorrelationError(
          f'"{key}" does not match template "{protocol["correlation"]["key"]}"'
        )
      continue
    try:
      text = canonical(part, declared[field], networks=networks)
    except CorrelationError as e:
      raise CorrelationError(f'"{key}" field "{field}": {e}') from None
    if text != part:
      raise CorrelationError(
        f'"{key}" field "{field}" is not canonical; expected "{text}"'
      )
    fields[field] = int(text) if declared[field] in ('int', 'uint') else text
  return id, fields
