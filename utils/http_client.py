import httpx
import asyncio
import time
import random
from typing import Optional
from bs4 import BeautifulSoup


class BaseHTTPClient:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url
        self.headers = headers
        self.retry_codes = [429, 500, 502, 503, 504]
    
    def _calculate_wait_time(self, attempt: int, response: Optional[httpx.Response] = None) -> float:
        """Tính thời gian chờ với exponential backoff"""
        if response and response.headers.get("Retry-After"):
            try:
                return float(response.headers.get("Retry-After")) + random.uniform(0.5, 2.0)
            except:
                pass
        return (6 * attempt) + random.uniform(0.5, 2.0)
    
    def _should_retry(self, response: httpx.Response) -> bool:
        """Kiểm tra có nên retry không"""
        return response.status_code in self.retry_codes


class AsyncHTTPClient(BaseHTTPClient):    
    def __init__(self, base_url: str, headers: dict):
        super().__init__(base_url, headers)
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """Kết nối và pre-warm cookies"""
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        
        try:
            await self.client.get(self.base_url)
            await asyncio.sleep(1.0)
        except:
            pass  # Bỏ qua nếu pre-warm thất bại
    
    async def get_soup(self, url: str, max_retries: int = 5) -> BeautifulSoup:
        """Lấy BeautifulSoup từ URL với retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                response = await self.client.get(url)
                
                if self._should_retry(response):
                    wait = self._calculate_wait_time(attempt, response)
                    print(f"[WARN] Lỗi {attempt}/5 → chờ {wait:.1f}s tại {url}")
                    await asyncio.sleep(wait)
                    continue
                
                response.raise_for_status()
                return BeautifulSoup(response.text, "lxml")
                
            except httpx.TimeoutException:
                print(f"[WARN] Timeout {attempt}/5 tại {url}")
                if attempt < max_retries:
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
            except Exception as e:
                print(f"[WARN] Lỗi {attempt}/5 tại {url}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
        
        raise Exception(f"Không tải được trang sau {max_retries} lần thử: {url}")
    
    async def close(self):
        """Đóng kết nối"""
        if self.client:
            await self.client.aclose()


class SyncHTTPClient(BaseHTTPClient):    
    def __init__(self, base_url: str, headers: dict):
        super().__init__(base_url, headers)
        self.client: Optional[httpx.Client] = None
    
    def connect(self):
        """Kết nối và pre-warm cookies"""
        self.client = httpx.Client(headers=self.headers, timeout=30.0)
        
        try:
            self.client.get(self.base_url)
            time.sleep(2.0)
        except:
            pass
    
    def get_soup(self, url: str, max_retries: int = 5) -> BeautifulSoup:
        """Lấy BeautifulSoup từ URL với retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.get(url)
                
                if self._should_retry(response):
                    wait = self._calculate_wait_time(attempt, response)
                    print(f"[WARN] Lỗi {attempt}/5 → chờ {wait:.1f}s tại {url}")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                return BeautifulSoup(response.text, "lxml")
                
            except httpx.TimeoutException:
                print(f"[WARN] Timeout {attempt}/5 tại {url}")
                if attempt < max_retries:
                    time.sleep(random.uniform(1, 3))
                    continue
            except Exception as e:
                print(f"[WARN] Lỗi {attempt}/5 tại {url}: {e}")
                if attempt < max_retries:
                    time.sleep(random.uniform(2, 5))
                    continue
        
        raise Exception(f"Không tải được trang sau {max_retries} lần thử: {url}")
    
    def close(self):
        """Đóng kết nối"""
        if self.client:
            self.client.close()