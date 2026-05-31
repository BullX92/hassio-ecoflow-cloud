from collections.abc import Iterable, Mapping
from typing import Any


_EMPTY_PRODUCT_NAMES = {"", "undefined", "null", "none"}
_STREAM_PRODUCT_TYPE = 58
_STREAM_PRODUCT_DETAIL = 5


def _as_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.casefold() in _EMPTY_PRODUCT_NAMES:
        return None
    return text


def _as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _known_product_names(known_products: Iterable[str]) -> list[str]:
    return [name for name in known_products if _as_nonempty_str(name)]


def _case_insensitive_match(product_name: str, known_products: Iterable[str]) -> str | None:
    product_name_cf = product_name.casefold()
    for known_product in _known_product_names(known_products):
        if known_product.casefold() == product_name_cf:
            return known_product
    return None


def _stream_battery_product_name(known_products: Iterable[str]) -> str:
    for preferred in ("Stream Battery", "Stream AC", "Stream Ultra", "Stream PRO"):
        if preferred in known_products:
            return preferred
    return "Stream AC"


def canonical_product_name(product_name: str, known_products: Iterable[str]) -> str:
    """Normalize EcoFlow product-name variants to a device registry key."""
    name = _as_nonempty_str(product_name)
    if name is None:
        return "undefined"

    exact_match = _case_insensitive_match(name, known_products)
    if exact_match is not None:
        return exact_match

    lowered = name.casefold()
    if lowered.startswith("stream"):
        if "microinverter" in lowered:
            return _case_insensitive_match("Stream Microinverter", known_products) or name
        return _stream_battery_product_name(known_products)

    return name


def _get_first_int(device: Mapping[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        if key in device:
            candidate = _as_int(device.get(key))
            if candidate is not None:
                return candidate

    for container_key in ("productInfo", "product", "productInfoVo"):
        container = device.get(container_key)
        if not isinstance(container, Mapping):
            continue
        for key in keys:
            if key in container:
                candidate = _as_int(container.get(key))
                if candidate is not None:
                    return candidate

    return None


def infer_public_product_name(device: Mapping[str, Any], known_products: Iterable[str]) -> str:
    """Infer the public API device type from inconsistent EcoFlow metadata."""
    product_type = _get_first_int(device, ("productType", "productTypeId"))
    product_detail = _get_first_int(device, ("productDetail", "productDetailId"))
    if product_type == _STREAM_PRODUCT_TYPE or (product_type is None and product_detail == _STREAM_PRODUCT_DETAIL):
        return _stream_battery_product_name(known_products)

    product_name = _as_nonempty_str(device.get("productName"))
    if product_name is not None:
        return canonical_product_name(product_name, known_products)

    device_name = _as_nonempty_str(device.get("deviceName")) or ""
    for known_product in sorted(_known_product_names(known_products), key=len, reverse=True):
        if device_name.casefold().startswith(known_product.casefold()):
            return canonical_product_name(known_product, known_products)

    if device_name.casefold().startswith("stream"):
        return _stream_battery_product_name(known_products)

    return "undefined"
