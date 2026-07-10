"""Remove the password from a password-protected PDF.

This module decrypts a PDF using a password that the user already knows and
writes out an unlocked copy. It does NOT attempt to guess or crack unknown
passwords - the correct password must be supplied.
"""

import argparse
import io
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError, FileNotDecryptedError


class WrongPasswordError(Exception):
    """Raised when the supplied password does not open the PDF."""


class NotEncryptedError(Exception):
    """Raised when the PDF is not password protected."""


def remove_password(pdf_bytes: bytes, password: str) -> bytes:
    """Return an unlocked copy of ``pdf_bytes`` decrypted with ``password``.

    Args:
        pdf_bytes: Raw bytes of the (encrypted) PDF file.
        password: The password that opens the PDF.

    Returns:
        Raw bytes of a new PDF with no password.

    Raises:
        NotEncryptedError: The PDF has no password to remove.
        WrongPasswordError: The password did not open the PDF.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except PdfReadError as exc:
        raise ValueError(f"Not a valid PDF file: {exc}") from exc

    if not reader.is_encrypted:
        raise NotEncryptedError("The PDF is not password protected.")

    # PdfReader.decrypt returns a value indicating whether the password worked.
    try:
        result = reader.decrypt(password)
    except (FileNotDecryptedError, NotImplementedError) as exc:
        raise WrongPasswordError(str(exc)) from exc

    if result == 0:  # PasswordType.NOT_DECRYPTED
        raise WrongPasswordError("The supplied password is incorrect.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # Copy document metadata if present.
    if reader.metadata is not None:
        writer.add_metadata(reader.metadata)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove the password from a password-protected PDF."
    )
    parser.add_argument("input", help="Path to the password-protected PDF.")
    parser.add_argument(
        "-p", "--password", required=True, help="Password that opens the PDF."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Where to write the unlocked PDF (default: <input>-unlocked.pdf).",
    )
    args = parser.parse_args(argv)

    output_path = args.output
    if output_path is None:
        if args.input.lower().endswith(".pdf"):
            output_path = args.input[:-4] + "-unlocked.pdf"
        else:
            output_path = args.input + "-unlocked.pdf"

    try:
        with open(args.input, "rb") as fh:
            pdf_bytes = fh.read()
    except OSError as exc:
        print(f"Could not read '{args.input}': {exc}", file=sys.stderr)
        return 1

    try:
        unlocked = remove_password(pdf_bytes, args.password)
    except NotEncryptedError:
        print("The PDF is not password protected - nothing to remove.", file=sys.stderr)
        return 2
    except WrongPasswordError:
        print("The supplied password is incorrect.", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    try:
        with open(output_path, "wb") as fh:
            fh.write(unlocked)
    except OSError as exc:
        print(f"Could not write '{output_path}': {exc}", file=sys.stderr)
        return 1

    print(f"Unlocked PDF written to '{output_path}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
