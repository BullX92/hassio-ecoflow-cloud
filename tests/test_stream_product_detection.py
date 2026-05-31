from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "custom_components" / "ecoflow_cloud" / "devices" / "product_names.py"


def load_product_names_module():
    spec = importlib.util.spec_from_file_location("product_names", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StreamProductDetectionTest(unittest.TestCase):
    def setUp(self):
        self.product_names = load_product_names_module()
        self.known_products = {
            "PowerStream",
            "Smart Meter",
            "Stream AC",
            "Stream PRO",
            "Stream Ultra",
            "Stream Microinverter",
        }

    def test_canonicalizes_stream_ac_pro_to_stream_ac(self):
        self.assertEqual(
            self.product_names.canonical_product_name("Stream AC Pro", self.known_products),
            "Stream AC",
        )

    def test_keeps_stream_microinverter_distinct(self):
        self.assertEqual(
            self.product_names.canonical_product_name("Stream Microinverter", self.known_products),
            "Stream Microinverter",
        )

    def test_canonicalizes_other_stream_battery_variants(self):
        self.assertEqual(
            self.product_names.canonical_product_name("Stream Max", self.known_products),
            "Stream AC",
        )

    def test_infers_stream_battery_from_product_type_58(self):
        self.assertEqual(
            self.product_names.infer_public_product_name(
                {"sn": "BK31...", "deviceName": "Stream AC Pro", "productType": 58},
                self.known_products,
            ),
            "Stream AC",
        )

    def test_infers_stream_battery_from_undefined_name_and_device_name(self):
        self.assertEqual(
            self.product_names.infer_public_product_name(
                {"sn": "BK31...", "deviceName": "Stream AC Pro", "productName": "undefined"},
                self.known_products,
            ),
            "Stream AC",
        )

    def test_preserves_non_stream_product_names(self):
        self.assertEqual(
            self.product_names.infer_public_product_name(
                {"sn": "SM...", "deviceName": "Smart Meter-1234", "productName": "Smart Meter"},
                self.known_products,
            ),
            "Smart Meter",
        )


if __name__ == "__main__":
    unittest.main()
