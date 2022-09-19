import requests
import csv
import random
import re
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


def iHateUnlimitedScrolling(url):  # https://stackoverflow.com/a/57452250

    driver = webdriver.Chrome()
    driver.get(url)

    heights = []
    counter = 0
    for i in range(1,300):
        bg = driver.find_element(By.XPATH, "//div[@class='result-list-container']//div")
        driver.execute_script("arguments[0].click();", bg)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    return driver.page_source


class Response404(Exception):
    pass


class ProxyFileDoesNotExist(Exception):
    pass


def downloadProxy():
    file = open('proxy.log', 'w+')
    print('Downloading proxy list...')
    proxies = downloadProxyScrapeList()
    numOfProxies = len(proxies)
    print(f'{numOfProxies} found!')
    print(f'Checking proxies... (This will take approx. {round((numOfProxies // 4.157) // 60)} minutes)')
    checkedProxies = 0
    for proxy in proxies:
        proxy = checkProxy(proxy, 'https://www.zillow.com/')
        if proxy:
            with open('proxy.log', 'a') as file:
                file.write(proxy + '\n')
            checkedProxies += 1
            if checkedProxies == 1:
                print(f'{checkedProxies} proxy checked...')
            else:
                print(f'{checkedProxies} proxies checked...')
    print('Finished downloading proxies!')
    return loadProxyFile()


def loadProxyFile():
    IPs = []
    try:
        file = open('proxy.log', 'r')
    except FileNotFoundError:
        print('Proxy list not found!')
        return downloadProxy()
        # raise ProxyFileDoesNotExist
    print('Proxy list loaded!')
    for line in file:
        IPs.append(line)
    return IPs


def downloadProxyScrapeList():
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }
    proxyList = []

    try:
        response = requests.get('https://api.proxyscrape.com/?request=getproxies&proxytype=http', headers=header,
                                stream=True)
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    proxyList.append(line)
        return proxyList
    except Exception as ex:
        print(ex)
        pass


def checkProxy(proxyIP, url):
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }
    proxy = {
        'http': proxyIP
    }

    try:
        response = requests.get(url, headers=header, proxies=proxy)
        if response.status_code == 200:
            return proxyIP
        else:
            return False
    except Exception as ex:
        pass


def startScraping():
    urls = ['https://www.zillow.com/houston-tx/',
            'https://www.zillow.com/houston-tx/houses/',
            'https://www.zillow.com/houston-tx/townhomes/',
            'https://www.zillow.com/houston-tx/condos/',
            'https://www.zillow.com/houston-tx/duplex/',
            'https://www.zillow.com/houston-tx/mobile/'
            ]

    proxy_list = loadProxyFile()
    for url in urls:
        try:
            resultsRetrieved = 0
            print(f'Preparing to collect results from {url}...')
            properties = scrapeSearch(url, proxy_list)
            if properties:
                print(f'{len(properties)} results found...')
                for propertyURL in properties:
                    data = scrapePropertyInfo(propertyURL, proxy_list)
                    writeCSV(data)
                    resultsRetrieved += 1
                    if resultsRetrieved == 1:
                        print(f'{resultsRetrieved} result retrieved...')
                    else:
                        print(f'{resultsRetrieved} results retrieved...')
            else:
                pass
        except AttributeError as ex:
            print('Error: Attribute does not exist')
            print('(Being blocked by captcha or scraped a page without expected values?)')
            print('"findAll" attribute errors likely indicate we are being blocked by the captcha')
            print(ex)
            pass
        except KeyboardInterrupt as ex:
            print('Error: Halted by keyboard interrupt')
            break
        except Response404 as ex:
            print('Error: 404')
            print(ex)
            pass
        except ProxyFileDoesNotExist as ex:
            print('Error: No proxy file downloaded...')
            downloadProxy()
            pass
        except Exception as ex:
            print(ex)
        else:
            print(f'{url} finished!')


def createCSV():
    file = open('houston.csv', 'w+', newline='')
    with file:
        writer = csv.DictWriter(file, fieldnames=['address', 'price', 'type', 'bed', 'sqft', 'walk', 'transit', 'bike'])
        writer.writeheader()
    file.close()
    print('houston.csv created...')


def writeCSV(data):
    try:
        file = open('houston.csv', 'a', newline='')
    except FileNotFoundError:
        createCSV()
        file = open('houston.csv', 'a', newline='')
    with file:
        writer = csv.DictWriter(file, fieldnames=['address', 'price', 'type', 'bed', 'sqft', 'walk', 'transit', 'bike'])
        writer.writerow(data)
    file.close()


def scrapeSearch(url, proxy_list):
    header = {  # you might have to ctrl+shift+i on zillow and go into network to get the cookie
        'cookie': 'zgsession=1|c1c3b65c-07b2-4c9b-ae8e-272e65beb138; zguid=24|%248a700c4c-4e6c-462a-b63d-bfeb3bfeefe3; pxcts=7badca67-351d-11ed-a934-7753566e4f55; _pxvid=7badbf75-351d-11ed-a934-7753566e4f55; G_ENABLED_IDPS=google; JSESSIONID=76F1FFB34E993848A9D4279D0FF338EC; _px3=c97fe022052ee8d0a05b5b753ae38199e1b0a85a3da6ceab34b3f309fab5001d:dohS7LTjgz1LzRWY29fBwYp0WKCL6O0DKlCl1+nzkNf5S6JYPIhA0zAe4K3CCz7UzNGuKSsaGlAcmChTMO7JSg==:1000:rq1bhAXx8HIJ0gZi45yiFYcrdPCskH/gNUJE/8oeWZ7l/MuiJVN4CWcMVvFFNqwZZthU2GFDnYzv9Dw87iqej/flzwbSp7bC6KMaSkCaG9aFeLJ9RKAAUhPhJCOl23UzRYvUX/RdhEpzzClo7IZ0Z43efmRgyG1t1SDtHPCR2Ig9mFPlegnJio0ACBNMvS/3MnVnR4kPCuXoH5bg1jZTBQ==; AWSALB=GiTW3+5xEI6dHP85RqnyyPqMQq44Zq8cld345nrWbF9YVnVxBbHznGLfnMVS7+yzl1WEVHXJ08FSCn7xzxFjV4VTr+pq/SJEApVpgvaItDJHwv7GOZpTkFzoKqrf; AWSALBCORS=GiTW3+5xEI6dHP85RqnyyPqMQq44Zq8cld345nrWbF9YVnVxBbHznGLfnMVS7+yzl1WEVHXJ08FSCn7xzxFjV4VTr+pq/SJEApVpgvaItDJHwv7GOZpTkFzoKqrf; search=6|1665956248020%7Crect%3D30.315590363280915%252C-94.62097225585939%252C29.317134675975517%252C-96.22772274414064%26rid%3D39051%26disp%3Dmap%26mdm%3Dauto%26p%3D1%26z%3D1%26fs%3D1%26fr%3D0%26mmm%3D0%26rs%3D0%26ah%3D0%26singlestory%3D0%26housing-connector%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%26zillow-owned%3D0%263dhome%3D0%26featuredMultiFamilyBuilding%3D0%09%0939051%09%09%09%09%09%09',
        'dnt': '1',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    }

    try:
        random_proxy = random.randint(0, len(proxy_list) - 1)
        proxy = {
            'http': proxy_list[random_proxy]
        }
        response = requests.get(url, headers=header, proxies=proxy)
        lastPropertyURL = ""

        if response.status_code == 200:

            # Only 20 pages are accessible without zooming in on zillow's map to narrow results shown, each page has 40 results
            resultsRemaining = 800
            pages = []
            resultsURLs = []

            for i in range(20):
                pages.append(f'{url}{i + 1}_p' if (i + 1 > 1) else f'{url}')
            for page in pages:

                random_proxy = random.randint(0, len(proxy_list) - 1)
                proxy = {
                    'http': proxy_list[random_proxy]
                }
                response = requests.get(page, headers=header, proxies=proxy)
                #page_source = iHateUnlimitedScrolling(page)
                soup = BeautifulSoup(response.text, "html5lib")

                propertyListingsDiv = soup.find('div', {'class': 'result-list-container'})
                properties = propertyListingsDiv.findAll('a', {'class': 'property-card-link'})
                for index, propertyListing in enumerate(properties):
                    if resultsRemaining and index <= 80:  # There's supposed to be 40 results per page, but I can't find a better element to scrape URLs from so we're getting duplicates
                        propertyURL = str(propertyListing).split('href="')[1].split('"')[0]
                        print(f'{index} results found...')
                        if propertyURL != lastPropertyURL:
                            lastPropertyURL = propertyURL
                            resultsURLs.append(propertyURL)
                            resultsRemaining -= 1
                    else:
                        break
            pages.clear()
            return resultsURLs
        elif response.status_code == 404:
            raise Response404
    except Exception as ex:
        print(ex)
        pass


def scrapePropertyInfo(url, proxy_list):
    header = {  # you might have to ctrl+shift+i on zillow and go into network to get the cookie
        'cookie': 'zgsession=1|c1c3b65c-07b2-4c9b-ae8e-272e65beb138; zguid=24|%248a700c4c-4e6c-462a-b63d-bfeb3bfeefe3; pxcts=7badca67-351d-11ed-a934-7753566e4f55; _pxvid=7badbf75-351d-11ed-a934-7753566e4f55; G_ENABLED_IDPS=google; JSESSIONID=76F1FFB34E993848A9D4279D0FF338EC; _px3=c97fe022052ee8d0a05b5b753ae38199e1b0a85a3da6ceab34b3f309fab5001d:dohS7LTjgz1LzRWY29fBwYp0WKCL6O0DKlCl1+nzkNf5S6JYPIhA0zAe4K3CCz7UzNGuKSsaGlAcmChTMO7JSg==:1000:rq1bhAXx8HIJ0gZi45yiFYcrdPCskH/gNUJE/8oeWZ7l/MuiJVN4CWcMVvFFNqwZZthU2GFDnYzv9Dw87iqej/flzwbSp7bC6KMaSkCaG9aFeLJ9RKAAUhPhJCOl23UzRYvUX/RdhEpzzClo7IZ0Z43efmRgyG1t1SDtHPCR2Ig9mFPlegnJio0ACBNMvS/3MnVnR4kPCuXoH5bg1jZTBQ==; AWSALB=GiTW3+5xEI6dHP85RqnyyPqMQq44Zq8cld345nrWbF9YVnVxBbHznGLfnMVS7+yzl1WEVHXJ08FSCn7xzxFjV4VTr+pq/SJEApVpgvaItDJHwv7GOZpTkFzoKqrf; AWSALBCORS=GiTW3+5xEI6dHP85RqnyyPqMQq44Zq8cld345nrWbF9YVnVxBbHznGLfnMVS7+yzl1WEVHXJ08FSCn7xzxFjV4VTr+pq/SJEApVpgvaItDJHwv7GOZpTkFzoKqrf; search=6|1665956248020%7Crect%3D30.315590363280915%252C-94.62097225585939%252C29.317134675975517%252C-96.22772274414064%26rid%3D39051%26disp%3Dmap%26mdm%3Dauto%26p%3D1%26z%3D1%26fs%3D1%26fr%3D0%26mmm%3D0%26rs%3D0%26ah%3D0%26singlestory%3D0%26housing-connector%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%26zillow-owned%3D0%263dhome%3D0%26featuredMultiFamilyBuilding%3D0%09%0939051%09%09%09%09%09%09',
        'dnt': '1',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    }
    try:
        random_proxy = random.randint(0, len(proxy_list) - 1)
        proxy = {
            'http': proxy_list[random_proxy]
        }
        response = requests.get(url, headers=header, proxies=proxy)
        soup = BeautifulSoup(response.text, 'lxml')
        propertyPrice = soup.find('span', {'data-testid': 'price'}).text.strip()
        propertyAddress = soup.find('div', {'class': 'hdp__sc-riwk6j-0 tLBoE'}).text.strip()
        if ')' in propertyAddress:
            propertyAddress = propertyAddress.split(')')[1]
        propertyType = soup.find('span',
                                 {'class': 'Text-c11n-8-65-2__sc-aiai24-0 dpf__sc-2arhs5-3 kpJbvM btxEYg'}).text.strip()
        propertyBedBathBeyond = soup.find('span', {'data-testid': 'bed-bath-beyond'}).text.strip().split('bd')
        propertyBed = propertyBedBathBeyond[0]
        propertySqft = propertyBedBathBeyond[1].split('ba')[1].split(' ')[0]
        walkScoreUrl = f'https://www.walkscore.com/score/{propertyAddress.lower().replace("#", "").replace(",", "").replace(" ", "-").replace(" ", "-")}'  # Zillow has some random white space character in their address text that we need to clean up

        data = {
            'address': propertyAddress,
            'price': propertyPrice,
            'type': propertyType,
            'bed': propertyBed,
            'sqft': propertySqft,
            'walk': walkScoreScrape(walkScoreUrl, "walk", proxy_list),
            'transit': walkScoreScrape(walkScoreUrl, "transit", proxy_list),
            'bike': walkScoreScrape(walkScoreUrl, "bike", proxy_list)
        }
        return data
    except Exception as ex:
        print(ex)
        pass


def walkScoreScrape(walkScoreUrl, score, proxy_list):
    if score == "walk" or score == "transit" or score == "bike":
        header = {  # you might have to ctrl+shift+i on walkscore.com and go into network to get the cookie
            'cookie': 'session="xhhi8hPHA5q2LZrzHfm0mhv7bkk=?_expires=STE2NjU5NDkwMDcKLg==&_permanent=STAxCi4=&has_commute=STAwCi4=&session_id=UydiOGQ1ZmJlZDQyMWEyMDcwJwpwMAou"',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
        }

        random_proxy = random.randint(0, len(proxy_list) - 1)
        proxy = {
            'http': proxy_list[random_proxy]
        }
        response = requests.get(walkScoreUrl, headers=header, proxies=proxy)
        soup = BeautifulSoup(response.text, 'lxml')

        propertyScore = soup.find('div', {'data-eventsrc': f'score page {score} badge'})
        try:
            if propertyScore:
                propertyScore = re.findall("\d+", propertyScore.img.get('alt'))[0]
                if int(propertyScore) > 100:  # I have no clue what's happening, but for some reason we're occasionally grabbing the street address instead of the score, reloading the page and trying again seems to *sometimes* fix it...
                    random_proxy = random.randint(0, len(proxy_list) - 1)
                    proxy = {
                        'http': proxy_list[random_proxy]
                    }
                    response = requests.get(walkScoreUrl, headers=header, proxies=proxy)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    propertyScore = soup.find('div', {'data-eventsrc': f'score page {score} badge'})
                    propertyScore = re.findall("\d+", propertyScore.img.get('alt'))[0]
                    if int(propertyScore) > 100:
                        propertyScore = '-1'
            else:
                propertyScore = 'N/A'
        except Exception as ex:
            print(ex)
            propertyScore = 'N/A'
        return propertyScore




