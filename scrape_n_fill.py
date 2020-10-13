from bs4 import BeautifulSoup as bs
import requests
from collections import Counter
from dataclasses import dataclass

API_URL = "http://127.0.0.1:5000"

STACKJOBS = {
        "name": "stackoverflow.com",
        "css_class": "post-tag no-tag-menu"
        }

FREELANCER = {
        "name": "www.freelancer.com",
        "css_class": "JobSearchCard-primary-tagsLink",
        }

@dataclass
class Site:
    id: int
    name: str

def get_tags(html_page, css_class):
    soup = bs(html_page, 'html.parser')
    html_tags = soup.find_all('a', {"class": css_class})
    return [x.text for x in html_tags]


def get_stackjobs_pages(session):
    # results from stackoverflow.com/jobs depend on agent header
    # and I presume some others. This got 1k results, without this - 16k
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept":"text/html"})

    first_page = session.get('https://stackoverflow.com/jobs').text
    yield first_page
    soup = bs(first_page, 'html.parser')
    # getting number of pages from pagination item title
    pagi_tag = soup.select_one("a.s-pagination--item.is-selected")
    # title -> "page 1 of <int>"
    num_pages = int(pagi_tag.get("title").rsplit(" ", 1)[1])
    print(num_pages)
    for i in range(2, num_pages + 1):
        print(f"page: {i}")
        next_page = session.get('https://stackoverflow.com/jobs', params={'pg': i}, headers={"Accept":"text/html"}).text
        yield next_page


def get_freelancer_pages(session):
    first_page = session.get("https://www.freelancer.com/work/projects/?results=100").text
    yield first_page
    soup = bs(first_page, 'html.parser')
    # getting number of results from spec span
    num_results = soup.find('span', {"id":"total-results"}).text
    num_pages = int(num_results) // 100 + 1
    print(f"freelancer pages: {num_pages}")
    for i in range(2, num_pages + 1):
        print(f"page: {i}")
        next_page = session.get(f"https://www.freelancer.com/work/projects/{i}/?results=100").text
        yield next_page


def scrape_origin(css_class, page_gen):
    tags = []
    with requests.Session() as session:
        for html_page in page_gen(session):           
            tags += get_tags(html_page, css_class)
    tags_counter = Counter(tags) 
    return tags_counter   

origins = [FREELANCER, STACKJOBS]
page_gens = {
        "stackoverflow.com": get_stackjobs_pages,
        "www.freelancer.com": get_freelancer_pages,
}

rs = requests.delete(API_URL + "/tag")
print(rs.json())

for site_data in origins:
    rs = requests.put(API_URL + "/site", {'name':site_data['name']})
    site = Site(**rs.json())
    counter = scrape_origin(site_data['css_class'], page_gens[site_data['name']])
    rs = requests.post(API_URL + f"/tag/{site.id}", json=dict(counter))
    print(rs.json())