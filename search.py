import requests
from bs4 import BeautifulSoup


postlimit = 6
def getMovies(query):
    moviesDictionary = {
        'success': True,
        'query': query,
        'data': [],
    }
    page = 1
    try:
        if page != None:
            base_url = f'https://fmoviesz.to/filter?keyword={query}&page={page}'
            currentPage = page
            soup = BeautifulSoup(requests.get(base_url).content, 'lxml')
        else:
            base_url = f'https://fmoviesz.to/filter?keyword={query}'
            currentPage = '1'
            soup = BeautifulSoup(requests.get(base_url).content, 'lxml')
    except requests.exceptions.RequestException as e:
        moviesDictionary['success'] = False,
        moviesDictionary['error'] = str(e),
        return moviesDictionary

    moviesDictionary['currentPage'] = currentPage

    items = soup.find_all('div', class_='item')

    for item in items:
        try:
            a = item.find('a')
            href = a.get('href')
            link = f'https://fmoviesz.to{href}/1-1'
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
            quality = item.find('div', class_="quality").text
        except Exception as e:
            quality = str(e)


        try:
            type = item.find('i', class_='type').text
        except Exception as e:
            type = str(e)

        try:
            if(type == 'MOVIE'):
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                year = listData[0]
            else:
                year = 'N/A'
        except Exception as e:
            year = str(e)
        
        try:
            if(type == 'MOVIE'):
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                duration = listData[1] + " " + listData[2]
            else:
                duration = 'N/A'
        except Exception as e:
            duration = str(e)

        try:
            if(type == 'TV'):
                rawData = item.find('div', class_='meta').text
                listData = rawData.split()
                seasons = listData[1]
            else:
                seasons = 'N/A'
        except Exception as e:
            seasons = str(e)

        try:
            if(type == 'TV'):
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
            
            
            'title': title
            
            #'year': year,
            #'duration': duration,
            #'seasons': seasons,
            #'episodes': episodes
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
        a = l.find('a', text='»')
    if a != None:
        href = a['href']
        hrefSplit = href.split('page=')
        pages = hrefSplit[1]
        return pages
