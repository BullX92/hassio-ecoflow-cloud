from typing import Any


_MANUAL_VARINT_FIELDS = {
    6: ("f32ShowSoc", int),
    270: ("cmsMaxChgSoc", int),
    271: ("cmsMinDsgSoc", int),
    461: ("backupReverseSoc", int),
    1628: ("feedGridMode", int),
}


def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7
    raise ValueError("Incomplete protobuf varint")


def decode_stream_ac_manual_fields(pdata: bytes, params: dict[str, Any]) -> None:
    """Decode Stream AC fields missing from the generated protobuf schema."""
    pos = 0
    while pos < len(pdata):
        try:
            tag, pos = _decode_varint(pdata, pos)
        except ValueError:
            return

        field_num = tag >> 3
        wire_type = tag & 0x7

        if wire_type == 0:
            try:
                value, pos = _decode_varint(pdata, pos)
            except ValueError:
                return
            mapped = _MANUAL_VARINT_FIELDS.get(field_num)
            if mapped is not None:
                key, cast = mapped
                params[key] = cast(value)
        elif wire_type == 1:
            pos += 8
        elif wire_type == 2:
            try:
                length, pos = _decode_varint(pdata, pos)
            except ValueError:
                return
            pos += length
        elif wire_type == 5:
            pos += 4
        else:
            return
