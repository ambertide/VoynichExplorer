"""
Certain folio images are combinations of multiple
    pages of the same type. This creates an issue
    as the Voynich Explorer works on a single-folio
    basis, this program generates a JSON file that
    tells the VSIG.py single folio -> multi folio
    image name equivalents.
"""
from re import compile, Pattern, findall
from os import listdir
from json import dump
from typing import List, Dict

valid_name_pattern: Pattern = compile(r'f\d+[v|r]]\d?')


def get_folio_names(name: str) -> List[str]:
    """
    Given the name of a multi-folio image,
        breakdown the name to the names of the
        constituent folios.

    :param name: Name of the multi-folio page.
    :return: A list of names of the constituent folio image
        file names with appropriate extensions.

    >>> get_folio_names('f71v, f72r1,r2,3.jpg')
    ['f71v', 'f72r1', 'f72r2', 'f72r3']
    """
    naive_folio_names = name.split(',')  # Had all names fit the pattern, this would be adequate.
    for i, folio_name in enumerate(naive_folio_names):
        folio_name = folio_name.strip()
        if valid_name_pattern.match(folio_name):
            continue
        if folio_name.endswith('.jpg'):  # If the file does not hold an extension,
            folio_name = folio_name.replace('.jpg', '')  # Add the extension.
        if folio_name.startswith(('v', 'r')):  # Certain names only indicate v and r.
            folio_name = findall(r'(f\d+)', naive_folio_names[i - 1])[0] + folio_name  # Then use the folio name before.
        if not folio_name.startswith('f'):
            if 'v' in folio_name or 'r' in folio_name: # Catch names with forgotten f.
                folio_name = 'f' + folio_name
            else:  # If not, then these indicate r1, r2, r3, etc.
                folio_name = findall(r'(f\d+[v|r])', naive_folio_names[i - 1])[0] + folio_name
        naive_folio_names[i] = folio_name
    return naive_folio_names


def get_page_equivalents(names: List[str]) -> Dict[str, str]:
    """
    Get which singular folio page corresponds to which image
        name.

    :param path: Path containing the multi-page pictures.
    :param names: Names of the pictures.
    """
    folio_names = [get_folio_names(name) for name in names]
    multi_single_pairs = zip(names, folio_names)
    multi_single = {}  # This holds the single -> multi names.
    for m_name, folio_names in multi_single_pairs:
        multi_single.update({folio_name: m_name for folio_name in folio_names})
        # Update the general dictionary with pairs for a single
        # Multiple Folio Image name.
    return multi_single


if __name__ == '__main__':
    with open('equivalents.json', 'w') as fp:
        dump(get_page_equivalents(listdir('media_multi/')), fp)
