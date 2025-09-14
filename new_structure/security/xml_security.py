"""Secure XML parsing utilities to mitigate XXE (OWASP A4).

Provides a single entry point `secure_parse_xml` that:
 - Rejects overly large payloads (basic size gate)
 - Uses defusedxml if available for hardened parsers
 - Disables DTD / external entity expansion explicitly
 - Returns a minimal ElementTree-like root or raises ValueError

Currently the application does not parse XML, but this module is
introduced proactively to enforce safe defaults for any future
XML integrations (imports, third-party payloads, etc.).
"""
from __future__ import annotations
import io
from typing import Union

_DEFUSED_ET = None
try:
    from defusedxml import ElementTree as _DEFUSED_ET  # type: ignore
except Exception:  # pragma: no cover
    _DEFUSED_ET = None

import xml.etree.ElementTree as _STD_ET  # fallback (wrapped safely)

MAX_XML_BYTES = 512 * 1024  # 512 KB ceiling for defensive control


class XXEError(ValueError):
    """Raised when XML is considered unsafe or invalid under security policy."""


def _reject_doctype(xml_text: str) -> None:
    lowered = xml_text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered or "<![" in lowered:
        # Block DTD / ENTITY / conditional sections entirely
        raise XXEError("XML contains disallowed DOCTYPE/ENTITY declarations")


def secure_parse_xml(source: Union[str, bytes, io.BytesIO, io.StringIO]):
    """Parse XML safely, preventing XXE and related attacks.

    Args:
        source: XML content as str/bytes or a file-like object.

    Returns:
        Parsed XML root element.

    Raises:
        XXEError / ValueError on unsafe or invalid content.
    """
    if isinstance(source, (io.BytesIO, io.StringIO)):
        data = source.getvalue()
    else:
        data = source

    if isinstance(data, bytes):
        if len(data) > MAX_XML_BYTES:
            raise XXEError("XML payload exceeds size limit")
        try:
            text = data.decode('utf-8', errors='strict')
        except UnicodeDecodeError as e:
            raise XXEError(f"Invalid XML encoding: {e}") from e
    else:
        if len(data) > MAX_XML_BYTES:
            raise XXEError("XML payload exceeds size limit")
        text = data

    _reject_doctype(text)

    # Try hardened defusedxml first
    if _DEFUSED_ET is not None:
        try:
            return _DEFUSED_ET.fromstring(text)
        except Exception as e:  # defusedxml raises specific security exceptions
            raise XXEError(f"XML parse rejected: {e}") from e

    # Fallback to stdlib with pre-scan + no custom resolvers (we already blocked DTD)
    try:
        return _STD_ET.fromstring(text)
    except Exception as e:  # pragma: no cover - generic fallback
        raise XXEError(f"XML parse failed: {e}") from e


__all__ = ["secure_parse_xml", "XXEError"]
