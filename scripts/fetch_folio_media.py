from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get
from time import sleep
from typing import Dict, List


def get_commons_page(url: str) -> str:
    """
    Get the HTML source code of the WikiMedia Commons
        page to get Voynich page media urls.

    :param url: URL of the WikiMedia Commons Page.
    :return: the HTML Source code of the page.
    """
    response = get(url)
    text = response.text
    response.close()
    return text


def get_image(name: str, image_link: str) -> None:
    """
    Get the Image page from the WikiMedia commons and download
        the images to the media/ folder with proper names.

    :param name: Name of the folio page.
    :param image_link: Link to the WikiMedia Commons page.
    """
    response = get(image_link)
    html_body = response.text
    response.close()
    soup = BeautifulSoup(html_body, 'html.parser')
    full_image_box = soup.find("div", class_='fullImageLink')
    link = full_image_box.a['href']
    image = get(link)
    sleep(0.05)
    with open(f"media/{name}.jpg", "wb+") as media_file:
        media_file.write(image.content)
    image.close()


def get_folio_urls(html_source: str) -> Dict[str, str]:
    """
    Get the image URL's for each folio page.

    :param html_source: HTML Source code of the WikiMedia
        Commons catalogue page containing links to each
        and every folio page.
    :return: The URLs to each folio media.
    """
    links = {}
    soup = BeautifulSoup(html_source, 'html.parser')
    galleryboxes: List[Tag] = soup.find_all("li", class_="gallerybox")  # These hold both the title and the link.
    for box in galleryboxes:
        text_box = box.find("div", class_="gallerytext")
        try:
            name = text_box.p.text
        except AttributeError:
            continue
        url = box.find("a", class_="image")
        links[name.replace('\n', '')] = "https://commons.wikimedia.org" + url['href']
    return links


if __name__ == '__main__':
    image_urls = get_folio_urls(get_commons_page('https://commons.wikimedia.org/wiki/Voynich_manuscript'))
    for folio_name in image_urls:
        sleep(1)
        get_image(folio_name, image_urls[folio_name])

