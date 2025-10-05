<<<<<<< HEAD
from flask import Flask, jsonify, abort
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import os
from dotenv import load_dotenv
import re 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Function to fetch from Blogger API ---
def fetch_blogger_posts():
    """Fetches and formats posts from the Google Blogger API."""
    BLOG_ID = os.getenv("BLOG_ID")
    API_KEY = os.getenv("BLOGGER_API_KEY")
    if not BLOG_ID or not API_KEY: return []
        
    URL = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        items = response.json().get('items', [])
        posts = []
        for post in items:
            content = post.get('content', '')
            image_match = re.search(r'<img[^>]+src="([^">]+)"', content)
            image_url = image_match.group(1) if image_match else "https://i.imgur.com/OQI44rW.png" # Default image
            
            posts.append({
                "id": post.get('id'),
                "title": post.get('title'),
                "date": post.get('published'),
                "content": content,
                "source": "My Blog (Blogger)",
                "tags": post.get('labels', []),
                "imageUrl": image_url
            })
        return posts
    except Exception as e:
        print(f"Error fetching Blogger API data: {e}")
        return []

# --- Function to fetch from News API ---
def fetch_news_articles():
    """Fetches and formats articles from the News API."""
    API_KEY = os.getenv("NEWS_API_KEY")
    QUERY = os.getenv("NEWS_QUERY")
    if not API_KEY or not QUERY: return []
        
    URL = f"https://newsapi.org/v2/everything?q={QUERY}&sortBy=publishedAt&pageSize=10&apiKey={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        posts = []
        for article in articles:
            source_name = article.get('source', {}).get('name', 'News')
            posts.append({
                "id": article.get('url'),
                "title": article.get('title'),
                "date": article.get('publishedAt'),
                "content": article.get('description'),
                "source": source_name,
                "tags": [source_name],
                "imageUrl": article.get('urlToImage') or "https://i.imgur.com/OQI44rW.png" # Default image
            })
        return posts
    except Exception as e:
        print(f"Error fetching News API data: {e}")
        return []
# Add this function to backend/app.py
def fetch_gnews_articles():
    """Fetches and formats articles from the GNews.io API."""
    API_KEY = os.getenv("GNEWS_API_KEY")
    if not API_KEY: return []
    
    URL = f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&max=10&apikey={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        return [{
            "id": article.get('url'),
            "title": article.get('title'),
            "date": article.get('publishedAt'),
            "content": article.get('description'),
            "source": article.get('source', {}).get('name'),
            "tags": [article.get('source', {}).get('name')],
            "imageUrl": article.get('image') or "https://i.imgur.com/OQI44rW.png"
        } for article in articles]
    except Exception as e:
        print(f"Error fetching GNews.io data: {e}")
        return []

# Add this second function to backend/app.py
def fetch_newsdata_articles():
    """Fetches and formats articles from the NewsData.io API."""
    API_KEY = os.getenv("NEWSDATA_API_KEY")
    if not API_KEY: return []
    
    URL = f"https://newsdata.io/api/1/news?apikey={API_KEY}&language=en&category=technology"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('results', [])
        return [{
            "id": article.get('link'),
            "title": article.get('title'),
            "date": article.get('pubDate'),
            "content": article.get('description'),
            "source": article.get('source_id'),
            "tags": [article.get('source_id')],
            "imageUrl": article.get('image_url') or "https://i.imgur.com/OQI44rW.png"
        } for article in articles]
    except Exception as e:
        print(f"Error fetching NewsData.io data: {e}")
        return []
# REPLACE this entire function in backend/app.py
def fetch_knowivate_articles():
    """Fetches articles from multiple Knowivate API endpoints concurrently."""
    
    # --- Add all the URLs you want to fetch from here ---
    URLS = [
        "https://news.knowivate.com/api/technologies",
        "https://news.knowivate.com/api/business",
        "https://news.knowivate.com/api/science", "https://news.knowivate.com/api/sports","https://news.knowivate.com/api/agriculture"
        # Add more URLs as needed
    ]

    all_articles = []

    def fetch_and_parse(url):
        """Helper function to fetch and parse a single URL."""
        try:
            response = requests.get(url, timeout=10) # Added a timeout
            response.raise_for_status()
            json_response = response.json()
            articles = json_response.get('data', json_response.get('articles', []))
            
            # Format the articles to match our project structure
            return [{
                "id": article.get('url') or article.get('link'),
                "title": article.get('title'),
                "date": article.get('publishedAt') or article.get('pubDate'),
                "content": article.get('summary') or article.get('description'),
                "source": article.get('source', 'Knowivate'),
                "tags": [article.get('source', 'Technology')],
                "imageUrl": article.get('imageUrl') or article.get('image_url') or "https://i.imgur.com/OQI44rW.png"
            } for article in articles]
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            return [] # Return an empty list if an error occurs

    # Use a thread pool to fetch all URLs concurrently
    with ThreadPoolExecutor(max_workers=len(URLS)) as executor:
        results = executor.map(fetch_and_parse, URLS)
        for article_list in results:
            all_articles.extend(article_list)
            
    return all_articles    
# REPLACE this function in backend/app.py
# REPLACE this function in backend/app.py
@app.route('/api/content', methods=['GET'])
def get_all_content():
    # 1. Combine data from ALL API sources, including the new one
    all_content = (fetch_blogger_posts() + 
                   fetch_news_articles() + 
                   fetch_gnews_articles() + 
                   fetch_newsdata_articles() +
                   fetch_knowivate_articles()) # <-- Added new source
    
    # 2. Filter out duplicates
    unique_posts = []
    seen_titles = set()
    for post in all_content:
        if post.get('title') and post['title'].lower() not in seen_titles:
            unique_posts.append(post)
            seen_titles.add(post['title'].lower())
            
    # 3. Safer sorting on the unique list
    unique_posts.sort(key=lambda x: x.get('date') or '', reverse=True)
    
    return jsonify(unique_posts)

# Single post endpoint remains the same
@app.route('/api/content/<path:post_id>', methods=['GET'])
def get_single_content(post_id):
    all_content = load_posts() + fetch_blogger_posts() + fetch_news_articles()
    found_post = next((post for post in all_content if str(post.get('id')) == post_id), None)
    if found_post:
        return jsonify(found_post)
    else:
        abort(404, description="Post not found")

if __name__ == '__main__':
=======
from flask import Flask, jsonify, abort
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import os
from dotenv import load_dotenv
import re 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Function to fetch from Blogger API ---
def fetch_blogger_posts():
    """Fetches and formats posts from the Google Blogger API."""
    BLOG_ID = os.getenv("BLOG_ID")
    API_KEY = os.getenv("BLOGGER_API_KEY")
    if not BLOG_ID or not API_KEY: return []
        
    URL = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        items = response.json().get('items', [])
        posts = []
        for post in items:
            content = post.get('content', '')
            image_match = re.search(r'<img[^>]+src="([^">]+)"', content)
            image_url = image_match.group(1) if image_match else "https://i.imgur.com/OQI44rW.png" # Default image
            
            posts.append({
                "id": post.get('id'),
                "title": post.get('title'),
                "date": post.get('published'),
                "content": content,
                "source": "My Blog (Blogger)",
                "tags": post.get('labels', []),
                "imageUrl": image_url
            })
        return posts
    except Exception as e:
        print(f"Error fetching Blogger API data: {e}")
        return []

# --- Function to fetch from News API ---
def fetch_news_articles():
    """Fetches and formats articles from the News API."""
    API_KEY = os.getenv("NEWS_API_KEY")
    QUERY = os.getenv("NEWS_QUERY")
    if not API_KEY or not QUERY: return []
        
    URL = f"https://newsapi.org/v2/everything?q={QUERY}&sortBy=publishedAt&pageSize=10&apiKey={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        posts = []
        for article in articles:
            source_name = article.get('source', {}).get('name', 'News')
            posts.append({
                "id": article.get('url'),
                "title": article.get('title'),
                "date": article.get('publishedAt'),
                "content": article.get('description'),
                "source": source_name,
                "tags": [source_name],
                "imageUrl": article.get('urlToImage') or "https://i.imgur.com/OQI44rW.png" # Default image
            })
        return posts
    except Exception as e:
        print(f"Error fetching News API data: {e}")
        return []
# Add this function to backend/app.py
def fetch_gnews_articles():
    """Fetches and formats articles from the GNews.io API."""
    API_KEY = os.getenv("GNEWS_API_KEY")
    if not API_KEY: return []
    
    URL = f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&max=10&apikey={API_KEY}"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        return [{
            "id": article.get('url'),
            "title": article.get('title'),
            "date": article.get('publishedAt'),
            "content": article.get('description'),
            "source": article.get('source', {}).get('name'),
            "tags": [article.get('source', {}).get('name')],
            "imageUrl": article.get('image') or "https://i.imgur.com/OQI44rW.png"
        } for article in articles]
    except Exception as e:
        print(f"Error fetching GNews.io data: {e}")
        return []

# Add this second function to backend/app.py
def fetch_newsdata_articles():
    """Fetches and formats articles from the NewsData.io API."""
    API_KEY = os.getenv("NEWSDATA_API_KEY")
    if not API_KEY: return []
    
    URL = f"https://newsdata.io/api/1/news?apikey={API_KEY}&language=en&category=technology"
    try:
        response = requests.get(URL)
        response.raise_for_status()
        articles = response.json().get('results', [])
        return [{
            "id": article.get('link'),
            "title": article.get('title'),
            "date": article.get('pubDate'),
            "content": article.get('description'),
            "source": article.get('source_id'),
            "tags": [article.get('source_id')],
            "imageUrl": article.get('image_url') or "https://i.imgur.com/OQI44rW.png"
        } for article in articles]
    except Exception as e:
        print(f"Error fetching NewsData.io data: {e}")
        return []
# REPLACE this entire function in backend/app.py
def fetch_knowivate_articles():
    """Fetches articles from multiple Knowivate API endpoints concurrently."""
    
    # --- Add all the URLs you want to fetch from here ---
    URLS = [
        "https://news.knowivate.com/api/technologies",
        "https://news.knowivate.com/api/business",
        "https://news.knowivate.com/api/science", "https://news.knowivate.com/api/sports","https://news.knowivate.com/api/agriculture"
        # Add more URLs as needed
    ]

    all_articles = []

    def fetch_and_parse(url):
        """Helper function to fetch and parse a single URL."""
        try:
            response = requests.get(url, timeout=10) # Added a timeout
            response.raise_for_status()
            json_response = response.json()
            articles = json_response.get('data', json_response.get('articles', []))
            
            # Format the articles to match our project structure
            return [{
                "id": article.get('url') or article.get('link'),
                "title": article.get('title'),
                "date": article.get('publishedAt') or article.get('pubDate'),
                "content": article.get('summary') or article.get('description'),
                "source": article.get('source', 'Knowivate'),
                "tags": [article.get('source', 'Technology')],
                "imageUrl": article.get('imageUrl') or article.get('image_url') or "https://i.imgur.com/OQI44rW.png"
            } for article in articles]
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            return [] # Return an empty list if an error occurs

    # Use a thread pool to fetch all URLs concurrently
    with ThreadPoolExecutor(max_workers=len(URLS)) as executor:
        results = executor.map(fetch_and_parse, URLS)
        for article_list in results:
            all_articles.extend(article_list)
            
    return all_articles    
# REPLACE this function in backend/app.py
# REPLACE this function in backend/app.py
@app.route('/api/content', methods=['GET'])
def get_all_content():
    # 1. Combine data from ALL API sources, including the new one
    all_content = (fetch_blogger_posts() + 
                   fetch_news_articles() + 
                   fetch_gnews_articles() + 
                   fetch_newsdata_articles() +
                   fetch_knowivate_articles()) # <-- Added new source
    
    # 2. Filter out duplicates
    unique_posts = []
    seen_titles = set()
    for post in all_content:
        if post.get('title') and post['title'].lower() not in seen_titles:
            unique_posts.append(post)
            seen_titles.add(post['title'].lower())
            
    # 3. Safer sorting on the unique list
    unique_posts.sort(key=lambda x: x.get('date') or '', reverse=True)
    
    return jsonify(unique_posts)

# Single post endpoint remains the same
@app.route('/api/content/<path:post_id>', methods=['GET'])
def get_single_content(post_id):
    all_content = load_posts() + fetch_blogger_posts() + fetch_news_articles()
    found_post = next((post for post in all_content if str(post.get('id')) == post_id), None)
    if found_post:
        return jsonify(found_post)
    else:
        abort(404, description="Post not found")

if __name__ == '__main__':
>>>>>>> f460b6ef0f86bd1e5c8ad7befc75e75a83c0f5e6
    app.run(debug=True, port=5000)