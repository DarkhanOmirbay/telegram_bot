import logging
from datetime import datetime
from typing import Dict, Any, Optional
import gspread
from gspread import Client
from google.oauth2.service_account import Credentials
import json
import os

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Менеджер для работы с Google Sheets"""
    
    def __init__(self, credentials_path: str, spreadsheet_name: str):
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.client: Optional[Client] = None
        self.worksheet = None
        
    async def init_connection(self):
        """Инициализация подключения к Google Sheets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загрузка учетных данных
            if os.path.exists(self.credentials_path):
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=scopes
                )
            else:
                # Если файла нет, пробуем загрузить из переменной окружения
                credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if credentials_json:
                    credentials_info = json.loads(credentials_json)
                    credentials = Credentials.from_service_account_info(
                        credentials_info, scopes=scopes
                    )
                else:
                    raise FileNotFoundError("Google credentials not found")
            
            # Подключение к Google Sheets
            self.client = gspread.authorize(credentials)
            
            # Открытие таблицы или создание новой
            try:
                spreadsheet = self.client.open(self.spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                # Создаем новую таблицу если не существует
                spreadsheet = self.client.create(self.spreadsheet_name)
                logger.info(f"Created new spreadsheet: {self.spreadsheet_name}")
            
            # Получаем первый лист или создаем
            try:
                self.worksheet = spreadsheet.sheet1
            except:
                self.worksheet = spreadsheet.add_worksheet(title="Leads", rows=1000, cols=20)
            
            # Инициализируем заголовки если таблица пустая
            if not self.worksheet.get_all_records():
                await self.setup_headers()
                
            logger.info("Google Sheets connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
    
    async def setup_headers(self):
        """Настройка заголовков таблицы"""
        headers = [
            'Дата/Время',
            'Имя',
            'Телефон', 
            'Сегмент',
            'Действие',
            'Username',
            'User ID',
            'Статус',
            'Примечания'
        ]
        
        try:
            self.worksheet.insert_row(headers, 1)
            
            # Форматирование заголовков
            self.worksheet.format('A1:I1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })
            
            logger.info("Headers setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup headers: {e}")
    
    async def add_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Добавление нового лида в таблицу"""
        if not self.worksheet:
            logger.error("Worksheet not initialized")
            return False
            
        try:
            # Подготовка данных для вставки
            row_data = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                lead_data.get('name', ''),
                lead_data.get('phone', ''),
                lead_data.get('segment', ''),
                lead_data.get('action', ''),
                lead_data.get('username', ''),
                str(lead_data.get('user_id', '')),
                'Новый',
                f"Источник: Telegram Bot"
            ]
            
            # Добавление строки
            self.worksheet.append_row(row_data)
            
            logger.info(f"Lead added to Google Sheets: {lead_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add lead to Google Sheets: {e}")
            return False
    
    async def update_lead_fus(self, phone: str, status: str, notes: str = "") -> bool:
        """Обновление статуса лида"""
        if not self.worksheet:
            return False
            
        try:
            # Находим строку с данным номером телефона
            all_records = self.worksheet.get_all_records()
            
            for idx, record in enumerate(all_records, start=2):  # +2 т.к. индексация с 1 + заголовок
                if record.get('Телефон') == phone:
                    # Обновляем статус и примечания
                    self.worksheet.update_cell(idx, 8, status)  # Колонка "Статус"
                    if notes:
                        current_notes = record.get('Примечания', '')
                        updated_notes = f"{current_notes}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {notes}"
                        self.worksheet.update_cell(idx, 9, updated_notes)  # Колонка "Примечания"
                    
                    logger.info(f"Updated lead status: {phone} -> {status}")
                    return True
            
            logger.warning(f"Lead not found for phone: {phone}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update lead status: {e}")
            return False
    
    async def get_leads_count(self) -> int:
        """Получение количества лидов"""
        try:
            if not self.worksheet:
                return 0
            return len(self.worksheet.get_all_records())
        except Exception as e:
            logger.error(f"Failed to get leads count: {e}")
            return 0

# Глобальный экземпляр менеджера
sheets_manager: Optional[GoogleSheetsManager] = None

async def init_google_sheets():
    """Инициализация Google Sheets"""
    global sheets_manager
    
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google_credentials.json')
    spreadsheet_name = os.getenv('GOOGLE_SPREADSHEET_NAME', 'SignContract Leads')
    
    sheets_manager = GoogleSheetsManager(credentials_path, spreadsheet_name)
    success = await sheets_manager.init_connection()
    
    if success:
        logger.info("Google Sheets integration ready")
    else:
        logger.error("Google Sheets integration failed")
        sheets_manager = None
    
    return success

async def save_lead_to_sheets(user_data: Dict[str, Any], name: str, phone: str, action: str):
    """Сохранение лида в Google Sheets"""
    if not sheets_manager:
        logger.error("Google Sheets not initialized")
        return False
    
    lead_data = {
        'name': name,
        'phone': phone,
        'segment': user_data.get('segment', 'unknown'),
        'action': action,
        'username': user_data.get('username', ''),
        'user_id': user_data.get('user_id', ''),
    }
    
    return await sheets_manager.add_lead(lead_data)

# async def update_lead_status_in_sheets(phone: str, status: str, notes: str = ""):
#     """Обновление статуса лида в Google Sheets"""
#     if not sheets_manager:
#         return False
    
#     return await sheets_manager.update_lead_status(phone, status, notes)


async def get_leads_statistics():
    """Получение статистики лидов"""
    if not sheets_manager:
        return None
    
    try:
        # all records тип List[Dict[str,Union[int,float,str]]]
        # dict {} key-value
        # list [] mutable
        # tuple () immutable
        # Union значит либо int , libo float , libo str
        # Union(str,None) libo str libo None, mozhno ispolzovat Optional(str) libo str,libo None
        all_records = sheets_manager.worksheet.get_all_records()
        
        # Dict[segmnet(str),count(int)]
        segments = {}
        actions = {}
        statuses = {}
        
        for record in all_records:
            segment = record.get('Сегмент', 'unknown')
            segments[segment] = segments.get(segment, 0) + 1
            
            action = record.get('Действие', 'unknown')
            actions[action] = actions.get(action, 0) + 1
            
            status = record.get('Статус', 'unknown')
            statuses[status] = statuses.get(status, 0) + 1
        
        # Dict[str,dict[str,int]]
        return {
            'total_leads': len(all_records),
            'by_segment': segments,
            'by_action': actions,
            'by_status': statuses
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return None
    