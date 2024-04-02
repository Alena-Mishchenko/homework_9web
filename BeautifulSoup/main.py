
import requests
from bs4 import BeautifulSoup
import json
import os
from mongoengine import connect
from models import Author, Quote
from mongoengine.errors import NotUniqueError


current_directory = os.path.dirname(os.path.abspath(__file__))
connect(
    db="homework8",
    host="mongodb+srv://goitlearn:mypas@cluster0.nlahlds.mongodb.net/?retryWrites=true&w=majority",
)

base_url = 'http://quotes.toscrape.com/'

def get_author_data(base_url, author_url):
    response = requests.get(f"{base_url}{author_url}")
    soup = BeautifulSoup(response.text, 'html.parser')

    fullname = soup.find('h3', class_='author-title').text.strip()
    born_date = soup.find('span', class_='author-born-date').text.strip()
    born_location = soup.find('span', class_='author-born-location').text.strip()
    description = soup.find('div', class_='author-description').text.strip()

    return {
        'fullname': fullname,
        'born_date': born_date,
        'born_location': born_location,
        'description': description
    }
def scrape_quotes(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    quotes_data = []
    authors_data = []
    quotes = soup.select('div.quote')
    for quote in quotes:
        quote_text = quote.find('span', class_='text').text.strip()
        tags = [tag.text for tag in quote.find_all('a', class_='tag')]
        author_name = quote.find('small', class_='author').text.strip()
        author_link = quote.find('a', href=lambda href: href and href.startswith('/author/'))
        if author_link:
            author_url = author_link['href']
            author_data = get_author_data(base_url, author_url)
            authors_data.append(author_data)

        quotes_data.append({
                'tags': tags,
                'author': author_name,
                'quote': quote_text
            })
    
    return quotes_data, authors_data    

        
if __name__ == '__main__':
    current_page = 1
    all_quotes_data = []
    all_authors_data = []
    while True:
        url = f"{base_url}/page/{current_page}/"
        quotes_data, authors_data = scrape_quotes(url)
        all_quotes_data.extend(quotes_data)
        all_authors_data.extend(authors_data)
        if not quotes_data:
            break  
        current_page += 1
    authors_file_path = os.path.join(current_directory, 'authors.json')
    quotes_file_path = os.path.join(current_directory, 'quotes.json')
     
    with open(quotes_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_quotes_data, f, ensure_ascii=False, indent=2)
    
    with open(authors_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_authors_data, f, ensure_ascii=False, indent=2)
   
        for author_data in all_authors_data:
            try:
                author = Author(**author_data)
                author.save()
            except NotUniqueError:
                print(f"The author {author_data['fullname']} already exists")
 
        for quote_data in all_quotes_data:
            author_name = quote_data['author']
            author = Author.objects(fullname=author_name).first()
            if author:
                quote_data['author'] = author
                quote = Quote(**quote_data)
                quote.save()
            else:
                print(f"Author {author_name} not found")





