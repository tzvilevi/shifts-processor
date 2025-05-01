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