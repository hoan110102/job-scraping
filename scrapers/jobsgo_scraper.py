import asyncio
import re
from typing import Dict, List
import pandas as pd

from .base_scraper import JobScraper
from utils.http_client import AsyncHTTPClient


class JobsGoScraper(JobScraper):    
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
        super().__init__("JobsGo", "https://jobsgo.vn", headers)
        
        # CSS Selectors cho JobsGo
        self.selectors = {
            'url': 'div.card.job-card a.text-decoration-none',
            'title': 'h3.job-title',
            'id': 'div.card.job-card',
            'id_attr': 'data-id',
            'salary': 'div.mt-1 span:first-child',
            'location': 'div.mt-1 span:last-child',
            'exp': 'div.d-flex.flex-wrap.gap-1 span[title="Yêu cầu kinh nghiệm"]',
            'company': 'div.company-title',
            'level': 'div.col-6.col-md-4.d-flex:nth-of-type(2) strong',
            'industry': 'div.d-flex.mt-3 span.fw-500',
            'description': 'div.job-detail-card',
        }
    
    async def scrape(self, keyword: str) -> pd.DataFrame:
        query = keyword.replace(" ", "-").lower()
        base_url_template = f"{self.base_url}/viec-lam-{{query}}.html?page={{page}}"
        
        # Tạo HTTP client
        http_client = AsyncHTTPClient(self.base_url, self.headers)
        await http_client.connect()
        
        try:
            # Lấy số trang
            total_pages = await self._get_total_pages(http_client, query, base_url_template)
            if total_pages == 0:
                print(f"[INFO] Không tìm thấy jobs nào cho '{keyword}'")
                return pd.DataFrame()
            
            # Scrape tất cả pages
            all_jobs = []
            for page in range(1, total_pages + 1):
                url = base_url_template.format(query=query, page=page)
                print(f"  → Đang scrape page {page}/{total_pages}")
                
                soup = await http_client.get_soup(url)
                basic_info = self._extract_basic_info(soup, self.selectors)
                
                # Scrape chi tiết cho từng job
                detailed_info = await self._scrape_details(http_client, basic_info['url_job'])
                
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
            await http_client.close()
    
    async def _get_total_pages(self, http_client: AsyncHTTPClient, query: str, 
                              base_url_template: str) -> int:
        """Lấy tổng số trang"""
        try:
            url = base_url_template.format(query=query, page=1)
            soup = await http_client.get_soup(url)
            
            # Kiểm tra có kết quả không
            job_found = soup.select_one("p.h5.text-muted.mt-3")
            if not job_found:
                text_found = soup.select_one("h1.fs-4.mb-2.mb-sm-3").text.strip().split("-")[0]
                results_count = int(re.sub(r"\s*[^\d]", "", text_found))
                return results_count // 50 + (0 if results_count % 50 == 0 else 1)
        except Exception as e:
            print(f"[WARN] Lỗi khi đếm trang: {e}")
        
        return 0
    
    async def _scrape_details(self, http_client: AsyncHTTPClient, urls: List[str]) -> Dict[str, List]:
        """Scrape thông tin chi tiết cho từng job"""
        levels, industries, descriptions = [], [], []
        
        for url in urls:
            try:
                soup = await http_client.get_soup(url)
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