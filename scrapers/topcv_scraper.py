import re
import time
from typing import Dict, List
import pandas as pd

from .base_scraper import JobScraper
from utils.http_client import SyncHTTPClient


class TopCVScraper(JobScraper):    
    def __init__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        super().__init__("TopCV", "https://www.topcv.vn", headers)
        
        # CSS Selectors cho TopCV
        self.selectors = {
            'url': 'h3.title a',
            'title': 'h3.title',
            'id': 'div.job-list-search-result>div.job-item-search-result',
            'id_attr': 'data-job-id',
            'salary': 'label.salary>span',
            'location': 'span.city-text',
            'exp': 'label.exp>span',
            'company': 'span.company-name',
            'level': 'div.box-general-group:first-child div.box-general-group-info-value',
            'industry': 'div.company-field div.company-value',
            'description': 'div.job-description',
        }
    
    def scrape(self, keyword: str) -> pd.DataFrame:
        query = keyword.replace(" ", "-").lower()
        base_url_template = f"{self.base_url}/tim-viec-lam-{{query}}?type_keyword=1&page={{page}}&sba=1"
        
        # Tạo HTTP client
        http_client = SyncHTTPClient(self.base_url, self.headers)
        http_client.connect()
        
        try:
            # Lấy số trang
            total_pages = self._get_total_pages(http_client, query, base_url_template)
            if total_pages == 0:
                print(f"[INFO] Không tìm thấy jobs nào cho '{keyword}'")
                return pd.DataFrame()
            
            # Scrape tất cả pages
            all_jobs = []
            for page in range(1, total_pages + 1):
                url = base_url_template.format(query=query, page=page)
                print(f"  → Đang scrape page {page}/{total_pages}")
                
                soup = http_client.get_soup(url)
                basic_info = self._extract_basic_info(soup, self.selectors)
                
                # Scrape chi tiết cho từng job
                detailed_info = self._scrape_details(http_client, basic_info['url_job'])
                
                # Kết hợp thông tin
                for i in range(len(basic_info['url_job'])):
                    job_data = {
                        key: basic_info[key][i] if i < len(basic_info[key]) else None
                        for key in basic_info.keys()
                    }
                    job_data.update({
                        key: detailed_info[key][i] if i < len(detailed_info[key]) else None
                        for key in detailed_info.keys()
                    })
                    all_jobs.append(job_data)
            
            # Tạo DataFrame
            df = pd.DataFrame(all_jobs)
            return self._format_dataframe(df.to_dict('list'), keyword)
            
        finally:
            http_client.close()
    
    def _get_total_pages(self, http_client: SyncHTTPClient, query: str, 
                         base_url_template: str) -> int:
        """Lấy tổng số trang"""
        try:
            url = base_url_template.format(query=query, page=1)
            soup = http_client.get_soup(url)
            
            # Kiểm tra có kết quả không
            job_found = soup.select_one("div.none-suitable-job")
            if job_found and "none" in job_found.get("style", ""):
                text_found = soup.select_one("h1.search-job-heading").text.strip().split("[")[0]
                results_count = int(re.sub(r"\s*[^\d]", "", text_found))
                return results_count // 50 + (0 if results_count % 50 == 0 else 1)
        except Exception as e:
            print(f"[WARN] Lỗi khi đếm trang: {e}")
        
        return 0
    
    def _scrape_details(self, http_client: SyncHTTPClient, urls: List[str]) -> Dict[str, List]:
        """Scrape thông tin chi tiết cho từng job"""
        levels, industries, descriptions = [], [], []
        
        for url in urls:
            try:
                soup = http_client.get_soup(url)
                detail = self._extract_detail_info(soup, self.selectors)
                
                levels.append(detail.get('level'))
                industries.append(detail.get('industry'))
                descriptions.append(detail.get('description'))
            except Exception as e:
                print(f"[WARN] Lỗi khi scrape chi tiết {url}: {e}")
                levels.append(None)
                industries.append(None)
                descriptions.append(None)
        
        return {
            'level': levels,
            'industry': industries,
            'description': descriptions
        }