import asyncio
import pandas as pd
import time

from scrapers.jobsgo_scraper import JobsGoScraper
from scrapers.topcv_scraper import TopCVScraper
from data_processor.processor import JobDataProcessor
from utils.storage import CSVStorage, GoogleSheetStorage


class JobScrapingApp:    
    def __init__(self):
        self.keywords = [
            "Business Analyst",
            "Data Analyst", 
            "Data Engineer",
            "Data Scientist",
            "Machine Learning",
        ]
        self.all_data = pd.DataFrame()
        
        # Khởi tạo các thành phần
        self.scrapers = [
            JobsGoScraper(),
            TopCVScraper(),
        ]
        self.processor = JobDataProcessor()
        self.storages = [
            CSVStorage(folder="data"),
            GoogleSheetStorage(),
        ]
    
    async def run_async_scraper(self, scraper, keyword: str):
        """Chạy scraper async"""
        try:
            return await scraper.scrape(keyword)
        except Exception as e:
            print(f"[ERROR] Lỗi khi scrape {keyword} với {scraper.name}: {e}")
            return pd.DataFrame()
    
    def run_sync_scraper(self, scraper, keyword: str):
        """Chạy scraper sync"""
        try:
            return scraper.scrape(keyword)
        except Exception as e:
            print(f"[ERROR] Lỗi khi scrape {keyword} với {scraper.name}: {e}")
            return pd.DataFrame()
    
    async def scrape_all(self):
        """Scrape tất cả dữ liệu"""
        print("=" * 50)
        print("BẮT ĐẦU SCRAPING")
        print("=" * 50)
        
        total_start = time.time()
        
        for scraper in self.scrapers:
            print(f"\n{'-'*30}")
            print(f"Đang scrape từ: {scraper.name}")
            print(f"{'-'*30}")
            
            start_time = time.time()
            
            for keyword in self.keywords:
                print(f"\nKeyword: {keyword}")
                
                if isinstance(scraper, JobsGoScraper):  # Async scraper
                    df = await self.run_async_scraper(scraper, keyword)
                else:  # Sync scraper
                    df = self.run_sync_scraper(scraper, keyword)
                
                if not df.empty:
                    self.all_data = pd.concat([self.all_data, df], ignore_index=True)
                    print(f"  → Đã thêm {len(df)} jobs")
                else:
                    print(f"  → Không tìm thấy jobs")
            
            end_time = time.time()
            print(f"\nHoàn thành {scraper.name} trong {end_time - start_time:.2f}s")
        
        total_end = time.time()
        print(f"\n{'='*50}")
        print(f"TỔNG KẾT")
        print(f"{'='*50}")
        print(f"Tổng thời gian: {total_end - total_start:.2f}s")
        print(f"Tổng số jobs thu thập được: {len(self.all_data)}")
    
    def process_and_save(self):
        """Xử lý và lưu dữ liệu"""
        if self.all_data.empty:
            print("\nKhông có dữ liệu để xử lý!")
            return
        
        print(f"\n{'='*50}")
        print("XỬ LÝ VÀ LƯU DỮ LIỆU")
        print(f"{'='*50}")
        
        # Xử lý dữ liệu
        processed_data = self.processor.process(self.all_data)
        print(f"Đã xử lý {len(processed_data)} dòng dữ liệu")
        
        # Lưu vào tất cả storage
        for storage in self.storages:
            try:
                if isinstance(storage, GoogleSheetStorage):
                    storage.save(processed_data, "final_crawl_data")
                else:
                    storage.save(processed_data, "final_crawl_data")
                print(f"✓ Đã lưu vào {storage.get_name()}")
            except Exception as e:
                print(f"✗ Lỗi khi lưu vào {storage.get_name()}: {e}")


async def main():
    """Hàm main"""
    app = JobScrapingApp()
    
    # Scrape dữ liệu
    await app.scrape_all()
    
    # Xử lý và lưu
    app.process_and_save()


if __name__ == "__main__":
    asyncio.run(main())