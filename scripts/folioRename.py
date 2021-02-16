from re import compile
from os import listdir, rename
from os.path import join


def rename_files(path: str) -> None:
    """
    Due to a weird quirk in WikiMedia Commons
        some folios do not have the f prefix
        before their name. This adds that to
        their name.

    :param path: Directory of the image files.
    """
    pattern = compile(r'\b(?<!=f)\d+[v|r].jpg')
    file_names = listdir(path)  # Get the full image list.
    wrong_names = filter(lambda name: pattern.match(name), file_names)  # Offending file names.
    # Get a dictionary of wrong paths and the paths when corrected.
    correction_dict = {join(path, name): join(path, 'f' + name) for name in wrong_names}
    for source, destination in correction_dict.items():
        rename(source, destination)


if __name__ == '__main__':
    rename_files('../media')
