from argparse import ArgumentParser
from typing import List, Optional, Dict
from os import listdir
import sqlite3 as sql
from os.path import exists
from template_commons import footer, header, explanation_word, explanation_folio
from pathlib import Path
from json import load
from warnings import warn


class MissingImageWarning(Warning):
    pass


with open('equivalents.json') as fp:
    multis = load(fp)  # Multiline equivalents.


def generate_missing_folios():
    numbers = [12, *range(59, 65), 74, 91, 92, 97, 98, 109, 110]
    missing_folios = []
    for number in numbers:
        missing_folios.extend([f"f{number}v", f"f{number}r"])
    return missing_folios


missing_folios = generate_missing_folios()
print(missing_folios)


missing_card = r"""
            <div class="card error large">
                <div class="section title"><h2>Missing Image!</h2></div>
                <div class="section explanation"><p>This image is missing! This is likely not your fault,
                    it is extremely likely that the image is not on the server, and is an issue in our end,
                    we are aware of the missing images and are trying hard to find them.</p>
                </div>
            </div>
"""

folio_image = r"""
            <div class="folio_image">
                <img class="voynich_folio_page" src="../media/portrait.jpg" alt="Image description"/>
            </div>
"""


def replace_templates(replace_dict: Dict[str, str], template: str) -> str:
    """
    Replace the placeholders on a template to create a page.

    :param replace_dict: Replacement values for placeholder -> actual value.
    :param template: Template to replace in.
    :return: The generated page.
    """
    page = template
    for placeholder in replace_dict:
        page = page.replace("{%" + placeholder + "%}", replace_dict[placeholder])
    return page


def generate_word_page(word: str, cursor: sql.Cursor, template: str) -> None:
    """
    Generate a word page for the given word, which shows
        pages it appears in, its appearance number, as well
        as its various alternate forms.

    :param word: Word to create the page for.
    :param cursor: Cursor to the database.
    :param template: Template to create the page from.
    """
    page = template.replace("{%wordName%}", word)
    appearances = cursor.execute("SELECT folioName FROM Appears WHERE wordName = ? ORDER BY appearanceID", (word,))
    folios = [appearance[0] for appearance in appearances]
    page = page.replace("{%wordAppearanceCount%}", str(len(folios)))
    folios = get_list(folios, "../folio/", ".html")
    page = page.replace("{%appearances%}", folios)
    with open(f"word/{word}.html", "w") as page_file:
        page_file.write(page)


def generate_word_pages(db_filename: str) -> None:
    """
    Given the name of the SQLite3 file containing
        data on the Voynich word appearances generate word pages.
    
    :param db_filename: The path of the SQLite3 file.
    """
    with open("templates/word.html") as template_file:
        template = template_file.read()
    template = set_template_commons(template)
    with sql.connect(db_filename) as database:
        cursor = database.cursor()
        cursor.execute("SELECT * FROM Word")
        words = cursor.fetchall()
        for word in words:
            word = word[1]
            generate_word_page(word, cursor, template)


def generate_folio_div(paragraphs: List[str]) -> str:
    """
    Generate the paragraph text with the <a> tags.

    :param paragraphs: A list of paragraphs queried from the SQLite3 file.
    :return: The string to put into the HTML.
    """
    string_ = ""
    for i, paragraph in enumerate(paragraphs):
        words = paragraph[0].split('.')
        words = [f'<a class="voynich-word" href="../word/{word}.html">{word}</a>' for word in words]
        string_ += f'<sup>{i + 1}</sup>' + ' '.join(words) + '</br>'
    return string_


def generate_folio_page(folio_name: str, folio_paragraphs: str, template: str,
                        folio_before: Optional[str], folio_after: Optional[str], do_warn = True) -> None:
    """
    Generate a folio page from a given folio name and the paragraph of the
        Folio.

    :param folio_name: Name or page number of the folio.
    :param folio_paragraphs: Paragraphs in the folio.
    :param template: HTML template file about the folio.
    """
    page = template.replace("{%folioName%}", folio_name)
    page = page.replace("{%contents%}", folio_paragraphs)
    if folio_before:
        page = page.replace("{%before%}", f'<a id="before_link" href="{folio_before}.html"><b><</b></a>')
    else:
        page = page.replace("{%before%}", "").replace('<a href="f1r.html"><<</a>', "")
    if folio_after:
        page = page.replace("{%after%}", f'<a id="after_link" href="{folio_after}.html"><b>></b></a>')
    else:
        page = page.replace("{%after%}", "").replace('<a href="f116v.html">>></a>', "")
    image_name = folio_name + '.jpg'
    if folio_name in multis:
        image_name = multis[folio_name]
    if exists(f'media/{image_name}'):
        page = page.replace("portrait.jpg", image_name)
    elif folio_name not in missing_folios:
        warn(f'No image found for {folio_name}.', MissingImageWarning)
        page = page.replace(folio_image, missing_card)  # Display an error if the image is missing.
    with open(f'folio/{folio_name}.html', 'w') as web_page:
        web_page.write(page)


def set_template_commons(template) -> str:
    """
    Irregardles of the type of the page, some things stay constant.

    :param template: Template to change
    :return: The changed template
    """
    template = template.replace("{%footer%}", footer).replace("{%header%}", header)
    return template


def generate_folio_pages(db_file):
    with open('templates/folio.html') as template_file:
        template = template_file.read()
    template = set_template_commons(template)
    with open('templates/missing_folio.html') as missing_file:
        missing_template = missing_file.read()
    missing_template = set_template_commons(missing_template)
    with sql.connect(db_file) as db:
        cursor = db.cursor()
        cursor.execute("SELECT folioName FROM Folio ORDER BY folioID;")
        folio_names = cursor.fetchall()
        for i, folio_name in enumerate(folio_names):
            cursor.execute("SELECT paragraph FROM Paragraph WHERE folioName = ? ORDER BY paragraphID", folio_name)
            folio_paragraphs = cursor.fetchall()
            paragraph_text = generate_folio_div(folio_paragraphs)
            folio_before = None if i == 0 else folio_names[i - 1][0]
            folio_after = None if i == len(folio_names) - 1 else folio_names[i + 1][0]
            if folio_name[0] in missing_folios:
                generate_folio_page(folio_name[0], paragraph_text, missing_template, folio_before, folio_after, False)
            else:
                generate_folio_page(folio_name[0], paragraph_text, template, folio_before, folio_after)


def get_list(list_: List[str], path: str = '', extension: str = '') -> str:
    """
    Get the HTML list version of the list
        in Python.

    :param list_: A python list of strings.
    :param path: Directory path prefix of the links, optional.
        If not provided, act as if the links are in the same page.
    :param extension: Extension to be appended to
        the end of the file.
    :return: the HTML version of the list.
    """
    html_list = "<ul>"
    html_list += "\n".join(['<li> <a href="' + path + element + extension + '">'
                            + element.replace(".html", "") + '</a></li>' for element in list_])
    html_list += "</ul>"
    return html_list


def generate_index_pages(db_file) -> None:
    """
    These pages are the index pages for the word/ and
        folio/ directories.

    :param db_file: Database file, of type SQLite3
    """
    with sql.connect(db_file) as db:
        cur = db.cursor()
        cur.execute('SELECT folioName FROM Folio ORDER BY folioID')
        folio_list = cur.fetchall()
    folio_list = [folio[0] + '.html' for folio in folio_list]
    words_list = listdir("word/")
    words_list = get_list(words_list)
    with open("templates/general_index.html") as template_file:
        template = template_file.read()
    template = set_template_commons(template)
    word_page = replace_templates(
        {
            "page-title": "Word",
            "list_section": words_list,
            "explanation": explanation_word
        }, template)
    with open("word/index.html", "w") as word_index:
        word_index.write(word_page)
    folio_list = get_list(folio_list)
    folio_page = replace_templates(
        {
            "page-title": "Folio",
            "list_section": folio_list,
            "explanation": explanation_folio
        }, template)
    with open("folio/index.html", "w") as folio_index:
        folio_index.write(folio_page)


if __name__ == '__main__':

    program = ArgumentParser(description="Generate a Static Webpage for Exploring the Voynich Manuscript.")
    program.add_argument("input", help="Voynich data in a SQLite3 file")
    program.add_argument("--generate_folder", "-f", action="store_true", help="Generate the necessary folders.")
    args = program.parse_args()
    if args.generate_folder:
        for path in ['folio/', 'word/']:
            Path(path).mkdir(exist_ok=True)
    generate_folio_pages(args.input)
    generate_word_pages(args.input)
    generate_index_pages(args.input)
