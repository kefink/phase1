import pytest
from new_structure.security.xml_security import secure_parse_xml, XXEError


def test_secure_parse_rejects_doctype_entity():
    malicious = """<?xml version='1.0'?>
<!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
<foo>&xxe;</foo>"""
    with pytest.raises(XXEError):
        secure_parse_xml(malicious)


def test_secure_parse_allows_simple_xml():
    xml = "<root><child value='1'/></root>"
    root = secure_parse_xml(xml)
    assert root.tag == 'root'
    assert root.find('child').attrib['value'] == '1'


def test_secure_parse_size_limit():
    big = "<r>" + ("a" * (600 * 1024)) + "</r>"
    with pytest.raises(XXEError):
        secure_parse_xml(big)
