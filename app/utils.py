import csv
import sys


def increase_csv_field_size_limit():
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 10)


def split_str(text: str, delimiter: str = " ") -> list[str]:
    current_word = ""
    split_output = []

    for character in text.lstrip() + delimiter:
        if character != delimiter:
            current_word += character
        else:
            split_output.append(current_word)
            current_word = ""

    return split_output
