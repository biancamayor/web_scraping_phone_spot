import requests
import os
import pandas as pd
import threading
import queue
import random
import time
from utils.json_functions import load_json_file
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv


load_dotenv()
dynamic_proxies_list = load_json_file(os.getenv('credentials_path'))[1]['proxies']
def get_random_proxy():
    return random.choice(dynamic_proxies_list)

class Americanas():
    """Classe para realizar webScraping no site da Americanas."""
    
    def __init__(self, url, headers, num_threads):
        self.url = url
        self.headers = headers
        self.num_threads = num_threads
        self.products_links_queue = queue.Queue()
        self.codes_dict = {}
        self.codes_lock = threading.Lock()
        self.brand_dict = {}
        self.brand_lock = threading.Lock()
        self.all_rows = []
        self.limit = 24
        self.offset = 0
        self.page = 1
        self.amount_of_products = 840 #30 Páginas

    def get_products(self, soup):
        """Extrai informações de título, preço e link de produtos da página."""
        products = soup.findAll('div', attrs={'class':'col__StyledCol-sc-1snw5v3-0 qYCYL theme-grid-col'})

        for p in products:
            title = p.find('h3', attrs={'class':'styles__Name-sc-1e4r445-0 fYqJrQ product-name'}).text
            price_element = p.find('span', attrs={'class':'src__Text-sc-154pg0p-0 styles__PromotionalPrice-sc-yl2rbe-0 dthYGD list-price'})
            
            if price_element:
                price_str = price_element.text.strip()
                price = float(price_str.replace('.', '').replace(',', '.').replace('R$', ''))
                base_url = p.find('a', attrs={'aria-current':'page'})['href']
                individual_link = "https://www.americanas.com.br" + base_url

                self.all_rows.append({'title': title, 'price': price, 'link': individual_link})
                self.products_links_queue.put(individual_link)

    def get_brand(self, link, soup):
        """Extrai a marca do produto a partir da página do link."""
        try:
            tag_brand = soup.find('td', text='Marca')
            if tag_brand:
                brand = tag_brand.find_next('td').text.strip()
                with self.brand_lock:
                    self.brand_dict[link] = brand
            else:
                brand = None
        except Exception as e:
            print(f"Erro ao processar a marca no link {link}: {e}")
            brand = None
        return self.brand_dict

    def get_anatel_code(self, link, iterator):
        """Extrai o código ANATEL do produto a partir da página."""
        try:
            tag_code = iterator.find_next('td', class_='spec-drawer__Text-sc-jcvy3q-5 fMwSYd')
            code = tag_code.text.replace('-', '') if tag_code else None
            with self.codes_lock:
                self.codes_dict[link] = code
        except Exception as e:
            print(f"Erro ao processar {link}: {e}")
        return self.codes_dict

    def get_anatel_code_and_brand(self, link):
        """Função principal para extrair código ANATEL e marca de um link."""
        try:
            proxy = get_random_proxy()
            request = requests.get(link, headers=self.headers, proxies=proxy)
            soup = BeautifulSoup(request.content, 'html.parser')
            
            html_tag = soup.find_all('td', class_='spec-drawer__Text-sc-jcvy3q-5 fMwSYd')
            code = None
            brand = None
            
            for tag in html_tag:
                if any(substring in tag.get_text(strip=True) for substring in ['Código de homologação (Anatel', 'Codigo Homolog (ANATEL)']):
                    code = self.get_anatel_code(link=link, iterator=tag)
                
                if 'Marca' in tag.get_text(strip=True):
                    brand = self.get_brand(link=link, soup=soup)

            return code, brand
        
        except Exception as e:
            print(f"Erro ao processar {link}: {e}")
            return None, None  

    def next_page(self, soup):
        """Verifica se há uma próxima página para navegar."""
        next_button = soup.find('a', {'class':'src__PageLink-sc-82ugau-3 exDCiw'})
        return f'&page={self.page + 1}&limit={self.limit}&offset={self.offset}' if next_button else None

    def main(self):
        """Função principal para realizar scraping, processar links e extrair dados."""
        while True:
            current_url = f"{self.url}&page={self.page}&limit={self.limit}&offset={self.offset}"
            proxy = get_random_proxy()
            request = requests.get(current_url, headers=self.headers, proxies=proxy, verify=False)
            time.sleep(3)
            soup = BeautifulSoup(request.content, 'html.parser')

            self.get_products(soup)

            next_params = self.next_page(soup)
            if not next_params or self.offset >= self.amount_of_products:
                break

            self.offset += self.limit
            self.page += 1

        # Usando ThreadPoolExecutor para processar os links em paralelo
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            while not self.products_links_queue.empty():
                link = self.products_links_queue.get()
                executor.submit(self.get_anatel_code_and_brand, link)

        # Criando DataFrame e processando os resultados
        df_americanas = pd.DataFrame(self.all_rows)
        df_americanas['code'] = df_americanas['link'].map(self.codes_dict)
        df_americanas['brand'] = df_americanas['link'].map(self.brand_dict)
        
        # Filtrando valores nulos e inválidos
        df_americanas = df_americanas.dropna(subset=['code'])
        df_americanas = df_americanas[df_americanas['code'] != 'Null']
        
        df_americanas = df_americanas.dropna(subset=['price'])
        df_americanas = df_americanas[df_americanas['price'] > 0]

        return df_americanas


    
    def americanas_mercado_livre_matching_codes(self, df_mercadoLivre, df_americanas):
        """
        Verifica quais são os códigos anatel em comum no dataframe mercado Livre e Americanas.
        Os códigos em comum serão adicionados a uma lista nomeada matching_codes.
        O dataframe americanas será sobescrito e passará a ter apenas os produtos que também existem
        no dataframe mercado livre.
        
            Parâmetros:
                    df_mercadoLivre (pd.Dataframe): Dataframe do mercado livre
                    df_americanas (pd.Dataframe): Dataframe da americanas.
            
            Retorno:
                    df_americanas (pd.dataframe): Dataframe americanas sobescrito com códigos em comum entre os dois.
        """

        ml_codes = df_mercadoLivre['codigo'].astype(str).tolist()

        matching_codes = []
        for k,v in self.codes_dict.items():
            if v in ml_codes:
                matching_codes.append(v)

        df_americanas = df_americanas[df_americanas['code'].isin(ml_codes)]
        return df_americanas






# import requests
# import pandas as pd
# import threading
# import queue
# from bs4 import BeautifulSoup
# from concurrent.futures import ThreadPoolExecutor

# class Americanas():
#     """Classe para realizar webScraping no site da Americanas."""
    
#     def __init__(self, url, headers, num_threads):
#         self.url = url
#         self.headers = headers
#         self.num_threads = num_threads
#         self.products_links_queue = queue.Queue()
#         self.codes_dict = {}
#         self.codes_lock = threading.Lock()
#         self.brand_dict = {}
#         self.brand_lock = threading.Lock()
#         self.all_rows = []
#         self.limit = 24
#         self.offset = 0
#         self.page = 1
#         self.amount_of_products = 1080   #45 Páginas


#     def get_products(self, soup):
#         """
#         Pega o título, preço e link de todos os produtos existentes na página atual do site.
#         Essas informações são salvas em um dicionário.
#         O link de cada produto é salvo em uma fila (queue) para serem processador por threads futuramente.

#             Parâmetros:
#                     soup: objeto BeautifulSoup
            
#             Retorno:
#                     Atualização dos atributos 'all_rows' e 'products_links_queue', inicialmente criados na função
#                     __init__ da classe.

#         """

#         products = soup.findAll('div', attrs={'class':'col__StyledCol-sc-1snw5v3-0 qYCYL theme-grid-col'})

#         for p in products:
#             title = p.find('h3', attrs={'class':'styles__Name-sc-1e4r445-0 fYqJrQ product-name'}).text
#             price_element = p.find('span', attrs={'class':'src__Text-sc-154pg0p-0 styles__PromotionalPrice-sc-yl2rbe-0 dthYGD list-price'})
            
#             if price_element == None:
#                 break
#             else:
#                 price_str = price_element.text.strip() 
#                 price = price_str.replace('.', '').replace(',', '.').replace('R$', '') 
#                 price = float(price) 

#                 base_url = p.find('a', attrs={'aria-current':'page'})['href']
#                 individual_link = "https://www.americanas.com.br" + base_url

#                 self.all_rows.append({'title': title, 'price': price, 'link': individual_link})
#                 self.products_links_queue.put(individual_link)



#     def get_brand(self, link, soup):
#         try:
#             tag_brand = soup.find('td', text='Marca')
#             if tag_brand:
#                 brand = tag_brand.find_next('td').text.strip()
#                 with self.brand_lock:
#                     self.brand_dict[link] = brand
#             else:
#                 print(f"Marca não encontrada para o link: {link}")
#                 brand = None
#         except Exception as e:
#             print(f'Erro ao processar a marca no link {link}: {e}')
#             brand = None

#         return self.brand_dict



#     def get_anatel_code(self, link, iterator):
#         """Função para pegar o código anatel de cada produto capturado pelo getProducts.
#         O código anatel será utilizado como um id único para cada produto.
#             Parâmetros:
#                     link (str): Link para o produto do qual pegaremos o código anatel.
#                     iterator: Iterador que percorre cada link
#             Retorno:
#                     codes_dict (dict): Dicionário com o código anatel relacionado a cada link.
#         """
#         try:
#             tag_code = iterator.find_next('td', class_='spec-drawer__Text-sc-jcvy3q-5 fMwSYd')
#             code = tag_code.text.replace('-', '') if tag_code != None else None
#             with self.codes_lock:
#                 self.codes_dict[link] = code

#         except Exception as e:
#             print(f'Erro ao processar {link}: {e}')

#         return self.codes_dict


#     def get_anatel_code_and_brand(self, link):
#         try:
#             request = requests.get(link, headers=self.headers)
#             soup = BeautifulSoup(request.content, 'html.parser')
            
#             html_tag = soup.find_all('td', class_='spec-drawer__Text-sc-jcvy3q-5 fMwSYd')
            
#             code = None
#             brand = None
            
#             for tag in html_tag:
#                 if any(substring in tag.get_text(strip=True) for substring in ['Código de homologação (Anatel', 'Codigo Homolog (ANATEL)']):
#                     code = self.get_anatel_code(link=link, iterator=tag)
                
#                 if 'Marca' in tag.get_text(strip=True):  
#                     brand = self.get_brand(link=link, soup=soup)  

#             return code, brand
        
#         except Exception as e:
#             print(f'Erro ao processar {link}: {e}')
#             return None, None  
        



#     def next_page(self, soup):
#         """
#         Realiza a troca de página do site, tornando possível o getProducts pegar produtos de páginas
#         diferentes.
#            Retorna 'None' quando não encontrar mais o botão para mudar de página.
        
#             Parâmetros:
#                     soup: Objeto BeautifulSoup
            
#             Retorno:
#                     Link para a próxima página.
#         """

#         next_button = soup.find('a', {'class':'src__PageLink-sc-82ugau-3 exDCiw'})
#         return f'&page={self.page + 1}&limit={self.limit}&offset={self.offset}' if next_button else None




#     def main(self):
#         """
#         Função principal, responsável por chamar e conectar todas as outras funções.
#         Aqui, ocorre a chamada das threads e a passagem de parâmetros para as funções.

#             Retorno:
#                     df_americanas (pd.Dataframe): Dataframe com as informações de cada produto.
#         """

#         while True:
#             current_url = f"{self.url}&page={self.page}&limit={self.limit}&offset={self.offset}"
#             print(f'current_url = {current_url}')
#             request = requests.get(current_url, headers=self.headers)
#             soup = BeautifulSoup(request.content, 'html.parser')

#             self.get_products(soup = soup)

#             next_params = self.next_page(soup)
#             if not next_params or self.offset == self.amount_of_products: #20 páginas
#                 break

#             self.offset += self.limit
#             self.page += 1


#         with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
#             while not self.products_links_queue.empty():
#                 link = self.products_links_queue.get()
#                 executor.submit(self.get_anatel_code_and_brand, link)


#         df_americanas = pd.DataFrame(self.all_rows)

#         df_americanas['code'] = df_americanas['link'].map(self.codes_dict)
#         df_americanas['brand'] = df_americanas['link'].map(self.brand_dict)

#         df_americanas = df_americanas.dropna(subset=['code'])
#         df_americanas = df_americanas[df_americanas['code'] != 'Null'] 
        
#         df_americanas = df_americanas.dropna(subset=['price'])
#         df_americanas = df_americanas[df_americanas['price'] > 0]

#         return df_americanas


#     def americanas_mercado_livre_matching_codes(self, df_mercadoLivre, df_americanas):
#         """
#         Verifica quais são os códigos anatel em comum no dataframe mercado Livre e Americanas.
#         Os códigos em comum serão adicionados a uma lista nomeada matching_codes.
#         O dataframe americanas será sobescrito e passará a ter apenas os produtos que também existem
#         no dataframe mercado livre.
        
#             Parâmetros:
#                     df_mercadoLivre (pd.Dataframe): Dataframe do mercado livre
#                     df_americanas (pd.Dataframe): Dataframe da americanas.
            
#             Retorno:
#                     df_americanas (pd.dataframe): Dataframe americanas sobescrito com códigos em comum entre os dois.
#         """

#         ml_codes = df_mercadoLivre['codigo'].astype(str).tolist()

#         # matching_codes = []
#         # for k,v in self.codes_dict.items():
#         #     if v in ml_codes:
#         #         matching_codes.append(v)

#         df_americanas = df_americanas[df_americanas['code'].isin(ml_codes)]
#         return df_americanas



    



