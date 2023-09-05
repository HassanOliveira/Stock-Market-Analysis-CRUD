from bs4 import BeautifulSoup
import requests


def get_news():
    url = "https://economia.uol.com.br/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    noticias = soup.find_all("div")
    tgt_class = "thumbnail-standard-wrapper"
    news_dict = {}

    for noticia in noticias:
        if noticia and noticia.get("class"):
            if tgt_class in noticia.get("class"):
                h2_tag = noticia.find("h2")
                if h2_tag:
                    news_title = h2_tag.text.strip()
                    news_url = noticia.a.get("href").replace(
                        "http://economia.uol.com.br", ""
                    )
                    image_url = noticia.a.figure.div.img.get("data-src")
                    news_dict[news_title] = {"url": news_url, "image_url": image_url}

    return news_dict


def get_news_individual(noticia_url):
    base_url = "http://economia.uol.com.br"
    full_url = base_url + noticia_url

    page = requests.get(full_url)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("h1").text.strip()

    div0_elements = soup.select('div[data-metric-area="topo-noticia"] p.bullet.mt-0')
    div0 = []
    if div0_elements:
        for div_element in div0_elements:
            div = div_element.get_text()
            div0.append(div)
            next_element = div_element.find_next()
            if (
                next_element
                and next_element.name == "h2"
                and "bullet" in next_element.get("class", [])
            ):
                break
    else:
        div0 = None

    div1_elements = soup.select(
        'div[data-metric-area="topo-noticia"] p.bullet:not(.mt-0)'
    )
    div1 = []
    if div1_elements:
        for div_element in div1_elements:
            div = div_element.get_text()
            div1.append(div)
            next_element = div_element.find_next()
            if next_element and (
                (
                    next_element.name == "h2"
                    and "bullet" in next_element.get("class", [])
                )
                or (
                    next_element.name == "p"
                    and "bullet.mt-0" in next_element.get("class", [])
                )
            ):
                break
    else:
        div1 = None

    subtitle1_elements = soup.select('div[data-metric-area="topo-noticia"] h2.bullet')
    subtitle1 = []
    if subtitle1_elements:
        for subtitle_element in subtitle1_elements:
            subtitle = subtitle_element.get_text()
            subtitle1.append(subtitle)
    else:
        subtitle1 = None

    div2_elements = soup.select('div[data-metric-area="texto-noticia"] p.bullet.mt-0')
    div2 = []
    if div2_elements:
        div = div2_elements[0].get_text()
        div2.append(div)
    else:
        div2 = None

    div3_elements = soup.select(
        'div[data-metric-area="texto-noticia"] p.bullet:not(.mt-0)'
    )
    div3 = []
    if div3_elements:
        for div_element in div3_elements:
            div = div_element.get_text()
            div3.append(div)
            next_element = div_element.find_next()
            if next_element and (
                (
                    next_element.name == "h2"
                    and "bullet" in next_element.get("class", [])
                )
                or (
                    next_element.name == "p"
                    and "bullet.mt-0" in next_element.get("class", [])
                )
            ):
                break
    else:
        div3 = None

    subtitle2_elements = soup.select('div[data-metric-area="texto-noticia"] h2.bullet')
    subtitle2 = []
    if subtitle2_elements:
        for subtitle_element in subtitle2_elements:
            subtitle = subtitle_element.get_text()
            subtitle2.append(subtitle)
    else:
        subtitle2 = None

    news_info = {
        "title": title,
        "div0": div0,
        "div1": div1,
        "subtitle1": subtitle1,
        "div2": div2,
        "div3": div3,
        "subtitle2": subtitle2,
    }

    return news_info
