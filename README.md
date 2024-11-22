# 📊 **Web Scraping de Preços de Celulares**  

Este é um projeto de **web scraping** desenvolvido para coletar informações detalhadas sobre celulares disponíveis nos sites **Mercado Livre** e **Americanas**. O objetivo é criar uma base de dados robusta com informações como preço, marca, nome, código Anatel e link para o produto, que podem ser utilizadas para análises, APIs e interfaces visuais.  

---

## 🔍 **O que o projeto faz?**  
O projeto acessa automaticamente as páginas de produtos desses marketplaces, extrai informações relevantes e organiza tudo em um banco de dados relacional para fácil acesso e manipulação. Ele foi projetado para ser eficiente, modular e capaz de lidar com grandes volumes de dados.  

As informações extraídas incluem:  
- 📱 Nome do celular.  
- 💲 Preço.  
- 🏷️ Marca.  
- 🆔 Código Anatel.  
- 🔗 Link para o produto.  

---

## 🛠️ **Tecnologias Utilizadas**  
- **Python**: Linguagem principal.  
- **BeautifulSoup**: Para análise e extração de dados HTML.  
- **Requests**: Para realizar as requisições HTTP.  
- **Threads em Python**: Para otimizar a coleta de dados, permitindo múltiplas requisições simultâneas.  
- **Banco de dados relacional**: Para armazenamento dos dados coletados.  

---

## ⚙️ **Como funciona?**  
1. **Mapeamento das Páginas**: O script percorre as categorias e produtos das lojas Mercado Livre e Americanas.  
2. **Extração de Dados**: Utilizando BeautifulSoup, os dados relevantes são capturados diretamente do HTML das páginas.  
3. **Tratamento dos Dados**: Informações como preço e nome são padronizadas e organizadas.  
4. **Armazenamento**: Os dados são salvos em um banco de dados relacional para uso posterior.  

---

## 🔒 **Notas de Segurança**
As credenciais de acesso e variáveis de ambiente não são expostas no repositório. É necessário fornecer seus próprios arquivos para rodar o container.

---

## 🚀 **Como executar o projeto?**  
### Pré-requisitos   
- Bibliotecas listadas no arquivo `requirements.txt`.  
- Acesso a um banco de dados relacional. No projeto, utilizei o Tembo.


### Passos:  
1. Clone o repositório:  
   ```bash
   git clone https://github.com/biancamayor/web_scraping_phonespot.git
   cd web_scraping_phonespot

2. Instale as dependências:
    ```bash
    pip install -r requirements.txt

3. Configure o acesso ao banco de dados:
    - Crie um arquivo .env com uma variável chamada **credentials_path**. Essa variável irá armazenar o caminho para o seu arquivo de credenciais do banco de dados.

    - Crie um arquivo chamado **credentials.json**. Esse arquivo conterá suas credenciais para o banco de dados, além de uma lista de proxies dinâmicos para a requisição não ser barrada por anti-bots dos sites do Mercado Livre e Americanas e, por fim, um dicionário contendo um headers que simula um acesso humano aos sites, evitando barramento.

    ```bash
    [   {"host": host,
        "database": database,
        "user": user,
        "password": password},

        {"proxies":[
            {"http": proxy_1},
            {"http": proxy_2},
            {"http": proxy_3}
            ]
        },

        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": Language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    ]
    ```

---

# 🌟 **Destaques do Projeto**
- Performance aprimorada: Uso de threads para acelerar o processo de coleta de dados.
- Flexibilidade: O código é modular, facilitando a adaptação para novos sites ou categorias de produtos.
- Dados ricos: Informações detalhadas e organizadas em um formato fácil de consumir.

---

# **API com os dados do Web Scraping**
- Desenvolvi também uma API que utiliza os dados coletados pelo web scraping e fornece diversos endpoints para uso dos dados. O projeto também conta com uma interface visual construída com data app. Fique a vontade para conhecer o projeto:

- <a href="https://github.com/biancamayor/api_phonespot.git" target="_blank">API PhoneSpot</a>

---

## 📞 **Contato**
Para mais informações ou dúvidas, entre em contato:

- <a href="https://linkedin.com/in/bianca-mayor" target="_blank">LinkedIn</a>
- **E-mail**: biancamayor@hotmail.com



