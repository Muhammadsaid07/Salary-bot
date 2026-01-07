"""
Database handler for storing teacher accounts and access codes
"""
import threading
import sqlite3
import secrets
import string
import os
import shutil
from datetime import datetime
from typing import Optional, List, Tuple
from config import DATABASE_FILE, ACCESS_CODE_LENGTH, BACKUP_DIR, BACKUP_ENABLED



class Database:
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.backup_dir = BACKUP_DIR
        if BACKUP_ENABLED:
            self._ensure_backup_dir()
        self.init_database()
    
    def _ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create teachers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                access_code TEXT NOT NULL UNIQUE,
                failed_attempts INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def generate_access_code(self) -> str:
        """Generate a unique access code"""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(ACCESS_CODE_LENGTH))
            if not self.access_code_exists(code):
                return code

    def access_code_exists(self, code: str) -> bool:
        """Check if an access code already exists"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM teachers WHERE access_code = ?', (code,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def create_teacher(self, name: str) -> Optional[str]:
        """Create a new teacher account and return the access code"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            # Check if teacher name already exists
            cursor.execute('SELECT 1 FROM teachers WHERE name = ?', (name,))
            if cursor.fetchone():
                conn.close()
                return None
            
            # Generate unique access code
            access_code = self.generate_access_code()
            
            # Insert teacher
            cursor.execute('''
                INSERT INTO teachers (name, access_code)
                VALUES (?, ?)
            ''', (name, access_code))
            
            conn.commit()
            conn.close()
            return access_code
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def delete_teacher(self, name: str) -> bool:
        """Delete a teacher account"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM teachers WHERE name = ?', (name,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_teacher_by_code(self, access_code: str) -> Optional[Tuple[int, str]]:
        """Get teacher ID and name by access code. Returns (id, name) or None"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, is_blocked FROM teachers WHERE access_code = ?', (access_code,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            teacher_id, name, is_blocked = result
            if is_blocked:
                return None  # Teacher is blocked
            return (teacher_id, name)
        return None

    def reset_access_code(self, name: str) -> Optional[str]:
        """Reset access code for a teacher and return the new code"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Check if teacher exists
        cursor.execute('SELECT 1 FROM teachers WHERE name = ?', (name,))
        if not cursor.fetchone():
            conn.close()
            return None
        
        # Generate new access code
        new_code = self.generate_access_code()
        
        # Update access code and reset failed attempts
        cursor.execute('''
            UPDATE teachers 
            SET access_code = ?, failed_attempts = 0, is_blocked = 0
            WHERE name = ?
        ''', (new_code, name))
        
        conn.commit()
        conn.close()
        return new_code

    def increment_failed_attempts(self, access_code: str) -> Tuple[int, bool]:
        """Increment failed login attempts. Returns (current_attempts, is_blocked)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT failed_attempts FROM teachers WHERE access_code = ?', (access_code,))
        result = cursor.fetchone()
        
        if result:
            failed_attempts = result[0] + 1
            is_blocked = failed_attempts >= 5
            
            cursor.execute('''
                UPDATE teachers 
                SET failed_attempts = ?, is_blocked = ?
                WHERE access_code = ?
            ''', (failed_attempts, 1 if is_blocked else 0, access_code))
            
            conn.commit()
            conn.close()
            return (failed_attempts, is_blocked)
        
        conn.close()
        return (0, False)

    def reset_failed_attempts(self, access_code: str):
        """Reset failed attempts after successful login"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE teachers 
            SET failed_attempts = 0
            WHERE access_code = ?
        ''', (access_code,))
        conn.commit()
        conn.close()

    def get_all_teachers(self) -> List[Tuple[str, str]]:
        """Get all teachers with their access codes. Returns list of (name, access_code)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT name, access_code FROM teachers ORDER BY name')
        teachers = cursor.fetchall()
        conn.close()
        return teachers

    def unblock_teacher(self, name: str) -> bool:
        """Unblock a teacher account"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE teachers 
            SET is_blocked = 0, failed_attempts = 0
            WHERE name = ?
        ''', (name,))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    
    def create_backup(self) -> Optional[str]:
        """Create a backup of the database. Returns backup file path or None on error"""
        if not BACKUP_ENABLED:
            return None
        
        try:
            if not os.path.exists(self.db_file):
                return None
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"teachers_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy database file
            shutil.copy2(self.db_file, backup_path)
            
            # Keep only last 10 backups (optional cleanup)
            self._cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            return None
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Keep only the most recent backups, delete older ones"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # Get all backup files sorted by modification time
            backup_files = [
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith("teachers_backup_") and f.endswith(".db")
            ]
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Delete old backups
            for backup_file in backup_files[keep_count:]:
                try:
                    os.remove(backup_file)
                except Exception:
                    pass
        except Exception:
            pass
    
    def get_backup_list(self) -> List[Tuple[str, str, str]]:
        """Get list of available backups. Returns list of (filename, path, size)"""
        backups = []
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("teachers_backup_") and filename.endswith(".db"):
                    filepath = os.path.join(self.backup_dir, filename)
                    size = os.path.getsize(filepath)
                    size_str = self._format_file_size(size)
                    backups.append((filename, filepath, size_str))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
        except Exception:
            pass
        
        return backups
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

