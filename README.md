# **Job Market Analysis - Web Scraping System**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

Hệ thống thu thập và phân tích dữ liệu việc làm từ các trang web tuyển dụng tại Việt Nam, được xây dựng bằng Python với kiến trúc OOP.

## **📋 Mục Lục**

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Cài Đặt](#-cài-đặt)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [Cách Sử Dụng](#-cách-sử-dụng)
- [Cấu Hình](#-cấu-hình)
- [Kiến Trúc](#-kiến-trúc)

## **✨ Giới Thiệu**

Dự án này cung cấp giải pháp tự động hóa việc thu thập dữ liệu việc làm từ các trang web tuyển dụng hàng đầu Việt Nam. Hệ thống được thiết kế để:

- Thu thập thông tin việc làm theo nhiều keyword khác nhau
- Xử lý và chuẩn hóa dữ liệu tự động
- Lưu trữ dữ liệu vào nhiều định dạng (CSV, Google Sheets)
- Hỗ trợ phân tích thị trường việc làm

## **🚀 Tính Năng**

### **📊 Thu Thập Dữ Liệu**
- **Hỗ trợ đa nguồn**: JobsGo và TopCV
- **Xử lý linh hoạt**: Async (cho web không bị rate limiting) và Sync (cho web dình rate limiting)
- **Retry thông minh**: Tự động xử lý rate limiting và timeout
- **Phân trang tự động**: Tự động xác định số trang cần crawl

### **🔧 Xử Lý Dữ Liệu**
- **Chuẩn hóa lương**: Chuyển đổi về đơn vị triệu VND
- **Trích xuất kỹ năng**: Tự động phát hiện tools từ mô tả
- **Xử lý địa điểm**: Chuẩn hóa format địa điểm
- **Loại bỏ duplicate**: Dựa trên job_id và thời gian

### **💾 Lưu Trữ**
- **CSV**: Lưu trữ local với append mode
- **Google Sheets**: Đồng bộ lên cloud
- **Tự động deduplicate**: Giữ dữ liệu sạch

## **⚙️ Cài Đặt**

### **Yêu Cầu Hệ Thống**
- Python 3.8 trở lên
- pip (Python package manager)

### **Cài Đặt Dependencies**

```bash
# Clone repository
git clone https://github.com/hoan110102/job-scraping.git
cd job-scraping

# Tạo virtual environment (tuỳ chọn)
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### **requirements.txt**
```txt
httpx==0.25.0
beautifulsoup4==4.12.2
lxml==4.9.3
pandas==2.0.3
numpy==1.24.3
gspread==5.11.0
google-auth==2.22.0
google-auth-oauthlib==1.0.0
google-api-python-client==2.95.0
unidecode==1.3.6
python-dotenv==1.0.0
```

## **📁 Cấu Trúc Dự Án**

```
job-scraping/
├── scrapers/                    # Các module thu thập dữ liệu
│   ├── __init__.py
│   ├── jobsgo_scraper.py       # Scraper cho JobsGo (async)
│   └── topcv_scraper.py        # Scraper cho TopCV (sync)
├── utils/                      # Tiện ích và helpers
│   ├── __init__.py
│   ├── common.py              # Common functions và classes
│   └── config.py              # Configuration
├── data_processor/             # Xử lý dữ liệu
│   ├── __init__.py
│   └── processor.py           # Xử lý và chuẩn hóa dữ liệu
├── credentials/                # Credentials (không commit)
│   └── credentials.json       # Google Service Account
├── data/                       # Dữ liệu đã thu thập
│   └── final_crawl_data.csv   # Kết quả
├── image/                      # Hình ảnh và dashboard
├── venv_scraping/              # Virtual environment
├── main.py                     # Entry point chính
├── requirements.txt           # Dependencies
└── README.md                  # Tài liệu này
```

## **🚀 Cách Sử Dụng**

### **Chạy Toàn Bộ Hệ Thống**

```bash
python main.py
```

### **Output**
Hệ thống sẽ:
1. Thu thập dữ liệu từ JobsGo (async)
2. Thu thập dữ liệu từ TopCV (sync)
3. Xử lý và chuẩn hóa dữ liệu
4. Lưu vào `data/final_crawl_data.csv`
5. Upload lên Google Sheets (nếu được cấu hình)

### **Custom Keywords**

Mặc định hệ thống sẽ crawl các keyword:
```python
key_words = [
    "Business Analyst",
    "Data Analyst", 
    "Data Engineer",
    "Data Scientist",
    "Machine Learning",
]
```

Để thay đổi, sửa trong `main.py`:
```python
key_words = [
    "Your Keyword 1",
    "Your Keyword 2",
    # ... thêm keywords mới
]
```

## **🔧 Cấu Hình**

### **Cấu Hình Google Sheets**

1. **Tạo Google Cloud Project**:
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/)
   - Tạo project mới

2. **Kích hoạt APIs**:
   - Google Sheets API
   - Google Drive API

3. **Tạo Service Account**:
   - Vào IAM & Admin → Service Accounts
   - Tạo service account mới
   - Download JSON credentials

4. **Cấu hình trong project**:
   - Đặt file `credentials.json` vào folder `credentials/`
   - Chia sẻ Google Sheet với email của service account

### **Cấu Hình Headers và Timeout**

Sửa file `utils/config.py`:
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    # ... thêm headers tuỳ chỉnh
}

# Thời gian timeout (giây)
TIMEOUT = 30
```

## **🏗️ Kiến Trúc**

### **Design Pattern**
- **Factory Pattern**: Tạo HTTP client (sync/async)
- **Strategy Pattern**: Xử lý dữ liệu khác nhau cho từng website
- **Template Method**: Base class cho scraper

### **Data Flow**
```
1. Main → khởi tạo scraper
2. Scraper → HTTP Client → fetch HTML
3. HTML → BeautifulSoup → parse data
4. Raw Data → Data Processor → clean data
5. Clean Data → Storage (CSV/Google Sheets)
```

## **📊 Data Schema**

### **Raw Data Fields**
| Field | Type | Description |
|-------|------|-------------|
| source | string | "JobsGo" hoặc "TopCV" |
| job_type | string | Loại công việc (Data Analyst, etc.) |
| url_job | string | URL chi tiết công việc |
| job_id | string | ID duy nhất của job |
| posting_date | string | Ngày đăng (dd-mm-yyyy) |
| job_title | string | Tiêu đề công việc |
| salary | string | Mức lương (raw) |
| location | string | Địa điểm làm việc |
| exp | string | Yêu cầu kinh nghiệm |
| level | string | Cấp bậc |
| industry | string | Ngành nghề |
| company_name | string | Tên công ty |
| description | string | Mô tả công việc |

### **Processed Data Fields**
| Field | Type | Description |
|-------|------|-------------|
| month | int | Tháng thu thập |
| year | int | Năm thu thập |
| salary | float | Lương (triệu VND) |
| exp | float | Kinh nghiệm (năm) |
| tools | string | Các công cụ/kỹ năng phát hiện |

## **🛠️ Phát Triển**

### **Thêm Scraper Mới**

1. Tạo file mới trong folder `scrapers/`:
```python
# scrapers/new_scraper.py
from utils.common import Create_Client_Sync, Get_Soup_Sync, Crawl_Data
import pandas as pd

def scrape_new_site(key_word=None):
    # Implementation
    pass
```

2. Import vào `main.py`:
```python
from scrapers.new_scraper import scrape_new_site
```

3. Thêm vào pipeline trong `main.py`

## **⚠️ Best Practices & Notes**

### **Rate Limiting**
- JobsGo: Sử dụng async với delay hợp lý
- TopCV: Sử dụng sync để tránh bị block
- Luôn check `robots.txt` của từng website

### **Error Handling**
- Retry logic: 5 lần thử với exponential backoff
- Logging: In thông tin chi tiết khi có lỗi
- Graceful shutdown: Đóng connection đúng cách

### **Performance**
- Async cho I/O bound operations
- Batch processing cho large datasets
- Memory management với large DataFrames

## **📞 Liên Hệ**

Author: [hoan110102](https://github.com/hoan110102)

Project Link: [https://github.com/hoan110102/job-scraping](https://github.com/hoan110102/job-scraping)

## **🙏 Acknowledgements**

- [httpx](https://www.python-httpx.org/) - HTTP client cho async/sync requests
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [gspread](https://docs.gspread.org/) - Google Sheets API

---

**⭐ Nếu bạn thấy dự án hữu ích, hãy star repository này!**
