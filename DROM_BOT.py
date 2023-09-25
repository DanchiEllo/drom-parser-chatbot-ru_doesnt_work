import random
import socket
import time
import requests
import urllib3.exceptions
from bs4 import BeautifulSoup
import os
from io import BytesIO
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from geopy.geocoders import Nominatim
import json
import regions
from PIL import Image
import math
import urllib3
from concurrent.futures import ThreadPoolExecutor


sqlite3.threadsafety = 2
bdpath = ""
pypath = os.path.dirname(os.path.abspath(__file__))

token = "TOKEN" #Your vk token
bh = vk_api.VkApi(token=token)
give = bh.get_api()
longpoll = VkLongPoll(bh)

headers = [{
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu 20.10; Linux x86_64) AppleWebKit/537.36.0 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36.0'},
            {'user-agent': 'unknown_browser'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}]

def createSettingsMessage(user_id):
    settings = runQuery(f"SELECT price, mileage, documents, damage, owner FROM keyboard_user WHERE user_id = {user_id};")[0]
    if all(set == None for set in settings):
        message = "Параметры поиска установлены по умолчанию\n" \
                  "Чтобы их задать перейдите во вкладку \"Настройки\""
        return message
    else:
        message = "Выбранные параметры поиска:\n"
        for set, i in zip(settings, range(len(settings))):
            if set != None and i == 0:
                message = message + f"Желаемая цена: {set} ₽\n"
            elif set != None and i == 1:
                message = message + f"Желаемый пробег: {set} км\n"
            elif set != None:
                message = message + f"{set}\n"
        return message

def poolingFunc(function, args):
    start_time = time.time()
    perdoon = []
    with ThreadPoolExecutor(4) as executor:
        for bass in executor.map(function, args, timeout=60):
            perdoon.append(bass)
    print(time.time() - start_time)
    return perdoon

def createCarousel(urls):
    for i in range(urls.__len__()):
        urls[i] = f'{urls[i]}+-+{i}'
    photos_id = poolingFunc(idPhoto, urls)
    info = []
    for url, photo_id in zip(urls, photos_id):
        response = requests.get((url), headers=headers[random.randint(0, headers.__len__() - 1)])
        soup = BeautifulSoup(response.text, 'lxml')
        name = soup.find_all('span', class_='css-1kb7l9z e162wx9x0')[0].next_element[7:].split(' год')[0]
        price = soup.find_all('div', class_='css-eazmxc e162wx9x0')[0].next_element.replace('\xa0', '')
        ths = soup.find_all('th', class_='css-16lvhul ezjvm5n1')
        table = ''
        if 'Тип техники' in [i.text for i in ths]:
            tds = soup.find_all('td', class_='css-9xodgi ezjvm5n0')
            for td, i in zip(tds, range(0, 2)):
                table = table + f'{td.text}\n'
            info.append(
                {
                    "title": name,
                    "description": f"Цена: {price} ₽",
                    "action": {
                        "type": "open_photo",
                    },
                    "photo_id": photo_id,
                    "buttons": [{
                        "action": {
                            "type": "open_link",
                            "link": url,
                            "label": "Автомобиль на drom.ru"
                        }
                    }]
                })
        else:
            try:
                mileage = soup.find_all('span', class_='css-1osyw3j ei6iaw00')[0].next_element.replace('\xa0', '') + ' км'
            except IndexError:
                mileage = 'новый'
            try:
                owners = soup.find_all('button', class_='e8vftt60 css-1uu0zmh e104a11t0')[0].next_element.split(' зап')[0]
            except IndexError:
                owners = 'Неизвестно'
            info.append(
                {
                        "title": name,
                        "description": f"Цена: {price} ₽, пробег: {mileage}\nЗаписей по ПТС: {owners}",
                        "action": {
                                "type": "open_photo",
                        },
                        "photo_id": photo_id,
                        "buttons": [{
                                "action": {
                                        "type": "open_link",
                                        "link": url,
                                        "label": "Автомобиль на drom.ru"
                                }
                        }]
                        })
    carousel = {
        "type": "carousel",
        "elements": info
    }
    carousel = json.dumps(carousel)
    return carousel

def idPhoto(url_car):
    url_car = url_car.split('+-+')
    try:
        response = requests.get((url_car[0]), headers=headers[random.randint(0, headers.__len__() - 1)])
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            photo_url = soup.find_all('div', class_='css-bjn8wh ecmc0a90')[0].contents[0].get('href')
        except IndexError:
            photo_url = 'https://sun9-56.userapi.com/impg/MK1lwjeq2Q-O4OXErzZXxHzmL2bPPT8ZCwzNVg/BXYB8zit_cg.jpg?size=569x425&quality=96&sign=25c9b7c9fb0fd3f2d7433aa66571cc5e&type=album'
        file = BytesIO(requests.get(photo_url).content)
        img = Image.open(file)
        width, height = img.size
        new_width = 1280
        new_height = 799
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2
        new_image = img.crop((left, top, right, bottom))
        new_image = new_image.resize((884, 544))
        new_image.save(f'{pypath}\\{url_car[1]}nw.png')
        img.close()
        new_image.close()
        a = bh.method("photos.getMessagesUploadServer")
        b = requests.post(a['upload_url'], files={'file': open(f'{pypath}\\{url_car[1]}nw.png', 'r+b')}).json()
        c = bh.method('photos.saveMessagesPhoto', {'photo': b['photo'], 'server': b['server'], 'hash': b['hash']})[0]
        d = "photo{}_{}".format(c["owner_id"], c["id"])
        os.remove(os.path.join(pypath, f"{url_car[1]}nw.png"))
        return d.split('to')[1]
    except IndexError:
        print("No photo!")
        return -1

def correctLists(lists_offers):
    offers = []
    for list_offers in lists_offers:
        for dict in list_offers:
            if dict['photo_url'] != '--------':
                offers.append(dict)
    return sortOffers(offers)

def sortOffers(offers):
    new_offers = sorted(offers, key=lambda d: d['k'])
    offers = sorted(new_offers[:10], key=lambda d: d['price'])
    return offers[:10]

def getPages(url):
    start_getPages = time.time()
    response = requests.get(url, headers=headers[random.randint(0, headers.__len__() - 1)])
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        num_pages = soup.find_all('div', class_='css-1ksi09z e1hsrrag2')
        num_pages = math.ceil(int(num_pages[0].next_element.replace('\xa0', '').split(' о')[0]) / 20)
    except IndexError:
        num_pages = soup.find_all('a', class_='css-192eo94 e1px31z30')
        num_pages = math.ceil(int(num_pages[0].next_element.replace('\xa0', '').split(' о')[0]) / 20)
    if num_pages == 0:
        return [url, ]
    elif num_pages > 100:
        num_pages = 100
        if '?' in url:
            url = url.split('?')
            urls = [f'{url[0]}page{i}/?{url[1]}' for i in range(1, num_pages + 1)]
        else:
            urls = [f'{url}page{i}' for i in range(1, num_pages + 1)]
    else:
        if '?' in url:
            url = url.split('?')
            urls = [f'{url[0]}page{i}/?{url[1]}' for i in range(1, num_pages + 1)]
        else:
            urls = [f'{url}page{i}' for i in range(1, num_pages + 1)]
    print(f'getPages: {time.time() - start_getPages}')
    for a in urls:
        print(a)
    return urls

def getOffers(url):
    urls_pages_num = getPages(url)
    lists = poolingFunc(parceCars, urls_pages_num)
    offers = correctLists(lists)
    urls = []
    for url in offers:
        urls.append(url['url'])
    return urls


def parceCars(url):
    listoffers = []
    i = 0
    response = requests.get(url, headers=headers[random.randint(0, headers.__len__() - 1)])
    soup = BeautifulSoup(response.text, 'lxml')
    photo_urls = soup.find_all('div', class_='css-18zm4we e1e9ee560')
    names = soup.find_all('span', {'data-ftid': 'bull_title'})
    prices = soup.find_all('span', {'data-ftid': 'bull_price'})
    mileages = soup.find_all('span', {'data-ftid': 'bull_description-item'}, class_='css-1l9tp44 e162wx9x0')
    surls = soup.findAll('a', class_='css-xb5nz8 ewrty961')  # css-1dlmvcl ewrty961
    cansels = soup.findAll('div', class_='css-1dkhqyq ep0qbyc0')
    for photo_url, name, price, surl, cansel in zip(photo_urls, names, prices, surls, cansels):
        if 'снят с продажи' in surl.text:
            i = i + 6
            continue
        else:
            for mileage in mileages:
                try:
                    if ("тыс. км" in mileages[i].get_text(strip=True)):
                        if ("< 1 тыс. км") in mileages[i].next_element:
                            k = 0.5 / (float(price.text.replace(' ', '')))
                        else:
                            try:
                                k = float(mileages[i].next_element[:-8]) / (float(price.text.replace(' ', '')))
                                listoffers.append({"name": str(name.text.split(', ')[0]),
                                               "year": str(name.text.split(', ')[1]),
                                               "price": float(price.text.replace(' ', '')),
                                               "mileage": str(mileages[i].next_element),
                                               "k": round(k, 11),
                                               "url": str(surl.get('href')),
                                               "photo_url": photo_url.next_element.next.attrs['data-srcset'].split(' 1x')[0]
                                               })
                            except (KeyError, AttributeError):
                                k = float(mileages[i].next_element[:-8]) / (float(price.text.replace(' ', '')))
                                listoffers.append({"name": str(name.text.split(', ')[0]),
                                               "year": str(name.text.split(', ')[1]),
                                               "price": float(price.text.replace(' ', '')),
                                               "mileage": str(mileages[i].next_element),
                                               "k": round(k, 11),
                                               "url": str(surl.get('href')),
                                               "photo_url": '--------'
                                               })
                        i = i + 1
                        break
                    else:
                        i = i + 1
                except IndexError:
                    mileages = 'null'
                    break
    return listoffers

def regionNumber(info_message):
    latitude = '{:.16f}'.format(info_message['items'][0]['geo']['coordinates']['latitude'])
    longitude = '{:.16f}'.format(info_message['items'][0]['geo']['coordinates']['longitude'])

    geo_location = Nominatim(user_agent="GetLoc")
    try:
        location_name = geo_location.reverse(str(latitude) + ", " + str(longitude)).raw['address']
        for i in regions.regions:
            if location_name['state'] in i['name']:
                return i['id']
        return -1
    except:
        return -1


def sendMessage(user_id, message, keyboard=None, attchment=None):
    post = {
        'user_id': user_id,
        'message': message,
        'random_id': 0}
    if keyboard:
        post['keyboard'] = keyboard.get_keyboard()
    elif attchment:
        post['attachment'] = attchment
    bh.method('messages.send', post)
    return 0


def labelFollow(usid):
    return runQuery(f"SELECT DISTINCT follow FROM offers_to_users WHERE user_id = {usid};")[0][0]

def parceSpeshCars(next_url):
    listoffers = []
    response = requests.get(next_url, headers=headers[random.randint(0, headers.__len__() - 1)])
    soup = BeautifulSoup(response.text, 'lxml')
    surls = soup.findAll('a', class_='css-xb5nz8 ewrty961')
    for surl in surls:
        listoffers.append(surl.get('href'))
    random.shuffle(listoffers)
    return listoffers[:5]

def linkCorrection(message):
    message = message.replace(';', '')
    sort_message = message.replace('amp', '')
    if "&order" in sort_message:
        link = sort_message.split("&order")[0]
    else:
        link = sort_message
    return link


def runQuery(query):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "drom.db")
    con = sqlite3.connect(db_path, check_same_thread=False)
    cur = con.cursor()
    if "SELECT" in query:
        cur.execute(query)
        return cur.fetchall()
    else:
        cur.executescript(query)
    con.commit()
    con.close()


def orExist(usid):
    query = (f"SELECT * FROM offers_to_users WHERE user_id = {usid};")
    lenlist = runQuery(query).__len__()
    if lenlist <= 0:
        return -2
    elif lenlist > 0:
        return 0
    else:
        return -1


def printmessageFromBd(usid):
    query = (f"SELECT * FROM offers_to_users WHERE user_id = {usid} ORDER BY k;")
    sortinfo = runQuery(query)
    listoffers = sorted(sortinfo[:5], key=lambda d: d[3])
    if len(listoffers) == 1:
        offers = ' лучшее предложение:'
    elif 1 < len(listoffers) < 5:
        offers = ' лучших предложения:'
    else:
        offers = ' лучших предложений:'
    s = '-------------------\n' + str(len(listoffers)) + offers
    try:
        for item in listoffers:
            s = s + '\n' \
                    '\nМарка авто: ' + item[1] + '\n' \
                                                 'Год: ' + item[2] + '\n' \
                                                                     'Цена: ' + str(item[3]) + ' руб.' + '\n' \
                                                                                                         'Пробег: ' + str(
                item[4]) + '\n' \
                           'URL: ' + item[6]
        sendMessage(usid, s + '\n-------------------\n')
        return 0
    except vk_api.ApiError:
        return -1
    except requests.exceptions.RequestException:
        print('ConnectionError')

def deleteTableUser(usid):
    try:
        query = (f"DELETE FROM offers_to_users WHERE user_id = {usid};")
        runQuery(query)
        return 0
    except sqlite3.DatabaseError:
        return -1
    except requests.exceptions.RequestException:
        print('ConnectionError')

def getDesiredValues(desired_value):
    if desired_value < 1:
        return 0, 1000
    else:
        desired_value = desired_value
        min_mileage = round(desired_value - (desired_value * 0.295))
        max_mileage = round(desired_value + (desired_value * 0.19))
        return min_mileage, max_mileage


def parceInBd(url, usid, label_follow, num_pages_parsed=None):
    print(f"Parce start from User({usid}), Url({url})")
    next_url = url
    pag = 1
    i = 0
    query = ""
    while pag - 1 != num_pages_parsed:
        try:
            response = requests.get(next_url, headers=headers[random.randint(0, headers.__len__() - 1)])
            soup = BeautifulSoup(response.text, 'lxml')
            names = soup.find_all('span', {'data-ftid': 'bull_title'})
            prices = soup.find_all('span', {'data-ftid': 'bull_price'})
            mileages = soup.find_all('span', {'data-ftid': 'bull_description-item'}, class_='css-1l9tp44 e162wx9x0')
            pages = soup.find_all('a', {'data-ftid': 'component_pagination-item-next'}, class_='css-4gbnjj e24vrp30')
            surls = soup.findAll('a', class_='css-xb5nz8 ewrty961')  # css-1dlmvcl ewrty961
            if surls.__len__() == 0:
                runQuery(query)
                printmessageFromBd(usid)
                print(f"Parce done from User({usid}), Url({url}).")
                print("EBALA")
                return -1
            cansels = soup.findAll('div', class_='css-1dkhqyq ep0qbyc0')
            for name, price, surl, cansel in zip(names, prices, surls, cansels):
                if 'снят с продажи' in surl.text:
                    i = i + 6
                    continue
                else:
                    for mileage in mileages:
                        try:
                            if ("тыс. км" in mileages[i].get_text(strip=True)):
                                if ("< 1 тыс. км") in mileages[i].next_element:
                                    k = 0.5 / (float(price.text.replace(' ', '')))
                                else:
                                    k = float(mileages[i].next_element[:-8]) / (float(price.text.replace(' ', '')))
                                query = query + (f"INSERT OR REPLACE INTO offers_to_users (user_id, name, year, price, mileage, k, url, url_page, follow) \
                                                                                            VALUES({str(usid)}, \"{str(name.text.split(', ')[0])}\", \
                                                                                             {str(name.text.split(', ')[1])}, {float(price.text.replace(' ', ''))}, \
                                                                                                \"{str(mileages[i].next_element)}\", {round(k, 11)}, \"{str(surl.get('href'))}\", \
                                                                                                    \"{str(url)}\", {label_follow});\n")
                                i = i + 1
                                break
                            else:
                                i = i + 1
                        except IndexError:
                            mileages = 'null'
                            break
            if len(pages) != 0:
                for link in pages:
                    next_url = link.get('href')
                pag = pag + 1
                i = 0
            else:
                break
        except requests.exceptions.RequestException:
            print('ConnectionError')
            continue
    print(f"Parce done from User({usid}), Url({url}).")
    runQuery(query)
    query = (f"SELECT * FROM offers_to_users WHERE user_id = {usid} ORDER BY k;")
    info = runQuery(query)
    sortinfo = sorted(info[:5], key=lambda d: d[3])
    urls = set().union((d[6] for d in sortinfo))
    return urls

class userKeyboard(object):
    __slots__ = "user_id"

    def __init__(self, user_id):
        self.user_id = user_id

    def searchKeyboard(self):
        sendMessage(self.user_id, 'Введите марку и модель')
        self.sellPositionInBD("searchKeyboard")

    def keyboardStartMenu(self):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('START', VkKeyboardColor.SECONDARY)
        sendMessage(self.user_id, 'START MENU', keyboard)

    def cancelPrice_keyboard(self, message):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Очистить', VkKeyboardColor.NEGATIVE)
        sendMessage(self.user_id, message, keyboard)

    def cancelMileage_keyboard(self, message):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Очистить', VkKeyboardColor.NEGATIVE)
        sendMessage(self.user_id, message, keyboard)

    def settings_keyboard(self):
        buttons = {
            'Документы в порядке': VkKeyboardColor.PRIMARY,
            'Проблемные документы': VkKeyboardColor.PRIMARY,
            'Без повреждений': VkKeyboardColor.PRIMARY,
            'Требует ремонта': VkKeyboardColor.PRIMARY,
            'Собственник': VkKeyboardColor.PRIMARY,
            'Частник': VkKeyboardColor.PRIMARY,
            'Компания': VkKeyboardColor.PRIMARY
        }
        keyboard = VkKeyboard(one_time=False)

        result = runQuery(f"SELECT documents, damage, owner, price, mileage FROM keyboard_user WHERE user_id = {self.user_id}")
        if result[0][4] != None:
            buttons[f'Пробег {result[0][4]} км'] = VkKeyboardColor.POSITIVE
        else:
            buttons[f'Пробег'] = VkKeyboardColor.PRIMARY

        if result[0][3] != None:
            buttons[f'Цена {result[0][3]} ₽'] = VkKeyboardColor.POSITIVE
        else:
            buttons[f'Цена'] = VkKeyboardColor.PRIMARY


        a = 0
        for i in range(buttons.__len__()):
            if i == 2 or i == 4:
                a = a + 1
            if result[0][a] in list(buttons.keys()):
                buttons[result[0][a]] = VkKeyboardColor.POSITIVE

        for button_key, button_value, i in zip(buttons.keys().__reversed__(), buttons.values().__reversed__(), range(buttons.__len__())):
            if i in [2, 5, 7]:
                keyboard.add_line()
            keyboard.add_button(button_key, button_value)

        keyboard.add_line()
        keyboard.add_button('Помощь💬', VkKeyboardColor.POSITIVE)
        keyboard.add_button('Меню🏁', VkKeyboardColor.SECONDARY)
        sendMessage(self.user_id, 'Главное меню', keyboard)
        self.sellPositionInBD("settings_keyboard")

    def firstMenu(self):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_location_button()
        keyboard.add_line()
        keyboard.add_button('Свежие объявления автомобилей🚗', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Тазы на злых валах😈', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Помощь💬', VkKeyboardColor.POSITIVE)
        keyboard.add_button('Настройки⚙', VkKeyboardColor.PRIMARY)
        sendMessage(self.user_id, 'Главное меню',keyboard)
        self.sellPositionInBD("firstMenu")

    def requestsMenu(self):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Отправить ссылку с параметрами⚙', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Отслеживать🙉', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Не отслеживать🙈', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Помощь💬', VkKeyboardColor.POSITIVE)
        keyboard.add_button('Меню🏁', VkKeyboardColor.SECONDARY)
        sendMessage(self.user_id, 'Запросы', keyboard)
        self.sellPositionInBD("requestsMenu")

    def sellPositionInBD(self, name_function):
        query = f"UPDATE keyboard_user SET position = \"{name_function}\" WHERE user_id = {self.user_id};"
        runQuery(query)

    def documents_keyboard(self):
        keyboard = VkKeyboard(one_time=False)
        buttons = {'Документы в порядке': VkKeyboardColor.SECONDARY,
                   'Проблемные документы': VkKeyboardColor.SECONDARY}
        result = runQuery(f"SELECT documents FROM keyboard_user WHERE user_id = {usid}")
        if result[0][0] != None:
            buttons[result[0][0]] = VkKeyboardColor.POSITIVE
        for button_key, button_value in buttons.items():
            keyboard.add_button(button_key, button_value)
        keyboard.add_line()
        keyboard.add_button('Назад', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Далее', VkKeyboardColor.PRIMARY)
        sendMessage(self.user_id, 'Параметры документов', keyboard)
        self.sellPositionInBD("documents_keyboard")

    def damage_keyboard(self):
        keyboard = VkKeyboard(one_time=False)
        buttons = {'Без повреждений': VkKeyboardColor.SECONDARY,
                   'Требует ремонта': VkKeyboardColor.SECONDARY}
        result = runQuery(f"SELECT damage FROM keyboard_user WHERE user_id = {usid}")
        if result[0][0] != None:
            buttons[result[0][0]] = VkKeyboardColor.POSITIVE
        for button_key, button_value in buttons.items():
            keyboard.add_button(button_key, button_value)
        keyboard.add_line()
        keyboard.add_button('Назад', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Далее', VkKeyboardColor.PRIMARY)
        sendMessage(self.user_id, 'Параметры повреждений', keyboard)
        self.sellPositionInBD("damage_keyboard")

    def owner_keyboard(self):
        keyboard = VkKeyboard(one_time=False)
        buttons = {'Собственник': VkKeyboardColor.SECONDARY,
                   'Частник': VkKeyboardColor.SECONDARY,
                   'Компания': VkKeyboardColor.SECONDARY}
        result = runQuery(f"SELECT owner FROM keyboard_user WHERE user_id = {usid}")
        if result[0][0] != None:
            buttons[result[0][0]] = VkKeyboardColor.POSITIVE
        for button_key, button_value in buttons.items():
            keyboard.add_button(button_key, button_value)
        keyboard.add_line()
        keyboard.add_button('Назад', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Далее', VkKeyboardColor.PRIMARY)
        sendMessage(self.user_id, 'Параметры владельцев', keyboard)
        self.sellPositionInBD("owner_keyboard")

    def typeSpeshCar_keyboard(self):
        keyboard = VkKeyboard(one_time=False)
        buttons = {'Автобусы': VkKeyboardColor.SECONDARY,
                   'Вездеходы': VkKeyboardColor.SECONDARY,
                   'Лесозаготовительная': VkKeyboardColor.SECONDARY,
                   'Автодома': VkKeyboardColor.SECONDARY,
                   'Грузовики': VkKeyboardColor.SECONDARY,
                   'Погрузчики': VkKeyboardColor.SECONDARY,
                   'Автокраны': VkKeyboardColor.SECONDARY,
                   'Дорожно-строительная': VkKeyboardColor.SECONDARY,
                   'Полуприцепы': VkKeyboardColor.SECONDARY,
                   'Экскаваторы': VkKeyboardColor.SECONDARY,
                   'Коммунальная': VkKeyboardColor.SECONDARY,
                   'Прицепы': VkKeyboardColor.SECONDARY,
                   'Тягачи': VkKeyboardColor.SECONDARY,
                   'Сельзозтехниа': VkKeyboardColor.SECONDARY,
                   'Бульдозеры': VkKeyboardColor.SECONDARY,
                   'Другая': VkKeyboardColor.SECONDARY
                   }
        result = runQuery(f"SELECT type_car FROM keyboard_user WHERE user_id = {usid}")
        if result[0][0] != None and result[0][0] != 'speshcar':
            buttons[result[0][0]] = VkKeyboardColor.POSITIVE
        for button_key, button_value, i in zip(buttons.keys(), buttons.values(), range(0, buttons.__len__())):
            if i % 3 == 0 and i != 15 and i != 0:
                keyboard.add_line()
            keyboard.add_button(button_key, button_value)
        keyboard.add_line()
        keyboard.add_button('Назад', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Далее', VkKeyboardColor.PRIMARY)
        sendMessage(self.user_id, 'Параметры владельцев', keyboard)
        self.sellPositionInBD("typeSpeshCar_keyboard")

    def url_offers(self):
        result = runQuery(f"SELECT type_car, documents, damage, owner FROM keyboard_user WHERE user_id = {usid}")[0]
        a = [element for element in result if element != None]
        if result[0] != None:
            values = {
                'Автобусы': 'https://www.drom.ru/spec/bus/all/',
                'Вездеходы': 'https://www.drom.ru/spec/atv/all/',
                'Лесозаготовительная': 'https://www.drom.ru/spec/forestry/all/?',
                'Автодома': 'https://www.drom.ru/spec/motorhome/all/',
                'Грузовики': 'https://www.drom.ru/spec/truck/all/',
                'Погрузчики': 'https://www.drom.ru/spec/loader/all/',
                'Автокраны': 'https://www.drom.ru/spec/crane/all/',
                'Дорожно-строительная': 'https://www.drom.ru/spec/building/all/',
                'Полуприцепы': 'https://www.drom.ru/spec/semitrailer/all/',
                'Экскаваторы': 'https://www.drom.ru/spec/excavator/all/',
                'Коммунальная': 'https://www.drom.ru/spec/municipal/all/',
                'Прицепы': 'https://www.drom.ru/spec/trailer/all/',
                'Тягачи': 'https://www.drom.ru/spec/truck-tractor/all/',
                'Сельзозтехниа': 'https://www.drom.ru/spec/farm/all/',
                'Бульдозеры': 'https://www.drom.ru/spec/bulldozer/all/',
                'Другая': 'https://www.drom.ru/spec/misc/all/',
                'speshcar': 'https://www.drom.ru/spec/used/all/',
                'car': 'https://auto.drom.ru/used/all/',
                'Документы в порядке': 'pts=2',
                'Проблемные документы': 'pts=1',
                'Без повреждений': 'damaged=2',
                'Требует ремонта': 'damaged=1',
                'Собственник': 'isOwnerSells=1',
                'Частник': 'owner_type=1',
                'Компания': 'owner_type=2',
            }

            desired_price = runQuery(f"SELECT price FROM keyboard_user WHERE user_id = {usid}")[0][0]
            desired_mileage = runQuery(f"SELECT mileage FROM keyboard_user WHERE user_id = {usid}")[0][0]
            if desired_price != None:
                (min_price, max_price) = getDesiredValues(desired_price)
                values['desired_price'] = f'minprice={min_price}&maxprice={max_price}'
            if desired_mileage != None:
                (min_mileage, max_mileage) = getDesiredValues(desired_mileage)
                values['desired_mileage'] = f'minprobeg={min_mileage}&maxprobeg={max_mileage}'
            url = ''
            if a.__len__() == 1:
                url = f'{values[a[0]]}'
            elif a.__len__() == 2 and a[0] == 'car':
                url = f'{values[a[0]]}?{values[a[1]]}'
            elif a.__len__() == 3 and a[0] == 'car':
                url = f'{values[a[0]]}?{values[a[1]]}&{values[a[2]]}'
            elif a.__len__() == 4 and a[0] == 'car':
                url = f'{values[a[0]]}?{values[a[1]]}&{values[a[2]]}&{values[a[3]]}'
            elif a.__len__() == 4:
                url = f'{values[a[0]]}?{values[a[1]]}&{values[a[2]]}'
            elif a.__len__() == 2 and a[1] in list(values.keys())[22:25]:
                url = f'{values[a[0]]}'
            elif a.__len__() == 2:
                url = f'{values[a[0]]}?{values[a[1]]}'
            elif a.__len__() == 3 and a[1] in list(values.keys())[22:25] and a[2] not in list(values.keys())[22:25]:
                url = f'{values[a[0]]}?{values[a[2]]}'
            elif a.__len__() == 3 and a[2] in list(values.keys())[22:25]:
                url = f'{values[a[0]]}?{values[a[1]]}'

            if a.__len__() == 1 and desired_price != None:
                url = f"{values[a[0]]}?{values['desired_price']}"
            if a.__len__() == 1 and desired_mileage != None:
                url = f"{values[a[0]]}?{values['desired_mileage']}"
            if a.__len__() == 1 and desired_price != None and desired_mileage != None:
                url = f"{values[a[0]]}?{values['desired_price']}&{values['desired_mileage']}"
            if a.__len__() > 1 and desired_price != None:
                url = url + f"&{values['desired_price']}"
            if a.__len__() > 1 and desired_mileage != None:
                url = url + f"&{values['desired_mileage']}"
            if a.__len__() > 1 and desired_price != None and desired_mileage != None:
                url = url + f"&{values['desired_price']}&{values['desired_mileage']}"

            if url and values['car'] in url:
                print(url)
                bh.method('messages.send', {'user_id': self.user_id, 'message': 'Предложения:', 'random_id': 0,
                                            'template': createCarousel(getOffers(url))})
        else:
            sendMessage(self.user_id, 'Пожалуйста выберите все параметры(документы, повреждения, владельцы)')

    def secondMenu(self):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('MANUAL', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('help', VkKeyboardColor.POSITIVE)
        keyboard.add_button('1', VkKeyboardColor.SECONDARY)
        keyboard.add_button('2', VkKeyboardColor.SECONDARY)
        keyboard.add_button('3', VkKeyboardColor.SECONDARY)
        keyboard.add_button('stop', VkKeyboardColor.NEGATIVE)
        sendMessage(self.user_id, 'Как пользоваться', keyboard)

    def emptyKeyboard(self, message):
        bh.method('messages.send',
                  {'user_id': self.user_id, 'random_id': 0, 'message': message,
                   'keyboard': vk_api.keyboard.VkKeyboard.get_empty_keyboard()})

if __name__ == '__main__':
    with sqlite3.connect('drom.db', check_same_thread=False) as con:
        cur = con.cursor()
        cur.executescript("""CREATE TABLE IF NOT EXISTS offers_to_users (
            user_id TEXT,
            name TEXT,
            year TEXT,
            price REAL,
            mileage TEXT,
            k REAL,
            url TEXT,
            url_page TEXT,
            follow INTEGER,
            unique (user_id, name, year, price, k, url, url_page)
            );
             CREATE TABLE IF NOT EXISTS keyboard_user (
                        user_id TEXT,
                        position TEXT,
                        type_car TEXT,
                        price INT,
                        mileage INT,
                        documents TEXT,
                        damage TEXT,
                        owner TEXT,
                        unique (user_id, documents, damage, owner)
                        );
            CREATE TABLE IF NOT EXISTS messages (
                                user_id TEXT,
                                message TEXT,
                                firstname TEXT,
                                secondname TEXT
                                )""")
        con.commit()
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    message = event.text
                    usid = event.user_id
                    user_keyboard = userKeyboard(usid)
                    if message.lower() == 'начать':
                        query = (f"SELECT * FROM keyboard_user WHERE user_id = {usid};")
                        if runQuery(query).__len__() == 0:
                            query = f"INSERT OR REPLACE INTO keyboard_user (user_id, type_car) VALUES({usid}, \"car\");"
                            runQuery(query)
                        user_keyboard.firstMenu()
                    elif message == 'Меню🏁':
                        user_keyboard.firstMenu()
                    elif message == 'Запросы🧲':
                        user_keyboard.requestsMenu()
                    elif message == 'Настройки⚙':
                        user_keyboard.settings_keyboard()
                    elif message == 'Помощь💬':
                        sendMessage(usid, 'Главное меню:\n'
                                          '\" Отправить своё местоположение\" - Выбираете своё местоположение на карте, чтобы бот'
                                          ' отправил вам лучшие предложения из вашего региона\n'
                                          '\" Свежие объявления автомобилей🚗\" - Отправляет недавно опубликованные предложения всех марок'
                                          ' автомобилей. После нажатия кнопки, вам предоставляется выбор параметров автомобиля, вы можете выбрать предложенные'
                                          ' параметры либо же пропустить их(Далее)\n'
                                          '\" Свежие объявления спецтехники🚐\" - Отправляет недавно опубликованные предложения всех видов спецтехники. После нажатия кнопки'
                                          ' вам предоставляется выбор типа спецтехники и выбор других параметров, вы так же можете пропустить данный этап (Далее)\n'
                                          '\"Тазы на злых валах😈\" - Отправляет недавно опубликованные предложения автомобилей марки \"Лада\" с тюнингом\n'
                                          '\"Запросы\" - После нажатия на кнопку выолняется переход в меню \"Запросы\":\n'
                                          '\" Отправить ссылку с параметрами⚙\" - После нажатия вы отправляете ссылку на drom с выбранными вами параметрами'
                                          ' конкретной марки(модель, цена, объём, тип кузова и т.д.)\n'
                                          '\" Отслеживать🙉\" - После нажатия, бот будет присылать вам только что опубликованные объявления автомобилей(1-2 мин.)'
                                          ' по вашем параметрам которые вы отправили в \"Отправить ссылку с параметрами⚙\"\n'
                                          ' \"Не отслеживать🙈\" - Бот больше не будет присылать только что опубликованные объявления автомобилей\n'
                                          ' \"Меню🏁\" - Переход в главное меню\n'
                                          '\"Помощь💬\" - Отправляет мануал(данное сообщение)')
                    elif message == 'Свежие объявления автомобилей🚗':
                        query = (f"SELECT * FROM keyboard_user WHERE user_id = {usid};")
                        if runQuery(query).__len__() == 0:
                            query = f"INSERT OR REPLACE INTO keyboard_user (user_id, type_car) VALUES({usid}, \"car\");"
                            runQuery(query)
                        else:
                            query = f"UPDATE keyboard_user SET type_car = \"car\" WHERE user_id = {usid};"
                            runQuery(query)
                        user_keyboard.emptyKeyboard(createSettingsMessage(usid))
                        user_keyboard.url_offers()
                        user_keyboard.firstMenu()
                        # user_keyboard.documents_keyboard()
                    elif message == 'Свежие объявления спецтехники🚐':
                        query = (f"SELECT * FROM keyboard_user WHERE user_id = {usid};")
                        if runQuery(query).__len__() == 0:
                            query = f"INSERT OR REPLACE INTO keyboard_user (user_id, type_car) VALUES({usid}, \"speshcar\");"
                            runQuery(query)
                        else:
                            query = f"UPDATE keyboard_user SET type_car = \"speshcar\" WHERE user_id = {usid};"
                            runQuery(query)
                        user_keyboard.typeSpeshCar_keyboard()
                    elif message == 'Тазы на злых валах😈':
                        user_keyboard.emptyKeyboard('Пожалуйста подождите.')
                        bh.method('messages.send', {'user_id': usid, 'message': 'Предложения:', 'random_id': 0,
                                                    'template': createCarousel(getOffers('https://auto.drom.ru/lada/all/?keywords=злые+валы'))})
                        user_keyboard.firstMenu()
                    elif 'Цена' in message or 'а ₽' in message:
                        query = f"UPDATE keyboard_user SET position = \"desired_price\" WHERE user_id = {usid};"
                        runQuery(query)
                        if runQuery(f"SELECT price FROM keyboard_user WHERE user_id = {usid};")[0][0] == None:
                            user_keyboard.emptyKeyboard('Введите цену')
                        else:
                            user_keyboard.cancelPrice_keyboard('Введите цену')
                    elif message == 'Очистить' and 'desired_price' in runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                        query = f"UPDATE keyboard_user SET price = NULL WHERE user_id = {usid};"
                        runQuery(query)
                        user_keyboard.settings_keyboard()
                    elif 'Пробег' in message or 'г км' in message:
                        query = f"UPDATE keyboard_user SET position = \"desired_mileage\" WHERE user_id = {usid};"
                        runQuery(query)
                        if runQuery(f"SELECT mileage FROM keyboard_user WHERE user_id = {usid};")[0][0] == None:
                            user_keyboard.emptyKeyboard('Введите цену')
                        else:
                            user_keyboard.cancelMileage_keyboard('Введите пробег')
                    elif message == 'Очистить' and 'desired_mileage' in runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                        query = f"UPDATE keyboard_user SET mileage = NULL WHERE user_id = {usid};"
                        runQuery(query)
                        user_keyboard.settings_keyboard()
                    elif message in ('Документы в порядке', 'Проблемные документы'):
                        if message == runQuery(f"SELECT documents FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                            query = f"UPDATE keyboard_user SET documents = NULL WHERE user_id = {usid};"
                            runQuery(query)
                        else:
                            query = f"UPDATE keyboard_user SET documents = \"{message}\" WHERE user_id = {usid};"
                            runQuery(query)
                        user_keyboard.settings_keyboard()
                    elif message in ('Без повреждений', 'Требует ремонта'):
                        if message == runQuery(f"SELECT damage FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                            query = f"UPDATE keyboard_user SET damage = NULL WHERE user_id = {usid};"
                            runQuery(query)
                        else:
                            query = f"UPDATE keyboard_user SET damage = \"{message}\" WHERE user_id = {usid};"
                            runQuery(query)
                        user_keyboard.settings_keyboard()
                    elif message in ['Собственник', 'Частник', 'Компания']:
                        if message == runQuery(f"SELECT owner FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                            query = f"UPDATE keyboard_user SET owner = NULL WHERE user_id = {usid};"
                            runQuery(query)
                        else:
                            query = f"UPDATE keyboard_user SET owner = \"{message}\" WHERE user_id = {usid};"
                            runQuery(query)
                        user_keyboard.settings_keyboard()
                    elif message == 'START':
                        user_keyboard.firstMenu()
                    elif message == 'Не отслеживать🙈':
                        query = (f"UPDATE offers_to_users SET follow = 0 WHERE user_id = {usid};")
                        runQuery(query)
                        sendMessage(usid, 'Вы больше не отслеживаете новые предложения')
                    elif message == 'Отправить ссылку с параметрами⚙':
                        user_keyboard.sellPositionInBD('/query')
                        user_keyboard.emptyKeyboard('Отправьте ссылку со своими параметрами')
                    elif 'drom.ru' in message and '.html' not in message and message != 'https://www.drom.ru/'\
                            and "/query" in \
                                runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                        if requests.get(message).status_code == 200:
                            user_keyboard.emptyKeyboard('Пожалуйста подождите. Скорость ответа зависит от всего предложенного ассортимента')
                            if orExist(usid) == -2:
                                label_follow = 0
                            else:
                                label_follow = labelFollow(usid)
                            print(deleteTableUser(usid))
                            bh.method('messages.send',
                                      {'user_id': usid, 'message': 'Предложения:', 'random_id': 0,
                                       'template': createCarousel(
                                           parceInBd(linkCorrection(message), usid, label_follow, 20))})
                            user_keyboard.requestsMenu()
                        else:
                            sendMessage(usid, 'Url не действителен')
                    elif message == 'Отслеживать🙉':
                        if orExist(usid) != 0:
                            sendMessage(usid, 'Вы не можете использовать функцию \"Отслеживать🙉'
                                                                   '\" если не обозначили конкретный ассортимент автомобилей'
                                                                   ' через \"Отправить ссылку с параметрами⚙"')
                        elif runQuery(f"SELECT DISTINCT follow FROM offers_to_users WHERE user_id = {usid};")[0][0] != 0:
                            sendMessage(usid, 'Вы уже отслеживаете новые предложения')
                        else:
                            sendMessage(usid, 'Теперь вы отслеживаете новые предложения👍🏻')
                            query = (f"UPDATE offers_to_users SET follow = 1 WHERE user_id = {usid};")
                            runQuery(query)
                    elif message == '':
                        info_message = bh.method("messages.getById", {"message_ids": event.message_id})
                        try:
                            link = info_message['items'][0]['attachments'][0]['link']['url']
                        except IndexError:
                            link = 0
                        if link != 0:
                            if 'drom.ru' in link and '.html' not in link and link != 'https://www.drom.ru/' \
                                and "/query" in \
                                runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                                if requests.get(link).status_code == 200:
                                    user_keyboard.emptyKeyboard(
                                        'Пожалуйста подождите. Скорость ответа зависит от всего предложенного ассортимента')
                                    if orExist(usid) == -2:
                                        label_follow = 0
                                    else:
                                        label_follow = labelFollow(usid)
                                    deleteTableUser(usid)
                                    bh.method('messages.send',
                                              {'user_id': usid, 'message': 'Предложения:', 'random_id': 0,
                                               'template': createCarousel(
                                                   parceInBd(linkCorrection(link), usid, label_follow, 20))})
                                    user_keyboard.requestsMenu()
                                else:
                                    sendMessage(usid, 'Url не действителен')
                            else:
                                sendMessage(usid, 'Url не действителен')
                        elif regionNumber(info_message) > 0:
                            url = f"https://auto.drom.ru/region{regionNumber(info_message)}/used/all/"
                            user_keyboard.emptyKeyboard('Пожалуйста, подождите')
                            bh.method('messages.send',
                                      {'user_id': usid, 'message': 'Предложения:', 'random_id': 0,
                                       'template': createCarousel(getOffers(url))})
                            user_keyboard.firstMenu()
                        else:
                            sendMessage(usid, "Упс! вашего региона нет на drom.ru")
                    elif message.isdigit() and 'desired_price' in runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                        runQuery(f"UPDATE keyboard_user SET price = {int(message)} WHERE user_id = {usid};")
                        user_keyboard.settings_keyboard()
                    elif message.isdigit() and 'desired_mileage' in runQuery(f"SELECT position FROM keyboard_user WHERE user_id = {usid}")[0][0]:
                        runQuery(f"UPDATE keyboard_user SET mileage = {int(message)} WHERE user_id = {usid};")
                        user_keyboard.settings_keyboard()
                    else:
                        message = message.replace(' ', '+')
                        bh.method('messages.send',
                                  {'user_id': usid, 'message': 'Предложения:', 'random_id': 0,
                                   'template': createCarousel(getOffers(f'https://auto.drom.ru/used/all/?keywords={message}'))})
        except vk_api.ApiError:
            print('vk_api.ApiError')
            continue
        except requests.exceptions.RequestException:
            print('requests.exceptions.RequestException')
            continue
        except urllib3.exceptions.ReadTimeoutError:
            print('urllib3.exceptions.ReadTimeoutError')
            continue
        except socket.timeout:
            print('socket.timeout')
            continue
