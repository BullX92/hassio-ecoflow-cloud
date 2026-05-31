from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "custom_components"
    / "ecoflow_cloud"
    / "devices"
    / "internal"
    / "stream_ac_manual_fields.py"
)


def load_manual_fields_module():
    spec = importlib.util.spec_from_file_location("stream_ac_manual_fields", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def encode_varint(value: int) -> bytes:
    data = bytearray()
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            data.append(0x80 | bits)
        else:
            data.append(bits)
            return bytes(data)


def encode_varint_field(field_num: int, value: int) -> bytes:
    return encode_varint(field_num << 3) + encode_varint(value)


class StreamACManualFieldsTest(unittest.TestCase):
    def setUp(self):
        self.manual_fields = load_manual_fields_module()

    def test_decodes_known_top_level_varint_fields(self):
        params = {}
        pdata = b"".join(
            [
                encode_varint_field(6, 47),
                encode_varint_field(270, 100),
                encode_varint_field(271, 12),
                encode_varint_field(461, 20),
                encode_varint_field(1628, 2),
            ]
        )

        self.manual_fields.decode_stream_ac_manual_fields(pdata, params)

        self.assertEqual(
            params,
            {
                "f32ShowSoc": 47,
                "cmsMaxChgSoc": 100,
                "cmsMinDsgSoc": 12,
                "backupReverseSoc": 20,
                "feedGridMode": 2,
            },
        )

    def test_skips_length_delimited_unknown_fields(self):
        params = {}
        unknown_bytes_field = encode_varint((584 << 3) | 2) + encode_varint(3) + b"abc"
        pdata = unknown_bytes_field + encode_varint_field(461, 30)

        self.manual_fields.decode_stream_ac_manual_fields(pdata, params)

        self.assertEqual(params, {"backupReverseSoc": 30})


if __name__ == "__main__":
    unittest.main()
