import pandas as pd
import numpy as np
import re
from unidecode import unidecode
from typing import Optional, List, Set


class JobDataProcessor:
    """Class xử lý dữ liệu job - thể hiện tính ĐÓNG GÓI"""
    
    def __init__(self, keywords: Optional[List[str]] = None):
        """Khởi tạo processor với danh sách keywords (nếu có)"""
        self.keywords = keywords or self._get_default_keywords()
        self.processed_data = None
    
    def _get_default_keywords(self) -> List[str]:
        """Trả về danh sách keywords mặc định"""
        return [
            # Tools for DA
            'Python', 'R', 'SQL', 'Tableau', 'Power BI', 'Qlik', 'Looker', 'Data Studio',
            'Mysql', 'Postgresql', 'Oracle', 'SQL Server', 'Excel', 'Google Sheet', 'Powerpoint', 'SPSS',
            # Tools for DE
            'Mongodb', 'Bigquery', 'Spark', 'Amazon S3', 'Google Cloud Storage', 'Azure', 'Kafka', 
            'Flink', 'Hive', 'Presto', 'Airflow', 'Luigi', 'Alation', 'Collibra', 'Redshift', 
            'Snowflake', 'Docker', 'Kubernetes', 'Terraform', 'Informatica', 'Talend', 'SSIS', 'ODI',
            # Tools for DS, ML
            "Matplotlib", "Spark", "Hadoop", "TensorFlow", "SAS", "BigML", "Scikit-learn", 
            "Knime", "Matlab", "Pytorch", "Cloud Computing", "Keras", "Rapid Miner",
            "Azure Machine Learning", "Watson Studio", "Mahout", "RapidMiner", "Shogun", 
            "OpenNN", "SageMaker",
            # Tools for ML
            "Visio", "Jira", "Excel", "Power BI", "LucidChart", "Balsamiq", "Clickup", 
            "Enterprise Architect", "Wrike", "Blueprint", "Confluence", "NetSuite", 
            "Axure", "Trello"
        ]
    
    def process(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Xử lý dữ liệu thô - phương thức chính"""
        if raw_data.empty:
            print("[INFO] Không có dữ liệu để xử lý")
            return raw_data
        
        print(f"Bắt đầu xử lý {len(raw_data)} dòng dữ liệu...")
        
        # Tạo bản copy để không ảnh hưởng dữ liệu gốc
        new_df = raw_data.copy()
        
        # Thực hiện các bước xử lý
        self._add_date_columns(new_df)
        new_df["salary"] = new_df["salary"].apply(self._process_salary)
        new_df["location"] = new_df["location"].apply(self._process_location)
        new_df["exp"] = new_df["exp"].apply(self._process_exp)
        new_df["level"] = new_df["level"].apply(self._process_level)
        new_df["industry"] = new_df["industry"].apply(self._process_industry)
        new_df["tools"] = new_df["description"].apply(self._process_description)
        
        # Chọn và sắp xếp columns
        final_df = self._select_columns(new_df)
        
        # Xóa duplicate
        final_df = self._remove_duplicates(final_df)
        
        self.processed_data = final_df
        print("Đã xử lý xong dữ liệu!")
        return final_df
    
    def _add_date_columns(self, df: pd.DataFrame) -> None:
        """Thêm cột month và year từ posting_date"""
        try:
            df["month"] = pd.to_datetime(df["posting_date"], dayfirst=True).dt.month.astype(int)
            df["year"] = pd.to_datetime(df["posting_date"], dayfirst=True).dt.year.astype(int)
        except Exception as e:
            print(f"[WARN] Lỗi khi xử lý ngày tháng: {e}")
            df["month"] = pd.Timestamp.now().month
            df["year"] = pd.Timestamp.now().year
    
    def _process_salary(self, salary: str) -> Optional[float]:
        """Xử lý thông tin lương"""
        if pd.isna(salary):
            return None
        
        try:
            salary_str = unidecode(salary.lower().strip())
            
            # Kiểm tra nếu là "thỏa thuận" hoặc "thương lượng"
            if any(x in salary_str for x in ["thoa thuan", "thuong luong", "canh tranh"]):
                return None
            
            # Loại bỏ ký tự không phải số, dấu "." và "-"
            pattern = r"\s*[^\d.-]"
            num_salary = re.sub(pattern, "", salary_str)
            
            if not num_salary:  # Nếu không còn số nào
                return None
            
            # Xử lý range (khoảng lương)
            if "-" in num_salary:
                parts = num_salary.split("-")
                if len(parts) == 2:
                    x = float(parts[0])
                    y = float(parts[1])
                    avg_salary = (x + y) / 2
                else:
                    return None
            else:
                avg_salary = float(num_salary)
            
            # Chuyển đổi đơn vị
            if "trieu" in salary_str:
                return float(avg_salary)
            elif "usd" in salary_str:
                return float(avg_salary) * 0.026  # 1 USD = 26,000 VND (làm tròn)
            else:
                return float(avg_salary)
                
        except Exception as e:
            print(f"[WARN] Lỗi xử lý lương '{salary}': {e}")
            return None
    
    def _process_location(self, location: str) -> Optional[str]:
        """Xử lý thông tin địa điểm"""
        if pd.isna(location):
            return None
        
        try:
            location = str(location).strip()
            
            # Nếu có "&" thì lấy phần trước "&"
            if "&" in location:
                return location.split("&")[0].strip()
            # Nếu có "," thì lấy phần trước dấu ","
            elif "," in location:
                return location.split(",")[0].strip()
            else:
                return location
                
        except Exception as e:
            print(f"[WARN] Lỗi xử lý địa điểm '{location}': {e}")
            return None
    
    def _process_exp(self, exp: str) -> Optional[float]:
        """Xử lý thông tin kinh nghiệm"""
        if pd.isna(exp):
            return None
        
        try:
            exp_str = unidecode(exp.lower().strip())
            
            # Kiểm tra nếu không yêu cầu kinh nghiệm
            if any(x in exp_str for x in ["khong yeu cau", "khong can kinh nghiem"]):
                return 0.0
            
            # Loại bỏ ký tự không phải số, dấu "." và "-"
            pattern = r"\s*[^\d.-]"
            num_exp = re.sub(pattern, "", exp_str)
            
            if not num_exp:  # Nếu không còn số nào
                return None
            
            # Xử lý range (khoảng kinh nghiệm)
            if "-" in num_exp:
                parts = num_exp.split("-")
                if len(parts) == 2:
                    x = float(parts[0])
                    y = float(parts[1])
                    return (x + y) / 2
                else:
                    return None
            else:
                return float(num_exp)
                
        except Exception as e:
            print(f"[WARN] Lỗi xử lý kinh nghiệm '{exp}': {e}")
            return None
    
    def _process_level(self, level: str) -> Optional[str]:
        """Xử lý thông tin cấp bậc"""
        if pd.isna(level):
            return None
        
        try:
            level = str(level).strip()
            
            # Chuẩn hóa dấu phân cách
            pattern = r"\s*[/,]\s*"
            level = re.sub(pattern, "/", level)
            
            return level
        except Exception as e:
            print(f"[WARN] Lỗi xử lý cấp bậc '{level}': {e}")
            return None
    
    def _process_industry(self, industry: str) -> Optional[str]:
        """Xử lý thông tin ngành nghề"""
        if pd.isna(industry):
            return None
        
        try:
            industry = str(industry).strip()
            
            # Chuẩn hóa dấu phân cách
            pattern = r"\s*[/,]\s*"
            industry = re.sub(pattern, "/", industry)
            
            return industry
        except Exception as e:
            print(f"[WARN] Lỗi xử lý ngành nghề '{industry}': {e}")
            return None
    
    def _process_description(self, description: str) -> Optional[str]:
        """Trích xuất tools từ mô tả công việc"""
        if pd.isna(description) or not description:
            return None
        
        try:
            text = str(description).lower()
            
            # Tạo mapping từ keyword lowercase về keyword gốc
            keyword_map = {}
            for kw in pd.Series(self.keywords).dropna().unique():
                kw_str = str(kw).strip()
                if not kw_str:
                    continue
                norm_kw = kw_str.lower()
                keyword_map[norm_kw] = kw_str
            
            # Tìm các keyword có trong description
            matched_original = set()
            
            for norm_kw, original_kw in keyword_map.items():
                # Pattern để tìm từ đứng độc lập (không phải phần của từ khác)
                pattern = r'(?i)(?<![\wàáảãạăắằẳẵặâấầẩẫậêếềểễệôốồổỗộơớờởỡợưứừửữựđ])' + \
                         re.escape(norm_kw) + \
                         r'(?![\wàáảãạăắằẳẵặâấầẩẫậêếềểễệôốồổỗộơớờởỡợưứừửữựđ])'
                
                if re.search(pattern, text):
                    matched_original.add(original_kw)
            
            # Trả về chuỗi các tools, phân cách bằng dấu phẩy
            return ",".join(sorted(matched_original)) if matched_original else None
            
        except Exception as e:
            print(f"[WARN] Lỗi xử lý mô tả: {e}")
            return None
    
    def _select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chọn và sắp xếp các cột cần thiết"""
        columns_order = [
            "source",
            "job_type",
            "month",
            "year",
            "job_id",
            "job_title",
            "salary",
            "location",
            "exp",
            "level",
            "industry",
            "company_name",
            "tools",  # Đã đổi tên từ description
        ]
        
        # Chỉ giữ lại các cột có trong DataFrame
        existing_columns = [col for col in columns_order if col in df.columns]
        return df[existing_columns]
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Xóa các bản ghi trùng lặp dựa trên job_id"""
        initial_count = len(df)
        df = df.drop_duplicates(subset=['job_id'], keep="first").reset_index(drop=True)
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            print(f"Đã xóa {removed_count} bản ghi trùng lặp")
        
        return df
    
    def get_summary(self) -> dict:
        """Trả về thống kê về dữ liệu đã xử lý"""
        if self.processed_data is None or self.processed_data.empty:
            return {"message": "Chưa có dữ liệu đã xử lý"}
        
        df = self.processed_data
        
        summary = {
            "total_jobs": len(df),
            "sources": df["source"].value_counts().to_dict(),
            "job_types": df["job_type"].value_counts().to_dict(),
            "jobs_with_salary": df["salary"].notna().sum(),
            "jobs_with_tools": df["tools"].notna().sum(),
            "average_exp": df["exp"].mean() if not df["exp"].isna().all() else None,
            "average_salary": df["salary"].mean() if not df["salary"].isna().all() else None,
            "top_locations": df["location"].value_counts().head(10).to_dict(),
            "top_companies": df["company_name"].value_counts().head(10).to_dict(),
        }
        
        return summary


# Hàm tiện ích để sử dụng như cũ (giữ lại cho tương thích)
def data_processor(df: pd.DataFrame) -> pd.DataFrame:
    """Hàm wrapper để sử dụng như code cũ"""
    processor = JobDataProcessor()
    return processor.process(df)


# Example usage
if __name__ == "__main__":
    # Tạo dữ liệu mẫu để test
    sample_data = pd.DataFrame({
        "source": ["JobsGo", "TopCV"],
        "job_type": ["Data Analyst", "Data Engineer"],
        "posting_date": ["01-12-2024", "15-12-2024"],
        "job_id": ["J001", "T001"],
        "job_title": ["Data Analyst", "Data Engineer"],
        "salary": ["10-15 triệu", "Thương lượng"],
        "location": ["Hà Nội, Việt Nam", "TP HCM & Đà Nẵng"],
        "exp": ["2-4 năm", "Không yêu cầu"],
        "level": ["Nhân viên / Chuyên viên", "Senior"],
        "industry": ["IT / Công nghệ", "Phần mềm"],
        "company_name": ["Công ty A", "Công ty B"],
        "description": ["Yêu cầu biết Python, SQL, Excel", "Cần kinh nghiệm với Spark, Hadoop"]
    })
    
    # Xử lý dữ liệu
    processor = JobDataProcessor()
    result = processor.process(sample_data)
    
    print("\nKết quả xử lý:")
    print(result)
    
    print("\nThống kê:")
    summary = processor.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")