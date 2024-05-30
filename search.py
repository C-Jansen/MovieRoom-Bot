import requests
from bs4 import BeautifulSoup

postlimit = 5

def getSoup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        return soup
    except requests.exceptions.RequestException as e:
        raise Exception(str(e))
    
def searchMovies(query, ss, ep, page=None):
    try:
        if page is not None:
            base_url = f'https://fmoviesz.to/filter?keyword={query}&page={page}'
            currentPage = page
        else:
            base_url = f'https://fmoviesz.to/filter?keyword={query}'
            currentPage = '1'
        soup = getSoup(base_url)
    except Exception as e:
        moviesDictionary = {
            'success': False,
            'query': query,
            'error': str(e),
            'data': [],
        }
        return moviesDictionary

    moviesDictionary = {
        'success': True,
        'query': query,
        'currentPage': currentPage,
        'data': [],
    }

    items = soup.find_all('div', class_='item')

    for item in items:
        try:
            a = item.find('a')
            href = a.get('href')
            link = f'https://fmoviesz.to{href}/{ss}-{ep}'
        except Exception as e:
            link = str(e)

        try:
            a = item.find('img')
            title = a.get('alt')
        except Exception as e:
            title = str(e)
        
        try:
            img = item.find('img')
            cover = img['data-src']
        except Exception as e:
            cover = str(e)
        
        try:
            type = item.find('span', class_='type').text
        except Exception as e:
            type = str(e)

        try:
            if type == 'MOVIE' or type.startswith('SS'):
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                year = listData[0]
            else:
                year = 'N/A'
        except Exception as e:
            year = str(e)
        
        try:
            if type == 'MOVIE':
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                duration = listData[2]
            else:
                duration = 'N/A'
        except Exception as e:
            duration = str(e)

        try:
            if type.startswith('SS'):
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                episodes = listData[-2]
            else:
                episodes = 'N/A'
        except Exception as e:
            episodes = str(e)

        moviesObject = {
            'link': link,
            'cover': cover,
            'title': title,
            'type': type,
            'year': year,
            'duration': duration,
            'seasons': type,
            'episodes': episodes
        }
        
        moviesDictionary['data'].append(moviesObject)
    
    moviesDictionary['totalPages'] = getPages(soup, query)

    return moviesDictionary['data'][:postlimit]

def getPages(soup, query):
    try:
        ul = soup.find('ul', class_='pagination')
        li = ul.find_all('li')
    except:
        pages = '1'
        return pages

    for l in li:
        a = l.find('a', string='»')
    if a is not None:
        href = a['href']
        hrefSplit = href.split('page=')
        pages = hrefSplit[1]
        return pages
