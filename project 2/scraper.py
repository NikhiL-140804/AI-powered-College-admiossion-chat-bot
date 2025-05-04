import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversityScraper:
    def __init__(self):
        self.base_url = "https://kanchiuniv.ac.in"
        self.base_domain = urlparse(self.base_url).netloc
        self.mongo_client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.db = self.mongo_client['university_db']
        self.visited_urls = set()
        self.to_visit = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.max_retries = 3
        self.retry_delay = 5
        
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            # Allow all URLs from the same domain
            return parsed.netloc == self.base_domain
        except:
            return False

    def get_page(self, url):
        """Get page content with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None

    def extract_content(self, soup, url):
        """Extract relevant content from the page"""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style']):
            element.decompose()
            
        # Extract main content
        content = {
            'url': url,
            'title': soup.title.string.strip() if soup.title else '',
            'text_content': soup.get_text(separator=' ', strip=True),
            'last_updated': datetime.now(),
            'links': [],
            'headings': [],
            'paragraphs': [],
            'metadata': {}
        }
        
        # Extract metadata
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                content['metadata'][meta['name']] = meta.get('content', '')
            if meta.get('property'):
                content['metadata'][meta['property']] = meta.get('content', '')
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            content['headings'].append(heading.get_text(strip=True))
            
        # Extract paragraphs
        for para in soup.find_all('p'):
            text = para.get_text(strip=True)
            if text:
                content['paragraphs'].append(text)
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            if self.is_valid_url(absolute_url):
                content['links'].append({
                    'url': absolute_url,
                    'text': link.get_text(strip=True)
                })
        
        return content

    def process_page(self, url):
        """Process a single page"""
        if url in self.visited_urls:
            return
            
        logger.info(f"Processing: {url}")
        self.visited_urls.add(url)
        
        html_content = self.get_page(url)
        if not html_content:
            return
            
        soup = BeautifulSoup(html_content, 'lxml')
        content = self.extract_content(soup, url)
        
        # Store in MongoDB
        self.db.pages.update_one(
            {'url': url},
            {'$set': content},
            upsert=True
        )
        
        # Add new links to visit
        for link in content['links']:
            new_url = link['url']
            if new_url not in self.visited_urls and new_url not in self.to_visit:
                self.to_visit.add(new_url)

    def crawl(self, start_url=None):
        if not start_url:
            start_url = self.base_url
            
        self.to_visit.add(start_url)
        processed_count = 0
        
        while self.to_visit:
            # Process multiple pages concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for url in list(self.to_visit)[:10]:  # Process up to 10 URLs at a time
                    self.to_visit.remove(url)
                    futures.append(executor.submit(self.process_page, url))
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error processing page: {str(e)}")
            
            processed_count += 10
            logger.info(f"Processed {processed_count} pages. {len(self.to_visit)} pages remaining.")
            
            # Be nice to the server
            time.sleep(1)

    def get_all_data(self):
        """Retrieve all scraped data from MongoDB"""
        return list(self.db.pages.find({}, {'_id': 0}))

def main():
    scraper = UniversityScraper()
    logger.info("Starting scraping process...")
    scraper.crawl()
    logger.info("Scraping completed!")
    
    # Print summary
    total_pages = len(scraper.visited_urls)
    logger.info(f"Total pages scraped: {total_pages}")
    
    # Example: Get all data
    all_data = scraper.get_all_data()
    logger.info(f"Total documents in database: {len(all_data)}")

if __name__ == "__main__":
    main() 