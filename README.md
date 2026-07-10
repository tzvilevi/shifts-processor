# shifts-processor

This project solves a shift scheduling problem using Google's OR-Tools library. The solution assigns employees to shifts (morning, afternoon, evening) for multiple days while ensuring that no employee works more than one shift per day.

## Requirements

- Python 3.7+
- OR-Tools library

## Installation

Install the required library using pip:

```bash
pip install ortools
```

## Usage

Run the script to generate a schedule:

```bash
python shift_scheduler.py
```

## Example Output

For a set of employees and days, the script will output a valid schedule like this:

```
Monday:
  morning: Alice
  afternoon: Bob
  evening: Charlie
Tuesday:
  morning: Bob
  afternoon: Charlie
  evening: Alice
...
```

## Remove a PDF Password

The project also includes a small tool for removing the password from a
password-protected PDF. You supply a PDF **and the password you already know**,
and it returns an identical copy without the password. It does not guess or
crack unknown passwords.

### Command line

```bash
python pdf_password_remover.py protected.pdf -p "your-password"
# writes protected-unlocked.pdf
```

Options:

- `-p`, `--password` (required): the password that opens the PDF.
- `-o`, `--output`: where to write the unlocked PDF (default: `<input>-unlocked.pdf`).

### Web interface

Run the Flask service and open `http://localhost:5000/pdf` in a browser to
upload a PDF, enter its password, and download the unlocked file:

```bash
python shift_scheduler_service.py
```

You can also call the endpoint directly:

```bash
curl -X POST http://localhost:5000/pdf/remove-password \
  -F "file=@protected.pdf" \
  -F "password=your-password" \
  -o unlocked.pdf
```