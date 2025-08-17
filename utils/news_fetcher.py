# utils/news_fetcher.py
import requests
import time
from datetime import datetime, timedelta
from config import API_KEYS, COMPANY_NAMES

# Indian financial news sources supported by NewsAPI
INDIAN_SOURCES = [
    "economictimes.indiatimes.com",
    "moneycontrol.com",
    "livemint.com",
    "business-standard.com",
    "financialexpress.com"
]

def chunk_companies(companies, max_chars=450):
    """Split list of company names into batches such that query length < max_chars."""
    batches = []
    batch = []
    total_len = 0
    for comp in companies:
        comp_len = len(comp) + 4  # account for ' OR '
        if total_len + comp_len > max_chars:
            if batch:
                batches.append(batch)
            batch = [comp]
            total_len = comp_len
        else:
            batch.append(comp)
            total_len += comp_len
    if batch:
        batches.append(batch)
    return batches

def combine_news_by_company(all_news_articles):
    """
    Combine multiple news articles for the same ticker/company into a single object.
    Descriptions are concatenated as bullet points, duplicates removed.
    Returns a list of combined news dictionaries.
    """
    combined_news = {}

    for item in all_news_articles:
        ticker = item.get("ticker") or item.get("companyName") or "Unknown"
        desc = item.get("description") or ""
        if not desc:
            continue  # skip empty descriptions

        if ticker in combined_news:
            existing_desc = combined_news[ticker]["description"]
            existing_lines = set(existing_desc.split("\n• "))
            for line in desc.split(". "):  # simple sentence split
                line = line.strip()
                if line and line not in existing_lines:
                    combined_news[ticker]["description"] += f"\n• {line}"
            # Add sources and urls
            # if item.get("source"):
            #     combined_news[ticker]["sources"].add(item["source"])
            # if item.get("url"):
            #     combined_news[ticker]["urls"].append(item["url"])
        else:
            combined_news[ticker] = {
                "ticker": ticker,
                "title": item.get("title") or "",
                "description": f"• {desc}",
                # "sources": set([item.get("source")]) if item.get("source") else set(),
                # "urls": [item.get("url")] if item.get("url") else []
            }

    # Convert sources set to list
    # for item in combined_news.values():
    #     item["sources"] = list(item["sources"])

    return list(combined_news.values())

def fetch_news(portfolio_companies=None):
    """
    Fetch news for portfolio companies + COMPANY_NAMES or general Indian market if portfolio_companies is None.
    Returns a list of news articles as dictionaries.
    """
    base_url = "https://newsapi.org/v2/everything"
    all_articles = []

    # If portfolio_companies is None, fetch general Indian market news
    if portfolio_companies is None:
        params = {
            "q": "(indian stock market OR indian stocks OR Sensex OR Nifty OR NSE OR BSE OR \"Indian economy\") "
                "AND (earnings OR \"quarterly results\" OR profit OR revenue OR loss OR \"net income\" "
                "OR dividend OR IPO OR \"share buyback\" OR merger OR acquisition OR \"capital expenditure\" "
                "OR \"expansion plans\" OR \"market trend\" OR \"investor sentiment\" OR bullish OR bearish OR correction)",
            "language": "en",
            "from": (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "apiKey": API_KEYS["news_api"]
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            print(f"Error fetching general market news: {data}")
        else:
            for article in data.get("articles", []):
                all_articles.append({
                    "companyName": None,  # General market news
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "source": article.get("source", {}).get("name"),
                    "publishedAt": article.get("publishedAt")
                })
        return all_articles

    # Combine portfolio companies with additional list from config
    # companies = list(set(portfolio_companies + COMPANY_NAMES))
    # batches = chunk_companies(companies)

    for company in portfolio_companies:
        query = company  # single company per request
        params = {
            "q": query,
            "language": "en",
            "from": (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "apiKey": API_KEYS["news_api"]
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            print(f"Error fetching news for {company}: {data}")
            continue

        for article in data.get("articles", []):
            title_desc = ((article.get("title") or "") + " " + (article.get("description") or "")).lower()

            all_articles.append({
                "companyName": company,
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "source": article.get("source", {}).get("name"),
                "publishedAt": article.get("publishedAt")
            })

        # Respect 1 request/sec limit
        time.sleep(2)

    return all_articles


def filter_earning_news(news_list):
    """
    Filter news for earnings/financial related keywords.
    Accepts a list of news dicts and returns a filtered list.
    """
    earning_keywords = [
        "earnings", "quarterly results", "profit", "loss", "revenue",
        "net income", "Q1 results", "Q2 results", "Q3 results", "Q4 results"
    ]
    filtered_news = []
    for news in news_list:
        content = (news.get("title") or "") + " " + (news.get("description") or "")
        if any(keyword.lower() in content.lower() for keyword in earning_keywords):
            filtered_news.append(news)
    return filtered_news
