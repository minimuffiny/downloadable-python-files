"""Validate command XML without executing its logic (Python 3.8+)."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


NAMESPACE = "https://commands.com/"


class ValidationError(ValueError):
    """The document does not satisfy the command XML contract."""


class _CommandTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValidationError("DOCTYPE declarations are not allowed")


def validate_xml(xml):
    """Validate XML text or bytes; return None or raise ValidationError.

    Names are compared exactly as parsed, including case and whitespace.
    Attribute values are never executed or rewritten.
    """
    try:
        root = ET.fromstring(xml, parser=ET.XMLParser(target=_CommandTreeBuilder()))
    except (ET.ParseError, LookupError, UnicodeError) as exc:
        raise ValidationError("Malformed XML: {}".format(exc)) from exc

    if root.tag != "{{{}}}commands".format(NAMESPACE):
        raise ValidationError("Expected <commands> in namespace {!r}".format(NAMESPACE))
    if root.attrib:
        raise ValidationError("<commands> must not have attributes")
    if root.text and root.text.strip():
        raise ValidationError("<commands> must not contain text")

    names = set()
    for index, command in enumerate(root, 1):
        location = "Command {}".format(index)
        if command.tag != "{{{}}}command".format(NAMESPACE):
            raise ValidationError("{}: unexpected element {!r}".format(location, command.tag))
        for attribute in ("name", "logic"):
            if attribute not in command.attrib:
                raise ValidationError("{}: missing {!r} attribute".format(location, attribute))
            if not command.attrib[attribute].strip():
                raise ValidationError("{}: empty {!r} attribute".format(location, attribute))
        if set(command.attrib) != {"name", "logic"}:
            raise ValidationError("{}: unexpected attribute".format(location))
        if len(command) or (command.text and command.text.strip()):
            raise ValidationError("{}: must be empty (no text or child elements)".format(location))
        if command.tail and command.tail.strip():
            raise ValidationError("{}: unexpected text after element".format(location))
        name = command.attrib["name"]
        if name in names:
            raise ValidationError("{}: duplicate command name {!r}".format(location, name))
        names.add(name)


def validate_file(path):
    """Validate a file; raise ValidationError or OSError on failure."""
    validate_xml(Path(path).read_bytes())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="commands-basic.xml")
    args = parser.parse_args(argv)
    try:
        validate_file(args.path)
    except (OSError, ValidationError) as exc:
        print("{}: {}".format(args.path, exc), file=sys.stderr)
        return 1
    print("{}: valid".format(args.path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
