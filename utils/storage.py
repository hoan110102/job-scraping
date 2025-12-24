import os
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials


class DataStorage(ABC):    
    @abstractmethod
    def save(self, data: pd.DataFrame, filename: str):
        """Lưu dữ liệu"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Lấy tên storage"""
        pass


class CSVStorage(DataStorage):    
    def __init__(self, folder: Optional[str] = None):
        self.folder = folder
        self.base_path = self._get_base_path()
    
    def _get_base_path(self) -> str:
        """Lấy đường dẫn base"""
        if self.folder:
            return os.path.join(os.path.dirname(__file__), "..", self.folder)
        return os.path.join(os.path.dirname(__file__), "..")
    
    def save(self, data: pd.DataFrame, filename: str):
        """Lưu dữ liệu vào CSV"""
        os.makedirs(self.base_path, exist_ok=True)
        filepath = os.path.join(self.base_path, f"{filename}.csv")
        
        if os.path.exists(filepath):
            # Append và kiểm tra duplicate
            data.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            df = pd.read_csv(filepath)
            print(f"Đã append {len(data)} dòng, tổng: {len(df)} dòng")
            
            # Xóa duplicate
            initial_len = len(df)
            df = df.drop_duplicates(subset=['job_id', 'month', 'year'])
            removed = initial_len - len(df)
            
            if removed > 0:
                print(f"Đã xóa {removed} dòng trùng lặp")
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
        else:
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"Đã tạo file mới: {filename}.csv với {len(data)} dòng")
    
    def get_name(self) -> str:
        return "CSV"


class GoogleSheetStorage(DataStorage):  
    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path is None:
            self.credentials_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "credentials", 
                "credentials.json"
            )
        else:
            self.credentials_path = credentials_path
    
    def save(self, data: pd.DataFrame, sheet_name: str, sheet_id: Optional[str] = None):
        """Lưu dữ liệu vào Google Sheets"""
        if data.empty:
            print("[WARN] DataFrame rỗng, bỏ qua!")
            return
        
        # Sử dụng sheet_id từ config hoặc parameter
        if sheet_id is None:
            # Import ở đây để tránh circular import
            from utils.config import sheet_id
            sheet_id = sheet_id
        
        # Kết nối Google Sheets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        
        creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Mở sheet
        sheet = client.open_by_key(sheet_id)
        
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=sheet_name, rows=10000, cols=30)
        
        # Lấy dữ liệu hiện có
        existing_data = worksheet.get_all_values()
        
        if len(existing_data) <= 1:  # Chỉ có header hoặc không có gì
            worksheet.clear()
            set_with_dataframe(worksheet, data, include_index=False, include_column_header=True)
            print(f"Đã ghi mới {len(data)} dòng vào Google Sheets")
        else:
            # Append dữ liệu mới
            worksheet.append_rows(data.values.tolist(), value_input_option="RAW")
            
            # Đọc lại toàn bộ dữ liệu để xóa duplicate
            all_data = worksheet.get_all_values()
            if len(all_data) > 1:
                df_all = pd.DataFrame(all_data[1:], columns=all_data[0])
                initial_len = len(df_all)
                df_all = df_all.drop_duplicates(subset=['job_id', 'month', 'year'], keep='last')
                removed = initial_len - len(df_all)
                
                # Ghi lại dữ liệu đã clean
                worksheet.clear()
                set_with_dataframe(worksheet, df_all, include_index=False, include_column_header=True)
                
                if removed > 0:
                    print(f"Đã xóa {removed} dòng trùng lặp trên Google Sheets")
            
            print(f"Hoàn tất cập nhật Google Sheets: {len(data)} dòng mới")
    
    def get_name(self) -> str:
        return "Google Sheets"