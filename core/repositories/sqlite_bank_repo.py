import sqlite3
from datetime import datetime
from typing import List, Optional
from .abstract_repository import AbstractBankRepository, BankAccount

class SqliteBankRepository(AbstractBankRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    user_id TEXT PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    loan_amount INTEGER DEFAULT 0,
                    loan_start_date TEXT,
                    total_repaid INTEGER DEFAULT 0,
                    last_deposit_date TEXT,
                    blacklisted INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def get_by_id(self, user_id: str) -> Optional[BankAccount]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, balance, loan_amount, loan_start_date, total_repaid, last_deposit_date, blacklisted "
                "FROM bank_accounts WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
                
            account = BankAccount()
            account.user_id = row[0]
            account.balance = row[1]
            account.loan_amount = row[2]
            account.loan_start_date = datetime.fromisoformat(row[3]) if row[3] else None
            account.total_repaid = row[4]
            account.last_deposit_date = datetime.fromisoformat(row[5]) if row[5] else None
            account.blacklisted = bool(row[6])
            
            return account

    def create_or_update(self, account: BankAccount) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO bank_accounts 
                (user_id, balance, loan_amount, loan_start_date, total_repaid, last_deposit_date, blacklisted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                account.user_id,
                account.balance,
                account.loan_amount,
                account.loan_start_date.isoformat() if account.loan_start_date else None,
                account.total_repaid,
                account.last_deposit_date.isoformat() if account.last_deposit_date else None,
                int(account.blacklisted)
            ))
            conn.commit()

    def get_all_accounts(self) -> List[BankAccount]:
        accounts = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, balance, loan_amount, loan_start_date, total_repaid, last_deposit_date, blacklisted "
                "FROM bank_accounts"
            )
            rows = cursor.fetchall()
            
            for row in rows:
                account = BankAccount()
                account.user_id = row[0]
                account.balance = row[1]
                account.loan_amount = row[2]
                account.loan_start_date = datetime.fromisoformat(row[3]) if row[3] else None
                account.total_repaid = row[4]
                account.last_deposit_date = datetime.fromisoformat(row[5]) if row[5] else None
                account.blacklisted = bool(row[6])
                accounts.append(account)
                
        return accounts

    def get_blacklist(self) -> List[str]:
        blacklist = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM bank_accounts WHERE blacklisted = 1")
            rows = cursor.fetchall()
            blacklist = [row[0] for row in rows]
        return blacklist