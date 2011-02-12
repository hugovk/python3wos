
#from urllib.request import urlopen
from urllib import urlopen
import pprint
import re
import os
from collections import namedtuple

from BeautifulSoup import BeautifulSoup

from filecache import filecache

base_url = 'http://pypi.python.org'
pkg_list_url = base_url + '/pypi?%3Aaction=index'
pkg_info = namedtuple('pkg_info', 'name url py3 downloads')

how_many_to_chart = 100

@filecache(3 * 24 * 60 * 60)
def get_rows():
    html = urlopen(pkg_list_url).read()
    rows = re.findall(b'<tr[ ].*?</tr>', html, re.DOTALL)
    return rows



def get_url(row):
    return re.findall(r'href="([^"]+)', row)[0]

def get_table(html):
    soup = BeautifulSoup(html)
    table = []
    all_tables = soup.findAll('table')
    if len(all_tables) == 0:
        return
    table_soup = all_tables[0]
    for tr in table_soup.findAll('tr'):
        row = []
        for td in tr.findAll(['td', 'th']):
            row.append(''.join(td.findAll(text=True)).strip())
        table.append(row)

    return table
            
    
def get_downloads(html):
    downloads = 0
    table = get_table(html)
    if table is None:
        return 0
    
    for row in table:
        if len(row) == 0:
            continue
        downloads_column = row[-1]
        if downloads_column.isdigit():
            downloads += int(downloads_column)

    return downloads


@filecache(3 * 24 * 60 * 60)
def get_package_info(url):
    html = urlopen(url).read()

    titles = re.findall(r'<h1>(.*?)</h1>', html)
    name = titles[0]
    
    if 'Programming Language :: Python :: 3' in html:
        py3 = True
    else:
        py3 = False

    downloads = get_downloads(html)

    info = pkg_info(py3=py3, downloads=downloads, name=name, url=url)

    return info
    
def get_packages():
    rows = get_rows()
    for row in rows:
        url = get_url(row)
        try:
            info = get_package_info(base_url + url)
        except Exception, e:
            print(url)
            print(e)
            continue
            
        #print info
        yield info

def build_html():
    packages = list(get_packages())
    def get_downloads(x): return x.downloads
    packages.sort(key=get_downloads)
    
    # just for backup
    open('results.txt', 'w').write(pprint.pformat(packages))
    
    top = packages[-how_many_to_chart:]
    total_html = "<table>%s</table>"
    rows = []
    row_template = '''<tr class="py3{py3}"><td><a href="{url}">{name}</a></td><td>{downloads}</td></tr>'''
    for package in reversed(top):
        rows.append(row_template.format(**package._asdict()))

    return total_html % '\n'.join(rows)

html = build_html()

open('results.html', 'w').write(html)


    
