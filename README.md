# downloadable-python-files
a bunch of downloadable python files using request to get these files

## Validating command XML

Requires Python 3.8+ and only the standard library. From the repository directory:

```sh
python validate_commands.py commands-basic.xml
python -m unittest -v
```

The path defaults to `commands-basic.xml` in the current directory. The validator
prints `PATH: valid` and exits 0 on success; invalid XML or an unreadable file
produces a diagnostic on stderr and exits 1 (CLI usage errors exit 2).

Validation contract:

- The root is `<commands>` in the exact namespace `https://commands.com/`.
  Default namespaces and prefixes are equivalent; missing or different namespaces
  are rejected, including namespace resets on child elements.
- The root contains zero or more direct `<command>` children in that namespace.
  Each has exactly two unqualified attributes, `name` and `logic`, both nonblank
  after checking whitespace. Values are preserved, not trimmed or rewritten.
- Names must be unique, comparing XML-decoded values exactly (case-sensitive,
  including surrounding whitespace). Logic is opaque text: semicolons and other
  shell syntax are accepted and **never executed** or checked as shell commands.
- Commands are empty: both self-closing syntax and explicit closing tags work.
  Unexpected elements, attributes, nested elements, and non-whitespace text are
  rejected. Formatting whitespace, XML comments, and processing instructions are
  ignored. Normal XML escaping applies; DOCTYPE declarations are rejected.

The existing `commands-basic.xml` syntax remains valid. For Python callers,
`validate_xml(text_or_bytes)` and `validate_file(path)` return `None` on success
and raise `ValidationError` on invalid content; file I/O errors raise `OSError`.
