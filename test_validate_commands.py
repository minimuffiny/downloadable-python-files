"""Run with: python -m unittest -v"""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from validate_commands import NAMESPACE, ValidationError, main, validate_file, validate_xml


def document(body="", namespace=NAMESPACE):
    return '<commands xmlns="{}">{}</commands>'.format(namespace, body)


class CommandValidationTests(unittest.TestCase):
    def test_repository_sample(self):
        validate_file(Path(__file__).with_name("commands-basic.xml"))

    def test_valid_forms(self):
        for body in (
            "",  # An empty collection is valid.
            '<command name="prank" logic="echo hahaha"/>',
            '<command name="gong" logic="echo bell; mkdir bell"></command>',
            '<command name="a" logic="echo &quot;x&quot; &amp; echo y"/>',
            '<!-- comment --><?note ignored?><command name="a" logic="x"/>',
            '<command name="a" logic="x"/><command name="A" logic="x"/>',
            '<command name="a" logic="x"/><command name=" a " logic="x"/>',
        ):
            with self.subTest(body=body):
                self.assertIsNone(validate_xml(document(body)))

    def test_malformed_xml(self):
        for xml in ("", "<commands>", "<a/><b/>", b'\xff',
                    b'<?xml version="1.0" encoding="unknown-codec"?><commands/>',
                    document('<command name="a" logic="x"></commands>'),
                    document('<command name="a" logic="x & y"/>'),
                    document('<command name="a" name="b" logic="x"/>')):
            with self.subTest(xml=xml):
                with self.assertRaisesRegex(ValidationError, "Malformed XML"):
                    validate_xml(xml)

    def test_missing_attributes(self):
        for attributes in ('logic="x"', 'name="a"', ''):
            with self.subTest(attributes=attributes):
                with self.assertRaisesRegex(ValidationError, "missing"):
                    validate_xml(document('<command {}/>'.format(attributes)))

    def test_empty_attributes(self):
        for attribute in ("name", "logic"):
            for value in ("", " ", "&#9;&#10;&#13;"):
                attrs = {"name": "a", "logic": "x", attribute: value}
                with self.subTest(attribute=attribute, value=value):
                    with self.assertRaisesRegex(ValidationError, "empty"):
                        validate_xml(document('<command name="{name}" logic="{logic}"/>'.format(**attrs)))

    def test_duplicate_names(self):
        for second_name in ("a", "&#97;"):
            with self.subTest(second_name=second_name):
                with self.assertRaisesRegex(ValidationError, "duplicate command name"):
                    validate_xml(document('<command name="a" logic="x"/>'
                                          '<command name="{}" logic="y"/>'.format(second_name)))

    def test_namespace_prefix_is_irrelevant(self):
        validate_xml('<c:commands xmlns:c="{}"><c:command name="a" logic="x"/></c:commands>'.format(NAMESPACE))

    def test_invalid_namespaces(self):
        for xml in (
            '<commands><command name="a" logic="x"/></commands>',
            document(namespace="https://wrong.example/"),
            document(namespace="https://commands.com"),
            document('<command xmlns="" name="a" logic="x"/>'),
            document('<x:command xmlns:x="urn:other" name="a" logic="x"/>'),
            document('<command xmlns:x="urn:other" x:name="a" logic="x"/>'),
        ):
            with self.subTest(xml=xml):
                with self.assertRaises(ValidationError):
                    validate_xml(xml)

    def test_unexpected_structure(self):
        for xml in (
            '<other xmlns="{}"/>'.format(NAMESPACE),
            document('<other/>'),
            document('<command name="a" logic="x"><other/></command>'),
            document('<commands/>'),
            document('unexpected'),
            document('<command name="a" logic="x">unexpected</command>'),
            document('<command name="a" logic="x"/>unexpected'),
            document('<command name="a" logic="x" extra="y"/>'),
            '<commands xmlns="{}" extra="y"/>'.format(NAMESPACE),
        ):
            with self.subTest(xml=xml):
                with self.assertRaises(ValidationError):
                    validate_xml(xml)

    def test_doctype_rejected(self):
        with self.assertRaisesRegex(ValidationError, "DOCTYPE"):
            validate_xml('<!DOCTYPE commands [<!ENTITY x "hello">]>' +
                         document('<command name="a" logic="&x;"/>'))

    def test_declared_encoding(self):
        validate_xml(('<?xml version="1.0" encoding="iso-8859-1"?>' +
                      document('<command name="café" logic="x"/>')).encode("iso-8859-1"))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "commands.xml"
            for contents, expected in ((document(), 0), ("<broken>", 1)):
                path.write_text(contents, encoding="utf-8")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(main([str(path)]), expected)
                self.assertTrue(out.getvalue() if expected == 0 else err.getvalue())
                self.assertFalse(err.getvalue() if expected == 0 else out.getvalue())
            path.unlink()
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main([str(path)]), 1)
            self.assertIn(str(path), err.getvalue())


if __name__ == "__main__":
    unittest.main()
