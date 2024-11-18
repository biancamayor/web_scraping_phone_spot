import requests
import threading
import queue
import pandas as pd
import psycopg2
import html
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor


class MercadoLivre():
    """Classe para realizar webScraping no site do mercado livre."""

    def __init__(self, url, headers, num_threads):
        self.url = url
        self.headers = headers
        self.num_threads = num_threads
        self.products_links_queue = queue.Queue()
        self.codes_lock = threading.Lock()
        self.size = 1
        self.codes_dict = {}
        self.brand_dict = {}
        self.brand_lock = threading.Lock()
        self.all_rows = []
        self.amount_of_products = 1501 #30 páginas


    def get_products(self, soup):
        """
        Pega o título, preço e link de todos os produtos existentes na página atual do site.
        Essas informações são salvas em um dicionário.
        O link de cada produto é salvo em uma fila (queue) para serem processador por threads futuramente.

            Parâmetros:
                    soup: objeto BeautifulSoup

            Retorno:
                    Atualização dos atributos 'all_rows' e 'products_links_queue', inicialmente criados na função
                    __init__ da classe.

        """

        products = soup.findAll('div', attrs={'class':'andes-card ui-search-result ui-search-result--core andes-card--flat andes-card--padding-16'})

        for p in products:
            title = p.find('h2',attrs={'class':'ui-search-item__title ui-search-item__group__element'}).text   
            price_str = p.find('span', attrs={'class':'andes-money-amount__fraction'})
           
            if price_str == None:
                break
            else:
                price_str = price_str.text
                price = price_str.replace('.', '').replace(',', '.').replace('R$', '')
                price = float(price)

                individual_link_tag = p.find('a', attrs={'class':'ui-search-link__title-card ui-search-link'})
                
                if individual_link_tag:
                    individual_link = html.unescape(individual_link_tag['href'])
                    self.all_rows.append({'title': title, 'price': price, 'link': individual_link})
                    self.products_links_queue.put(individual_link)
                else:
                    print("Link do produto não encontrado para:", title)


                self.all_rows.append({'title': title, 'price': price, 'link': individual_link})
                self.products_links_queue.put(individual_link)


    def get_brand(self, link, soup):
        try:
            tag_brand = soup.find('th', text='Marca')
            if tag_brand:
                brand = tag_brand.find_next('td').text.strip()
                with self.brand_lock:
                    self.brand_dict[link] = brand
            else:
                print(f"Marca não encontrada para o link: {link}")
                brand = None
        except Exception as e:
            print(f'Erro ao processar a marca no link {link}: {e}')
            brand = None

        return self.brand_dict



    def get_anatel_code(self, link, iterator):
        """Função para pegar o código anatel de cada produto capturado pelo getProducts.
        O código anatel será utilizado como um id único para cada produto.
            Parâmetros:
                link (str): Link para o produto do qual pegaremos o código anatel.
                iterator: Iterador que percorre cada link
            Retorno:
                codes_dict (dict): Dicionário com o código anatel relacionado a cada link.
        """
        try:
            tag_code = iterator.find_next('span', class_='andes-table__column--value')
            code = tag_code.text.replace('-', '') if tag_code != None else None
            with self.codes_lock:
                self.codes_dict[link] = code

        except Exception as e:
            print(f'Erro ao processar {link}: {e}')

        return self.codes_dict


    def get_anatel_code_and_brand(self, link):
        try:
            request = requests.get(link, headers=self.headers)
            soup = BeautifulSoup(request.content, 'html.parser')

            html_tag = soup.find_all('div', class_='andes-table__header__container')

            code = None
            brand = None

            for tag in html_tag:
                if any(substring in tag.get_text(strip=True) for substring in ['Código de homologação (Anatel', 'Codigo Homolog (ANATEL)', 'Homologação Anatel Nº', 'Número de homologação da Anatel']):
                    code = self.get_anatel_code(link=link, iterator=tag)

                if 'Marca' in tag.get_text(strip=True):  
                    brand = self.get_brand(link=link, soup=soup)  

            return code, brand

        except Exception as e:
            print(f'Erro ao processar {link}: {e}')
            return None, None 



    def next_page(self, soup):
        """
        Realiza a troca de página do site, tornando possível o getProducts pegar produtos de páginas
        diferentes.
           Retorna 'None' quando não encontrar mais o botão para mudar de página.

            Parâmetros:
                    soup: Objeto BeautifulSoup

            Retorno:
                    Link para a próxima página.
        """

        next_button = soup.find('a', {'class':'andes-pagination__link'})
        return f'celular_Desde_{self.size}_NoIndex_True' if next_button else None


    
    def main(self):
        """
        Função principal, responsável por chamar e conectar todas as outras funções.
        Aqui, ocorre a chamada das threads e a passagem de parâmetros para as funções.

            Retorno:
                    df_ml (pd.Dataframe): Dataframe com as informações de cada produto.
        """

        while True:
            current_url = f"{self.url}celular_Desde_{self.size}_NoIndex_True"
            print(f'current_url = {current_url}')
            request = requests.get(current_url, headers=self.headers)
            soup = BeautifulSoup(request.content, 'html.parser')

            self.get_products(soup)

            next_params = self.next_page(soup)
            if not next_params or self.size == self.amount_of_products: 
                break

            self.size += 50

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            while not self.products_links_queue.empty():
                link = self.products_links_queue.get()
                executor.submit(self.get_anatel_code_and_brand, link)

        df_ml = pd.DataFrame(self.all_rows)


        df_ml['code'] = df_ml['link'].map(self.codes_dict)
        df_ml['brand'] = df_ml['link'].map(self.brand_dict)

        df_ml = df_ml.dropna(subset=['code'])
        df_ml = df_ml[df_ml['code'] != 'Null']

        df_ml = df_ml.dropna(subset=['price'])
        df_ml = df_ml[df_ml['price'] > 0]

        return df_ml
       

   
    