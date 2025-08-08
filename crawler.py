import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from models import db, Page
from app import create_app
from utils import safe_print

def crawl_site(site_id, start_url):
    """
    Crawls a website starting from start_url, finding all internal links,
    and saves the content to the database.
    """
    app = create_app()
    with app.app_context():
        # Using a set to store visited URLs to avoid duplicates and loops
        visited_urls = {page.url for page in Page.query.filter_by(site_id=site_id).all()}
        # Using a list as a queue for URLs to visit
        queue = [start_url]

        # Get the base domain to stay on the same site
        base_domain = urlparse(start_url).netloc

        while queue:
            current_url = queue.pop(0)

            if current_url in visited_urls:
                continue

            safe_print(f"Crawling: {current_url}")

            try:
                response = requests.get(current_url, timeout=5)
                response.raise_for_status() # Raise an exception for bad status codes
            except requests.RequestException as e:
                safe_print(f"Error fetching {current_url}: {e}")
                continue

            visited_urls.add(current_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Save the page to the database
            new_page = Page(url=current_url, content=soup.get_text(), site_id=site_id)
            db.session.add(new_page)

            # Find all links on the page
            for link in soup.find_all('a', href=True):
                absolute_link = urljoin(start_url, link['href'])
                link_domain = urlparse(absolute_link).netloc

                # Check if the link is on the same domain and not visited
                if link_domain == base_domain and absolute_link not in visited_urls:
                    queue.append(absolute_link)

        db.session.commit()
        safe_print(f"Finished crawling for site {site_id}.")
