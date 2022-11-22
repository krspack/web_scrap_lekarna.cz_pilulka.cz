
# https://github.com/krspack/web_scrap_lekarna.cz_pilulka.cz


import requests
from bs4 import BeautifulSoup as bs
import json
import re
import csv

all_data_list = []

current_weight = int(input('Jaka je aktualni hmotnost ditete (kg, int)? '))



# lekarnacz:

def lekarnacz_weight(input_text):
    weight_pattern = re.compile("((?P<od>\d+)[^\d]*(kg)?(-|–|až)\s*)?(?P<do>\d+)[^\d]*kg")
    weight = re.search(weight_pattern, input_text)
    number_pattern = re.compile("\d+")
    weight_numbers = re.findall(number_pattern, str(weight))
    weight_numbers = [int(i) for i in weight_numbers]
    weight_numbers.pop(0)
    weight_numbers.pop(0)
    if len(weight_numbers) == 1:
            if weight_numbers[0] > 10:
                weight_numbers.append(100)
            else:
                weight_numbers.insert(0, 0)
    weight_numbers = [int(x) for x in weight_numbers]
    return weight_numbers

def lekarnacz_package_size(input_text):
    ks_pattern = re.compile("....ks|....kusů|....Kusů|....Plenek|....plenek")
    ks = re.findall(ks_pattern, input_text)
    ks_num_pattern = re.compile("\d+")
    ks_num = re.findall(ks_num_pattern, str(ks))
    if len(ks_num) > 0:
        ks_num = [int(i) for i in ks_num][0]
        return ks_num
    return 0

def lekarna_get_price(product):
    price = set()
    for child in product.descendants:
        if child.string != None:
            if 'Kč' in child.string and 'kus' not in child.string:
                p = (child.string).replace('Kč', '')
                p = p.replace(' ', '')
                price.add(int(p))
                price = max(price)
                return price
    return 0  # vyprodane polozky

def get_lek_urls(input_kg):
    lek_sizes = {0: [0, 3], 1:[2, 5], 2:[3, 6], 3:[4, 10], 4:[7, 18], 5:[11, 26], 6:[15, 100]}
    sizes = []
    urls = []
    for k, v in lek_sizes.items():
        if v[0] <= input_kg <= v[1]:
            sizes.append(k)

    for size in sizes:
        url = 'https://www.lekarna.cz/plenky-{}/?razeni=price-desc'.format(size)
        website = requests.get(url)
        web_html = website.content
        web_soup = bs(web_html, "html.parser")

        all_pages = []
        next_page_buttons = web_soup.find_all('li', attrs = {'class': 'flex items-center mx-1'})
        for button in next_page_buttons:
            for child in button.children:
                if child.string.strip() != '':
                    all_pages.append(child.string.strip())
                    all_pages = [int(x) for x in all_pages]
        try:
            for i in range(1, max(all_pages) + 1):
                urls.append('https://www.lekarna.cz/plenky-{}/?strana={}&razeni=price-desc'.format(size, i))
        except ValueError:
            pass
    return urls

def get_default_weight_range(size):
    lek_sizes = {0: [0, 3], 1:[2, 5], 2:[3, 6], 3:[4, 10], 4:[7, 18], 5:[11, 26], 6:[15, 100]}
    return lek_sizes.get(size)

def get_size_from_url(url):
    url_pattern = re.compile('plenky-\d')
    url_size = re.findall(url_pattern, url)[0]
    number = re.findall('\d', url_size)
    return int(number[0])

def lekarna_get_product_url(product):
    product_data = list(product.children)[1]
    href_lek = product_data.attrs["href"]
    href_lek_abs = "https://www.lekarna.cz/"+href_lek
    return href_lek_abs

def lekarna_get_product_description(product):
    product_data = list(product.children)[1]
    gtm = product_data.attrs["data-gtm"]
    gtm_dict = json.loads(gtm)
    description = gtm_dict["ecommerce"]["click"]["products"][0]["product_name"]
    return description

def lek_add_data(all_data = all_data_list):
    urls = get_lek_urls(current_weight)
    for url in urls:
        website = requests.get(url)
        html = website.content
        soup = bs(html, "html.parser")
        products = soup.find_all('div', attrs = {'class': 'relative flex flex-col items-stretch transition-shadow duration-150 ease-in-out group'
        ' flex-wrap w-full md:border md:border-transparent md:rounded-lg md:hover:border-gray-300 md:hover:shadow-md will-change-transform'})

        for product in products:
            description = lekarna_get_product_description(product)
            price = lekarna_get_price(product)
            product_url = lekarna_get_product_url(product)
            package_size = lekarnacz_package_size(description)
            if "kg" in description:
                weight_numbers = lekarnacz_weight(description)
            else:
                size = get_size_from_url(url)
                weight_numbers = get_default_weight_range(size)

            if price > 0 and package_size > 1:
                all_data.insert(0,{"website": url, "product": description, "price": price, "weight_from": weight_numbers[0], "weight_to": weight_numbers[1], "pieces in package": package_size, "price per piece": round(price/package_size, 2), "url": product_url})


# pilulkacz:

def get_pil_urls(input_kg = current_weight):
    pil_size_chart = {0: [0, 3], 1:[3, 5], 2:[4, 8], 3:[6, 10], 4:[9, 14], 5:[12, 17], 6:[15, 100], 7:[17, 100]}
    sizes = []
    urls = []
    for k, v in pil_size_chart.items():
        if v[0] <= input_kg <= v[1]:
            sizes.append(k)
    for size in sizes:
        urls.append('https://www.pilulka.cz/plenky-{}/nejkvalitnejsi'.format(size))
    return urls

def pil_get_product_description(input_tag):
    desc = input_tag.get_text()
    sleva_pattern = re.compile("Sleva \d+ \%")
    sleva = re.findall(sleva_pattern, desc)
    for sl in sleva:
        desc = desc.replace(sl, "")
        desc = desc.strip()
    return desc

def pil_get_package_size(description):
    ks_pattern = re.compile('(\d\s*x\s*)?(\d+)\s*(ks|Plenek|plenek)')
    ks = re.findall(ks_pattern, description)
    if len(ks) == 0:
        return 0      # veci chybne zarazene mezi plinky
    else:
        ks = ks[0]
        if len(ks[0]) == 0:    # skoro vsechny
            ks_fin = int(ks[1])
        else:     # typ 2 x 100 ks
            xtimes_pattern = re.compile('\d')
            xtimes = int(re.findall(xtimes_pattern, ks[0])[0])
            ks_fin = xtimes*int(ks[1])
        return ks_fin

def pil_get_size_from_url(url):
    url_pattern = re.compile('plenky-\d')
    url_size = re.findall(url_pattern, url)[0]
    number = int(re.findall('\d', url_size)[0])
    size_chart = {0: [0, 3], 1:[3, 5], 2:[4, 8], 3:[6, 10], 4:[9, 14], 5:[12, 17], 6:[15, 100], 7:[17, 100]}
    return size_chart.get(number)

def pil_get_weight_range(description):
    w_pattern = re.compile('((?P<od>\d+)[^\d]*(kg)?(-|–|až)\s*)?(?P<do>\d+)[^\d]*kg')
    kgs = re.search(w_pattern, description)

    size_pattern = re.compile("(Velikost...|velikost...|Vel....|vel....|S\d{1})")
    size_text = re.findall(size_pattern, description)

    if kgs == None:
        if len(size_text) > 0:
            size_pattern_2 = re.compile('\d+')
            size_list = re.findall(size_pattern_2, size_text[0])
            size_list = [int(size) for size in size_list]
            size_list = size_list[0]
            size_chart = {0: [0, 3], 1:[3, 5], 2:[4, 8], 3:[6, 10], 4:[9, 14], 5:[12, 17], 6:[15, 100], 7:[17, 100]}
            weight_list = size_chart.get(size_list)
        else:
            weight_list = None  # odvodi se z url, ale mimo tuto funkci
    else:
        number_pattern = re.compile("\d+")
        kgs = re.findall(number_pattern, str(kgs))
        kgs = [int(i) for i in kgs]
        kgs.pop(0)
        kgs.pop(0)

        if len(kgs) == 2:
            weight_list = kgs
        if len(kgs) == 1:
            if kgs[0] > 10:
                weight_list = [kgs[0], 100]
            else:
                weight_list = [0, kgs[0]]
    return weight_list

def pil_get_price(f_in_frame):
    pricetags = f_in_frame.find_all("a", attrs={"class": "js-trigger-availability-modal"})
    for pricetag in pricetags:
        price = pricetag.attrs["data-product-price"]
        price = price.replace(" Kč", "")
        price = int(price.replace(" ", ""))
    return price

def pil_add_data(all_data = all_data_list):
    for url in get_pil_urls():
        web_pil = requests.get(url)
        htmlp = web_pil.content
        pil_soup = bs(htmlp, "html.parser")
        frame = pil_soup.select(".product-prev__content")
        for f in frame:
            ahrefs = f.find_all("a", attrs={"class": "product-prev__title"})
            for a in ahrefs:
                href_pil = a.attrs["href"]
                href_pil_abs = "https://www.pilulka.cz/"+href_pil
                desc = pil_get_product_description(a).strip()
                w_list = pil_get_weight_range(desc)
                if w_list == None:
                    w_list = pil_get_size_from_url(url)
                ks_fin = pil_get_package_size(desc)
                price = pil_get_price(f)
                if (price != 0 and ks_fin > 0):
                    all_data.insert(0,{"website": url, "product": desc, "price": price, "weight_from": w_list[0], "weight_to": w_list[1], "pieces in package": ks_fin, "price per piece": round(price/ks_fin, 2), "url": href_pil_abs})



# výběr plenek jen pro danou hmotnost dítěte:

def find_cheapest(baby_weight, all_data = all_data_list):
    lek_add_data()
    pil_add_data()

    rows_selection = []
    for item in all_data:
        if item["weight_from"] <= baby_weight < item["weight_to"]:
            rows_selection.append(item)
    with open('plinky.csv', 'w') as output_csv:
      cols = list(all_data[0].keys())
      output_writer = csv.DictWriter(output_csv, fieldnames=cols)

      output_writer.writeheader()
      for itemm in rows_selection:
        output_writer.writerow(itemm)

    return "tabulka plinky.csv je aktualizovana"

print(find_cheapest(current_weight))