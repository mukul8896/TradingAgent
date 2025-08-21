# chartink_scanner.py
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import datetime
from config import CHARTINK_SCAN_URL

def stocks_scanner(query):
    url = CHARTINK_SCAN_URL
    stock_list = None
    with requests.session() as s:
        r_data = s.get(url)
        soup = bs(r_data.content, "lxml")
        meta = soup.find("meta", {"name" : "csrf-token"})["content"]
    
        header = {"x-csrf-token" : meta}
        data = s.post(url, headers=header, data=query).json()
    
        stock_list = pd.DataFrame(data["data"])
        # Check if the 'nsecode' column exists in the data
        if "nsecode" not in stock_list.columns:
            return []
        
        return stock_list["nsecode"].apply(lambda x: {"tradingsymbol": x}).tolist()