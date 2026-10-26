import requests
from bs4 import BeautifulSoup

url = input("Enter a url to scrape : ")

response = requests.get(url)

soup = BeautifulSoup(response.content.__str__(), "html.parser")

print(soup.find("h1"))
print(soup.find("p"))

open("scraped_data.html", "w", encoding="utf-8").write(soup.prettify().__str__())
