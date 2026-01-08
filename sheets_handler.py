import csv
import requests
from typing import Optional, Dict
import config

class SheetsHandler:
    def __init__(self):
        self.spreadsheet_id = config.SPREADSHEET_ID

    def get_all_data(self) -> list:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid={config.SHEET_GID}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return list(csv.reader(response.content.decode("utf-8").splitlines()))
        except Exception as e:
            raise Exception(f"Connection Error: {str(e)}")

    def find_teacher_row(self, teacher_name: str) -> Optional[Dict[str, any]]:
        data = self.get_all_data()
        name_col = config.COLUMN_MAPPING.get("name", 0)
        search_name = teacher_name.lower().strip()
        
        for row in data:
            if len(row) > name_col and row[name_col].strip().lower() == search_name:
                print(f"DEBUG: Found row for {teacher_name}: {row}")
                return self._extract_salary_data(row, teacher_name)
        return None

    def _extract_salary_data(self, row: list, teacher_name: str) -> Dict[str, any]:
        m = config.COLUMN_MAPPING
        
        def clean_number(key):
            idx = m.get(key)
            if idx is not None and idx < len(row):
                # 1. Convert to string and remove spaces/commas
                raw_val = str(row[idx]).strip().replace(" ", "").replace(",", "")
                
                # 2. Handle Google Sheets "Accounting" format: (792) becomes -792
                if raw_val.startswith('(') and raw_val.endswith(')'):
                    raw_val = '-' + raw_val[1:-1]
                
                # 3. Replace special Unicode dashes with standard minus signs
                raw_val = raw_val.replace('−', '-').replace('–', '-').replace('—', '-')
                
                # 4. CRITICAL FIX: Include '-' in the allowed characters
                clean_val = "".join(c for c in raw_val if c.isdigit() or c == '.' or c == '-')
                
                try:
                    if not clean_val or clean_val == "-":
                        return 0
                    return float(clean_val)
                except ValueError:
                    return 0
            return 0

        return {
            "name": teacher_name,
            "share": str(row[m["share"]]) if "share" in m and m["share"] < len(row) else "N/A",
            "salary": clean_number("salary"),
            "advance": clean_number("advance"),
            "bonus": clean_number("bonus"),
            "penalty": clean_number("penalty"),
            "cover_minus": clean_number("cover_minus"),
            "cover_plus": clean_number("cover_plus"),
            "tax": clean_number("tax"),
            "remains": clean_number("remains"),
        }
    def format_salary_message(self, data: Dict[str, any]) -> str:
        def f(val):
            try:
                return f"{int(float(val)):,}".replace(",", " ")
            except:
                return str(val)

        return (
            f"👤 **Name:** {data['name']}\n"
            f"📊 **Share:** {data['share']}\n"
            f"💰 **Salary:** {f(data['salary'])}\n"
            f"💸 **Advance:** {f(data['advance'])}\n"
            f"🎁 **Bonus:** {f(data['bonus'])}\n"
            f"⚠️ **Penalty:** {f(data['penalty'])}\n"
            f"➖ **Cover Minus:** {f(data['cover_minus'])}\n"
            f"➕ **Cover Plus:** {f(data['cover_plus'])}\n"
            f"🏦 **TAX:** {f(data['tax'])}\n"
            f"🏁 **Net Remains:** {f(data['remains'])}"
        )