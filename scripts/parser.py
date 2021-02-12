import re
import sqlite3 as sql
from typing import List, Dict, Iterable, Tuple
from argparse import ArgumentParser
from os import remove
from os.path import exists
from dataclasses import dataclass

@dataclass
class Appearances:
    """
    Words and the folios they appear in a parallel list structure.
    """
    words: List[str]
    folios: List[List[str]]


def sqlite_create_tables(output_file: str) -> None:
    """
    Create the SQL tables.

    :param output_file: file to output to.
    """
    with open("setup.sql") as sql_commands:
        setup_commands = sql_commands.read()
    with sql.connect(output_file) as db:
        cursor = db.cursor()
        cursor.executescript(setup_commands)
        db.commit()


def insert_folios(folios: Iterable[str], db_cursor: sql.Cursor) -> None:
    """
    Insert the folios to the database.

    :param folios: An iterable of folios, folio names or title pages.
    :param db_cursor: An SQLite3 cursor.
    """
    db_cursor.executemany("INSERT INTO Folio(folioName) VALUES(?)",
                          list(map(lambda x: (x, ), list(folios))))


def insert_paragraphs(folios_data: Dict[str, List[str]], db_cursor: sql.Cursor) -> None:
    """
    Insert the paragraphs to the database including their relations to
        folio pages.
    
    :param folios_data: Data belonging to folios.
    :param db_file: Filename of the SQLite3 database.
    """
    for folio_name in folios_data:
        folio_data = folios_data[folio_name]
        tuples = map(lambda x: (folio_name, x), folio_data)
        # This generates folio_name, paragraph tuples
        db_cursor.executemany(f"INSERT INTO Paragraph(folioName, paragraph) VALUES(?, ?)", list(tuples))


def insert_words(words: List[str], cursor: sql.Cursor) -> None:
    """
    Insert the words into the SQLite3 database.

    :param words: Words that appear in the manuscript.
    :param cursor: Cursor for the SQLite3 database.
    """
    cursor.executemany("INSERT INTO Word(wordName) VALUES(?)", [*map(lambda x: (x, ), words), ])


def insert_appearances(appearances: Appearances, cursor: sql.Cursor) -> None:
    """
    Insert the appearances to the database.

    :param appearances: Appearances data class holds the data about the appearances.
    :param cursor: Cursor for the database.
    """
    appears = []
    for i, word in enumerate(appearances.words):
        appears.extend([*map(lambda folio: (word, folio), appearances.folios[i])])
    cursor.executemany("INSERT INTO Appears(wordName, folioName) VALUES(?, ?)", appears)


def insert_values(folios_data: Dict[str, List[str]], db_file: str, appearances) -> None:
    """
    Insert the values into the SQLite3 database file.

    :param appearances: Appearances data object.
    :param folios_data: Data containing folio number, folio content
        pairs.
    :param db_file: Name of the database file.
    """
    with sql.connect(db_file) as db:
        cursor = db.cursor()
        cursor.execute("PRAGMA synchronous = OFF")  # Remove data protections.
        cursor.execute("PRAGMA journal_mode = MEMORY")  # For faster handling.
        insert_folios(folios_data.keys(), cursor)
        db.commit()
        insert_paragraphs(folios_data, cursor)
        db.commit()
        insert_words(appearances.words, cursor)
        db.commit()
        insert_appearances(appearances, cursor)
        db.commit()


def parse_folio_num(folio_tag: str) -> str:
    """
    Parse a folio number from a folio tag.

    :param folio_tag Tag of the folio.
    :return the name of the folio.
    """
    return folio_tag.replace('<', '').replace('>', '')


def clean_contents(folio_text: str) -> List[str]:
    """
    Clean the contents of a folio.

    :param folio_text: Text of a folio.
    :return The cleaned contents of a folio.
    """
    cleaned_paragraphs = re.findall(r"((?<=>)\s*.+[\n|\w])", folio_text)  # Not all are actually paragraphs.
    return list(filter(lambda x: x != '', map(lambda x: x.strip(), cleaned_paragraphs)))


def parse_word_appearances(cleaned_contents: List[str], appearances: Appearances, folio_name) -> None:
    """
    Parse the word appearance count and append the word appearances accordingly.

    :param cleaned_contents: Contents of a folio.
    :param appearances: Appearances dataclass.
    :param folio_name: Name of the folio that is parsed.
    """
    words = ('.'.join(cleaned_contents)).split('.')
    unique_words = list(set(words))
    while len(unique_words) > 0:
        word = unique_words.pop()  # Get a word.
        try:
            word_index = appearances.words.index(word)  # Check if the word appeared in the index before.
            appearances.folios[word_index].append(folio_name)  # Denote that the word that exists
            # Also appears in this folio.
        except ValueError: # If the word does not exists.
            appearances.words.append(word)  # Add the word.
            appearances.folios.append([folio_name, ])  # And denote it appears in this folio.


def split_folios(full_text: str, appearances: Appearances) -> Dict[str, List[str]]:
    """
    Split the full text into a list of strings
        each containing text belonging to a folio.

    :param full_text: Full text of the voynich manuscript.
    :param appearances: Appearances dataclass to hold which word appears where.
    :return a list of page transliterations.
    """
    all_split = re.split(r"(<f\d+(?:v|r)\d*>)", full_text)[1:]
    folios = {}  # The cleaned and semi-parsed folios list
    for i in range(0, len(all_split), 2):
        # Clean the contents of the folio and parse them to
        # Nice lists.
        cleaned_contents = clean_contents(all_split[i+1])
        folio_name = parse_folio_num(all_split[i])
        folios[folio_name] = cleaned_contents
        parse_word_appearances(cleaned_contents, appearances, folio_name)
    return folios


if __name__ == '__main__':
    program = ArgumentParser(prog="./parser.py",
                             description="Parse the Interim Voynich Files to SQLite3 databases.")
    program.add_argument("input", help="Input file in Voynich Interim Format.")
    program.add_argument("output", help="Output file in SQLite3 format.")
    program.add_argument("--remove_old", "-r",
                         action="store_true", help="Remove the old output file with the same name if it exists.")
    arguments = program.parse_args()
    if arguments.remove_old and exists(arguments.output):
        remove(arguments.output)
    sqlite_create_tables(arguments.output)
    with open(arguments.input) as file:
        appearances = Appearances([], [])
        folios = split_folios(file.read(), appearances)
        insert_values(folios, arguments.output, appearances)

