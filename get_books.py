import argparse
from datetime import datetime
import json
import os
import re
import time
from urllib.request import urlopen
from urllib.error import HTTPError
import bs4
import pandas as pd
from get_greads_links import time_took

@time_took
def get_all_lists(soup):
    lists = []
    list_count_dict = {}

    if soup.find('a', text='More lists with this book...'):

        lists_url = soup.find('a', text='More lists with this book...')['href']

        source = urlopen('https://www.goodreads.com' + lists_url)
        soup = bs4.BeautifulSoup(source, 'lxml')
        lists += [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'cell'})]

        i = 0
        while soup.find('a', {'class': 'next_page'}) and i <= 10:
            time.sleep(2)
            next_url = 'https://www.goodreads.com' + soup.find('a', {'class': 'next_page'})['href']
            source = urlopen(next_url)
            soup = bs4.BeautifulSoup(source, 'lxml')

            lists += [node.text for node in soup.find_all('div', {'class': 'cell'})]
            i += 1

        # Format lists text.
        for _list in lists:
            # _list_name = ' '.join(_list.split()[:-8])
            # _list_rank = int(_list.split()[-8][:-2]) 
            # _num_books_on_list = int(_list.split()[-5].replace(',', ''))
            # list_count_dict[_list_name] = _list_rank / float(_num_books_on_list)     # TODO: switch this back to raw counts
            _list_name = _list.split()[:-2][0]
            _list_count = int(_list.split()[-2].replace(',', ''))
            list_count_dict[_list_name] = _list_count

    return list_count_dict


@time_took
def get_shelves(soup):
    shelf_count_dict = {}

    if soup.find('a', text='See top shelves…'):

        # Find shelves text.
        shelves_url = soup.find('a', text='See top shelves…')['href']
        source = urlopen('https://www.goodreads.com' + shelves_url)
        soup = bs4.BeautifulSoup(source, 'lxml')
        shelves = [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'shelfStat'})]

        # Format shelves text.
        shelf_count_dict = {}
        for _shelf in shelves:
            _shelf_name = _shelf.split()[:-2][0]
            _shelf_count = int(_shelf.split()[-2].replace(',', ''))
            shelf_count_dict[_shelf_name] = _shelf_count

    return shelf_count_dict


@time_took
def get_genres(soup):
    genres = []
    for node in soup.find_all('div', {'class': 'left'}):
        current_genres = node.find_all('a', {'class': 'actionLinkLite bookPageGenreLink'})
        current_genre = ' > '.join([g.text for g in current_genres])
        if current_genre.strip():
            genres.append(current_genre)
    return genres


@time_took
def get_series_name(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_name = re.search(r'\((.*?)\)', series.text).group(1)
        return series_name
    else:
        return ""


@time_took
def get_series_uri(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_uri = series.get("href")
        return series_uri
    else:
        return ""


@time_took
def get_isbn(soup):
    try:
        isbn = re.findall(r'nisbn: [0-9]{10}', str(soup))[0].split()[1]
        return isbn
    except:
        return "isbn not found"


@time_took
def get_isbn13(soup):
    try:
        isbn13 = re.findall(r'nisbn13: [0-9]{13}', str(soup))[0].split()[1]
        return isbn13
    except:
        return "isbn13 not found"


@time_took
def get_rating_distribution(soup):
    distribution = re.findall(r'renderRatingGraph\([\s]*\[[0-9,\s]+', str(soup))[0]
    distribution = ' '.join(distribution.split())
    distribution = [int(c.strip()) for c in distribution.split('[')[1].split(',')]
    distribution_dict = {'5 Stars': distribution[0],
                         '4 Stars': distribution[1],
                         '3 Stars': distribution[2],
                         '2 Stars': distribution[3],
                         '1 Star': distribution[4]}
    return distribution_dict


@time_took
def get_num_pages(soup):
    if soup.find('span', {'itemprop': 'numberOfPages'}):
        num_pages = soup.find('span', {'itemprop': 'numberOfPages'}).text.strip()
        return int(num_pages.split()[0])
    return ''


@time_took
def get_year_first_published(soup):
    year_first_published = soup.find('nobr', attrs={'class': 'greyText'})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search('([0-9]{3,4})', year_first_published).group(1)
    else:
        return ''


@time_took
def get_id(bookid):
    pattern = re.compile("([^.-]+)")
    return pattern.search(bookid).group()


@time_took
def get_description(soup):
    try:
        return soup.find("div", class_="readable stacked").find_all("span")[1].text.replace("\"", "'")
    except:
        return ""


@time_took
def get_book_thumbail(soup):
    try:
        img = soup.find("img", {"id": "coverImage"})
        return img.attrs["src"]
    except:
        return ""


@time_took
def get_author_thumbnail(soup):
    try:
        auth_img = soup.find("div", {"class": "bookAuthorProfile__photo"}).attrs["style"]
        return auth_img[auth_img.find("url") + 4:-2]
    except:
        return ""


@time_took
def get_author_url(soup):
    try:
        auth_name = soup.find("div", {"class": "bookAuthorProfile__name"}).contents
        return "https://www.goodreads.com" + auth_name[1].attrs["href"]
    except:
        return ""

@time_took
def scrape_book(book_id):
    if not 'https://www.goodreads.com/book/show/' in book_id:
        url = 'https://www.goodreads.com/book/show/' + book_id
    else:
        url = book_id
    source = urlopen(url)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    return {
        'book_title': ' '.join(soup.find('h1', {'id': 'bookTitle'}).text.split()),
        'year_first_published': get_year_first_published(soup),
        'author': ' '.join(soup.find('span', {'itemprop': 'name'}).text.split()),
        'num_pages': get_num_pages(soup),
        'genres': get_genres(soup),
        'average_rating': soup.find('span', {'itemprop': 'ratingValue'}).text.strip(),
        'description': get_description(soup),
        "book_thumbnail" : get_book_thumbail(soup),
        "author_thumbnail" : get_author_thumbnail(soup),
        "author_url": get_author_url(soup),
    }


def condense_books(books_directory_path):
    books = []

    for file_name in os.listdir(books_directory_path):
        if file_name.endswith('.json') and not file_name.startswith('.') and file_name != "all_books.json":
            _book = json.load(open(books_directory_path + '/' + file_name, 'r'))  # , encoding='utf-8', errors='ignore'))
            books.append(_book)

    return books


# def main():
#     start_time = datetime.now()
#     script_name = os.path.basename(__file__)
#
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--book_ids_path', type=str)
#     parser.add_argument('--output_directory_path', type=str)
#     parser.add_argument('--format', type=str, action="store", default="json",
#                         dest="format", choices=["json", "csv"],
#                         help="set file output format")
#     args = parser.parse_args()
#
#     book_ids = [line.strip() for line in open(args.book_ids_path, 'r') if line.strip()]
#     books_already_scraped = [file_name.replace('.json', '') for file_name in os.listdir(args.output_directory_path) if file_name.endswith('.json') and not file_name.startswith('all_books')]
#     books_to_scrape = [book_id for book_id in book_ids if book_id not in books_already_scraped]
#     condensed_books_path = args.output_directory_path + '/all_books'
#
#     for i, book_id in enumerate(books_to_scrape):
#         try:
#             print(str(datetime.now()) + ' ' + script_name + ': Scraping ' + book_id + '...')
#             print(str(datetime.now()) + ' ' + script_name + ': #' + str(i + 1 + len(books_already_scraped)) + ' out of ' + str(len(book_ids)) + ' books')
#
#             book = scrape_book(book_id)
#             json.dump(book, open(args.output_directory_path + '/' + book_id + '.json', 'w'))
#
#             print('=============================')
#
#         except HTTPError as e:
#             print(e)
#             exit(0)
#
#     books = condense_books(args.output_directory_path)
#     if args.format == 'json':
#         json.dump(books, open(f"{condensed_books_path}.json", 'w'))
#     elif args.format == 'csv':
#         json.dump(books, open(f"{condensed_books_path}.json", 'w'))
#         book_df = pd.read_json(f"{condensed_books_path}.json")
#         book_df.to_csv(f"{condensed_books_path}.csv", index=False, encoding='utf-8')
#
#     print(str(datetime.now()) + ' ' + script_name + f':\n\n🎉 Success! All book metadata scraped. 🎉\n\nMetadata files have been output to /{args.output_directory_path}\nGoodreads scraping run time = ⏰ ' + str(datetime.now() - start_time) + ' ⏰')


# if __name__ == '__main__':
#     main()
