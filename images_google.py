from selenium import webdriver
import time, re, os
from time import sleep
from urllib.parse import unquote
from urllib.request import urlretrieve
from bs4 import BeautifulSoup



def get_driver(driver_filepath, headless = True):
    options = webdriver.FirefoxOptions()
    #prefs = {'profile.default_content_setting_values.notifications' : 2}
    #options.add_experimental_option('prefs',prefs)
    if headless:
        options.headless = True
    driver = webdriver.Firefox(executable_path=driver_filepath, options = options)
    driver.maximize_window()
    return driver
    
    
    
    
def scroll_indef(driver, class_name):
    while True:
        try:
            driver.find_element_by_id('smb').click()
            sleep(1)
        except:
            pass
        try:
            driver.find_element_by_class_name('btn_seemore').click()
            sleep(1)
        except:
            pass
        try:
            driver.find_element_by_class_name('more-res').click()
            sleep(1)
        except:
            pass
        try:
            driver.find_element_by_class_name('mye4qd').click()
            sleep(1)
        except:
            pass
        lh = driver.execute_script('return document.body.scrollHeight')
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        sleep(2)
        nh = driver.execute_script('return document.body.scrollHeight')
        if nh == lh:
            break
        lh = nh
    return driver




def get_img_src(driver):
    divs = driver.find_elements_by_xpath('//div[contains(@class,"isv-r")]')
    if not divs:
        divs = driver.find_elements_by_xpath('//div[contains(@class,"rg_bx")]')
    i = 0
    e = 0
    counter = 0
    sources = []
    for ele in divs:
        try:
            s = BeautifulSoup(ele.get_attribute('innerHTML'), features='lxml')
            if 'Related searches' in s.get_text():
                continue
            a = s.findAll('a', attrs={'href': re.compile("^[/imgres?imgurl=]")})
            if a:
                img_src = a[0]['href']
                img_src = img_src.split("/imgres?imgurl=")[1].split("&imgrefurl")[0]
                img_src = unquote(img_src)
                if img_src not in sources:
                    sources.append(img_src) 
                i += 1
            else:
                ele.click()
                s = BeautifulSoup(ele.get_attribute('innerHTML'), features='lxml')
                a = s.findAll('a', attrs={'href': re.compile("^[/imgres?imgurl=]")})
                if a:
                    img_src = a[0]['href']
                    img_src = img_src.split("/imgres?imgurl=")[1].split("&imgrefurl")[0]
                    img_src = unquote(img_src)
                    if img_src not in sources:
                        sources.append(img_src) 
                else:
                    y = driver.find_elements_by_id('islsp')
                    if not y:
                        y = driver.find_elements_by_id('irc-ss')
                    y = y[0]
                    if not 'img' in y.get_attribute('innerHTML'):
                        ele.click()
                        y = driver.find_element_by_id('islsp')
                        if not 'img' in y.get_attribute('innerHTML'):
                            continue
                    s = BeautifulSoup(y.get_attribute('innerHTML'), features='lxml')
                    if ele == divs[0]:
                        img_src = s.find('img')['src']
                    else:
                        img_src = s.findAll('img')[1]['src']
                    if img_src not in sources:
                        sources.append(img_src)
                e +=1
        except:
            print('Failed on element ' + str(e))
            
        counter += 1
    return sources




def collect(search_terms):
    #search_terms can be a string or a list of strings
    driver_path = r"\\geckodriver64" #insert path to selenium firefox driver here
    driver = get_driver(driver_path, False)
    if type(search_terms)==str:
        search_terms = [search_terms]

    i = 1
    errors = 0
    collected = []
    failures = []
    for term in search_terms:
        query = term.replace(' ','+')
        google_url = 'https://www.google.com/search?as_st=y&tbm=isch&hl=en' + \
                        '&as_q=' + query + '&as_epq=&as_oq=&as_eq=' + \
                        '&cr=&as_sitesearch=&safe=active&tbs=isz:lt,islt:xga'
        urls = [google_url]
        u = 1
        for url in urls:
            driver.get(url)
            sleep(2)
            if u == 1:
                driver = scroll_indef(driver, 'rg_bx')
                sources = get_img_src(driver)
                
            elif u == 2:
                driver = scroll_indef(driver, 'ld')
                source = driver.page_source
                soup = BeautifulSoup(source, 'html.parser')
                imgs = soup.findAll('img', id_='yui')
                
            else:
                driver = scroll_indef(driver, 'imgpt')
                source = driver.page_source
                soup = BeautifulSoup(source, 'html.parser')
                imgs = soup.findAll('img', class_='mimg')
                
            i = 0
            errors = 0
            collect_path = r'\\scraped_images' #insert path to scraped_images folder here
            #get year/month/day for new folder if necessary
            now = time.localtime()
            folder = str(now.tm_year)
            folder += str(now.tm_mon) if len(str(now.tm_mon))==2 else '0' + str(now.tm_mon)
            folder += str(now.tm_mday) if len(str(now.tm_mday))==2 else '0' + str(now.tm_mday)
            new_folder = collect_path + '/' + folder
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
            for source in sources:
                try:
                    img_path = new_folder + '/' + query + '_' + str(i) + '.png'
                    urlretrieve(source, img_path)
                    collected.append(source)
                    i += 1
                except:
                    failures.append(source)
                    errors += 1
                if ((i + errors)%5)==0:
                    s = "Downloaded " + str(i) + " out of " + str(len(sources)) + \
                        " with " + str(errors) + " failures. " + \
                        (str(round((i+errors)/len(sources) * 100, 1))) + \
                        "% complete."
                    print(s, end='\n')
            u += 1
    return {'collected': collected, 'failed': failures}
        

