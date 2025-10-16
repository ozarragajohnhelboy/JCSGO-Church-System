import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings


class GoogleSheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS not found in environment variables")
        
        try:
            credentials_info = json.loads(credentials_json)
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)
        except Exception as e:
            raise ValueError(f"Failed to initialize Google Sheets credentials: {str(e)}")
    
    def create_spreadsheet(self, title):
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            return spreadsheet.get('spreadsheetId'), spreadsheet.get('spreadsheetUrl')
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def update_values(self, spreadsheet_id, range_name, values):
        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            return result
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def clear_sheet(self, spreadsheet_id, range_name):
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def format_sheet(self, spreadsheet_id, sheet_id, requests):
        try:
            body = {
                'requests': requests
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def get_or_create_church_report_sheet(self, church):
        title = f"{church.name} - Church Report"
        if getattr(church, 'google_sheet_id', None):
            try:
                self.service.spreadsheets().get(spreadsheetId=church.google_sheet_id).execute()
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{church.google_sheet_id}"
                return church.google_sheet_id, spreadsheet_url
            except HttpError:
                pass
        env_key = f'GOOGLE_SHEET_{church.name.upper().replace(" ", "_")}'
        spreadsheet_id = os.getenv(env_key)
        if spreadsheet_id:
            try:
                self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                church.google_sheet_id = spreadsheet_id
                church.save(update_fields=['google_sheet_id'])
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                return spreadsheet_id, spreadsheet_url
            except HttpError:
                pass
        spreadsheet_id, spreadsheet_url = self.create_spreadsheet(title)
        church.google_sheet_id = spreadsheet_id
        church.save(update_fields=['google_sheet_id'])
        return spreadsheet_id, spreadsheet_url
    
    def export_church_report(self, church, demographic_stats, sunday_attendance_stats, target_2025, new_believers_stats=None):
        spreadsheet_id, spreadsheet_url = self.get_or_create_church_report_sheet(church)
        
        try:
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            if sheets:
                sheet_title = sheets[0].get('properties', {}).get('title', 'Sheet1')
            else:
                sheet_title = 'Sheet1'
        except HttpError:
            sheet_title = 'Sheet1'
        
        headers = [
            ['Church Report'],
            [f'Church: {church.name}'],
            [f'Location: {church.location}'],
            [''],
            ['Category', '2025 Target', 'Onsite/Actual', 'Online', 'TOTAL']
        ]
        
        data = []
        
        data.append(['2025 Target', target_2025['registered_disciples'], '', '', ''])
        
        data.append([
            'Registered Disciples',
            target_2025['registered_disciples'],
            demographic_stats['registered_disciples']['total'],
            0,
            demographic_stats['registered_disciples']['total']
        ])
        
        data.append([
            'Youth Men',
            target_2025['youth_men'],
            demographic_stats['registered_disciples']['youth_men'],
            0,
            demographic_stats['registered_disciples']['youth_men']
        ])
        
        data.append([
            'Youth Women',
            target_2025['youth_women'],
            demographic_stats['registered_disciples']['youth_women'],
            0,
            demographic_stats['registered_disciples']['youth_women']
        ])
        
        data.append([
            'Men',
            target_2025['men'],
            demographic_stats['registered_disciples']['men'],
            0,
            demographic_stats['registered_disciples']['men']
        ])
        
        data.append([
            'Women',
            target_2025['women'],
            demographic_stats['registered_disciples']['women'],
            0,
            demographic_stats['registered_disciples']['women']
        ])
        
        data.append([''])
        
        data.append([
            'Sunday Attendance',
            '',
            sunday_attendance_stats['sunday_attendance']['total'],
            0,
            sunday_attendance_stats['sunday_attendance']['total']
        ])
        
        data.append([
            'Youth Men',
            '',
            sunday_attendance_stats['sunday_attendance']['youth_men'],
            0,
            sunday_attendance_stats['sunday_attendance']['youth_men']
        ])
        
        data.append([
            'Youth Women',
            '',
            sunday_attendance_stats['sunday_attendance']['youth_women'],
            0,
            sunday_attendance_stats['sunday_attendance']['youth_women']
        ])
        
        data.append([
            'Men',
            '',
            sunday_attendance_stats['sunday_attendance']['men'],
            0,
            sunday_attendance_stats['sunday_attendance']['men']
        ])
        
        data.append([
            'Women',
            '',
            sunday_attendance_stats['sunday_attendance']['women'],
            0,
            sunday_attendance_stats['sunday_attendance']['women']
        ])
        
        if new_believers_stats:
            data.append([''])
            data.append(['II. New Believers', '', '', '', ''])
            data.append(['1st Timers', '', new_believers_stats.get('first_timers', 0), '', new_believers_stats.get('first_timers', 0)])
            data.append(['2nd Timers', '', new_believers_stats.get('second_timers', 0), '', new_believers_stats.get('second_timers', 0)])
            data.append(['3rd Timers', '', new_believers_stats.get('third_timers', 0), '', new_believers_stats.get('third_timers', 0)])
            data.append(['4th Timers', '', new_believers_stats.get('fourth_timers', 0), '', new_believers_stats.get('fourth_timers', 0)])
            data.append(['5th Timers/Conversion', '', new_believers_stats.get('fifth_timers_conversion', 0), '', new_believers_stats.get('fifth_timers_conversion', 0)])
            data.append(['Power Filled Life', '', new_believers_stats.get('power_filled_life', 0), '', new_believers_stats.get('power_filled_life', 0)])
            data.append(['Water Baptism', '', new_believers_stats.get('water_baptism', 0), '', new_believers_stats.get('water_baptism', 0)])
        all_values = headers + data
        
        self.clear_sheet(spreadsheet_id, f'{sheet_title}!A1:Z1000')
        self.update_values(spreadsheet_id, f'{sheet_title}!A1', all_values)
        
        formatting_requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.0, 'green': 0.48, 'blue': 1.0},
                            'textFormat': {
                                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                'fontSize': 16,
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            },
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 4,
                        'endRowIndex': 5,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                            'textFormat': {
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            }
        ]
        
        self.format_sheet(spreadsheet_id, 0, formatting_requests)
        
        return spreadsheet_url

