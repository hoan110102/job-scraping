from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd


class JobScraper(ABC):    
    def __init__(self, name: str, base_url: str, headers: dict):
        self.name = name
        self.base_url = base_url
        self.headers = headers
    
    @abstractmethod
    def scrape(self, keyword: str) -> pd.DataFrame:
        pass
    
    def _format_dataframe(self, data: Dict[str, List], keyword: str) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df['source'] = self.name
        df['job_type'] = keyword
        df['posting_date'] = datetime.now().strftime("%d-%m-%Y")
        
        # Sắp xếp columns
        columns_order = [
            'source', 'job_type', 'url_job', 'job_id', 'posting_date',
            'job_title', 'salary', 'location', 'exp', 'level',
            'industry', 'company_name', 'description'
        ]
        
        # Chỉ giữ columns có trong DataFrame
        existing_columns = [col for col in columns_order if col in df.columns]
        return df[existing_columns]
    
    def _extract_basic_info(self, soup, selectors: Dict[str, str]) -> Dict[str, List]:
        results = {}
        
        # URL
        a_tags = soup.select(selectors['url'])
        results['url_job'] = [
            url if url.startswith('http') else self.base_url + url
            for url in [a.get('href', '') for a in a_tags]
        ]
        
        # Job Title
        title_tags = soup.select(selectors['title'])
        results['job_title'] = [title.text.strip() for title in title_tags]
        
        # Job ID
        id_tags = soup.select(selectors['id'])
        results['job_id'] = [
            tag.get(selectors['id_attr'], '') for tag in id_tags
        ]
        
        # Salary
        salary_tags = soup.select(selectors['salary'])
        results['salary'] = [sal.text.strip() for sal in salary_tags]
        
        # Location
        loc_tags = soup.select(selectors['location'])
        results['location'] = [loc.text.strip() for loc in loc_tags]
        
        # Experience
        exp_tags = soup.select(selectors['exp'])
        results['exp'] = [exp.text.strip() for exp in exp_tags]
        
        # Company
        company_tags = soup.select(selectors['company'])
        results['company_name'] = [com.text.strip() for com in company_tags]
        
        return results
    
    def _extract_detail_info(self, soup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Trích xuất thông tin chi tiết - thể hiện tính ĐÓNG GÓI"""
        results = {}
        
        # Level
        level_tag = soup.select_one(selectors.get('level', ''))
        results['level'] = level_tag.get_text(strip=True) if level_tag else None
        
        # Industry
        industry_tag = soup.select_one(selectors.get('industry', ''))
        results['industry'] = industry_tag.get_text(strip=True) if industry_tag else None
        
        # Description
        desc_tag = soup.select_one(selectors.get('description', ''))
        results['description'] = desc_tag.get_text(strip=True, separator='\n') if desc_tag else None
        
        return results