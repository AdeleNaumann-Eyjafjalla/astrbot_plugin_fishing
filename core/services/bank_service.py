import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..repositories.abstract_repository import (
    AbstractUserRepository,
    AbstractBankRepository,
    AbstractItemTemplateRepository
)

class BankService:
    def __init__(
        self,
        user_repo: AbstractUserRepository,
        bank_repo: AbstractBankRepository,
        item_template_repo: AbstractItemTemplateRepository,
        config: Dict[str, Any]
    ):
        self.user_repo = user_repo
        self.bank_repo = bank_repo
        self.item_template_repo = item_template_repo
        self.config = config

    def deposit(self, user_id: str, amount: int) -> Dict[str, Any]:
        """存钱到银行"""
        if amount <= 0:
            return {"success": False, "message": "存款金额必须大于0"}

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        if user.coins < amount:
            return {"success": False, "message": f"金币不足，当前持有 {user.coins} 金币"}

        # 更新用户金币和银行存款
        user.coins -= amount
        
        # 获取或创建银行账户
        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account:
            bank_account = self._create_new_account(user_id)
        
        bank_account.balance += amount
        bank_account.last_deposit_date = datetime.now()
        
        # 保存更改
        self.user_repo.update(user)
        self.bank_repo.create_or_update(bank_account)

        return {
            "success": True,
            "message": f"成功存入 {amount} 金币到银行",
            "new_balance": bank_account.balance
        }

    def withdraw(self, user_id: str, amount: int) -> Dict[str, Any]:
        """从银行取钱"""
        if amount <= 0:
            return {"success": False, "message": "取款金额必须大于0"}

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account:
            return {"success": False, "message": "您还没有银行账户"}

        if bank_account.balance < amount:
            return {"success": False, "message": f"银行余额不足，当前余额 {bank_account.balance} 金币"}

        # 检查是否有贷款（不能有未还贷款时取款）
        if bank_account.loan_amount > 0:
            loan_days = (datetime.now() - bank_account.loan_start_date).days if bank_account.loan_start_date else 0
            if loan_days < 3:  # 贷款后3天内不能取款
                return {"success": False, "message": f"贷款后3天内无法取款，还需等待 {3 - loan_days} 天"}

        # 更新银行账户和用户金币
        bank_account.balance -= amount
        user.coins += amount

        self.bank_repo.create_or_update(bank_account)
        self.user_repo.update(user)

        return {
            "success": True,
            "message": f"成功从银行取出 {amount} 金币",
            "new_balance": bank_account.balance
        }

    def loan(self, user_id: str, amount: int) -> Dict[str, Any]:
        """向银行贷款"""
        if amount <= 0:
            return {"success": False, "message": "贷款金额必须大于0"}

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account:
            bank_account = self._create_new_account(user_id)

        # 检查是否已有贷款
        if bank_account.loan_amount > 0:
            return {"success": False, "message": "您已有未还贷款，请先还清后再申请新贷款"}

        # 计算最大贷款额度（历史最高持有金币的10%）
        max_loan = int(user.highest_coins_held * 0.1)
        if amount > max_loan:
            return {"success": False, "message": f"超出贷款额度，最大可贷 {max_loan} 金币"}

        # 更新账户
        bank_account.loan_amount = amount
        bank_account.loan_start_date = datetime.now()
        bank_account.total_repaid = 0  # 已还金额
        
        user.coins += amount

        self.bank_repo.create_or_update(bank_account)
        self.user_repo.update(user)

        return {
            "success": True,
            "message": f"成功贷款 {amount} 金币，贷款将在3天后开始计息",
            "loan_amount": amount
        }

    def repay(self, user_id: str) -> Dict[str, Any]:
        """还款"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account or bank_account.loan_amount <= 0:
            return {"success": False, "message": "您没有未还贷款"}

        # 检查贷款是否已过免还款期（3天）
        if not bank_account.loan_start_date:
            return {"success": False, "message": "贷款信息异常"}
            
        loan_days = (datetime.now() - bank_account.loan_start_date).days
        if loan_days < 3:
            return {"success": False, "message": f"贷款后3天内无法还款，还需等待 {3 - loan_days} 天"}

        # 计算应还总额（本金+利息）
        total_due = self._calculate_total_due(bank_account)
        
        if user.coins < total_due:
            return {"success": False, "message": f"金币不足，需要 {total_due} 金币还款，当前持有 {user.coins} 金币"}

        # 扣除还款金额
        user.coins -= total_due
        bank_account.total_repaid = total_due
        bank_account.loan_amount = 0
        bank_account.loan_start_date = None

        self.user_repo.update(user)
        self.bank_repo.create_or_update(bank_account)

        return {
            "success": True,
            "message": f"成功还款 {total_due} 金币，贷款已结清"
        }

    def query_bank_balance(self, user_id: str) -> Dict[str, Any]:
        """查询银行余额"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account:
            return {"success": False, "message": "您还没有银行账户"}

        return {
            "success": True,
            "balance": bank_account.balance,
            "last_deposit_date": bank_account.last_deposit_date.isoformat() if bank_account.last_deposit_date else None
        }

    def query_deposit_interest_rate(self) -> Dict[str, Any]:
        """查询存款利率"""
        # 存款利率为2%~3%波动
        import random
        rate = round(random.uniform(0.02, 0.03), 4)
        return {
            "success": True,
            "rate": rate,
            "rate_percent": f"{rate * 100:.2f}%"
        }

    def query_loan_info(self, user_id: str) -> Dict[str, Any]:
        """查询贷款信息"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        bank_account = self.bank_repo.get_by_id(user_id)
        if not bank_account or bank_account.loan_amount <= 0:
            return {"success": False, "message": "您没有未还贷款"}

        total_due = self._calculate_total_due(bank_account)
        days_since_loan = (datetime.now() - bank_account.loan_start_date).days if bank_account.loan_start_date else 0

        return {
            "success": True,
            "loan_amount": bank_account.loan_amount,
            "total_due": total_due,
            "repaid_amount": bank_account.total_repaid,
            "days_since_loan": days_since_loan,
            "loan_start_date": bank_account.loan_start_date.isoformat() if bank_account.loan_start_date else None
        }

    def query_loan_interest_rate(self) -> Dict[str, Any]:
        """查询贷款利率"""
        # 贷款利率为4%~5%波动
        import random
        rate = round(random.uniform(0.04, 0.05), 4)
        return {
            "success": True,
            "rate": rate,
            "rate_percent": f"{rate * 100:.2f}%"
        }

    def check_blacklist(self, user_id: str) -> bool:
        """检查用户是否在黑名单中"""
        bank_account = self.bank_repo.get_by_id(user_id)
        return bank_account.blacklisted if bank_account else False

    def get_blacklist(self) -> list:
        """获取黑名单"""
        return self.bank_repo.get_blacklist()

    def process_daily_interest(self):
        """处理每日利息（存款利息和贷款利息）"""
        accounts = self.bank_repo.get_all_accounts()
        
        for account in accounts:
            user = self.user_repo.get_by_id(account.user_id)
            
            # 处理存款利息
            if account.balance > 0 and account.last_deposit_date:
                days_deposited = (datetime.now() - account.last_deposit_date).days
                if days_deposited >= 1:  # 存入次日开始计息
                    deposit_rate = self.query_deposit_interest_rate()["rate"]
                    interest = int(account.balance * deposit_rate)
                    account.balance += interest
                    
                    # 更新账户余额
                    self.bank_repo.create_or_update(account)

            # 处理贷款利息
            if account.loan_amount > 0 and account.loan_start_date:
                days_since_loan = (datetime.now() - account.loan_start_date).days
                if days_since_loan >= 3:  # 贷款后第4天开始计息
                    loan_rate = self.query_loan_interest_rate()["rate"]
                    interest = int(account.loan_amount * loan_rate)
                    
                    # 检查是否超过本金100%
                    total_with_interest = account.loan_amount + interest
                    if total_with_interest > account.loan_amount * 2:  # 超过本金100%
                        # 停止计息，尝试扣除
                        self._attempt_deduction_for_overdue_loan(account, user)
                    else:
                        # 更新贷款总额
                        account.loan_amount += interest
                        self.bank_repo.create_or_update(account)

    def _calculate_total_due(self, account) -> int:
        """计算应还总额"""
        if not account.loan_start_date:
            return account.loan_amount
            
        days_since_loan = (datetime.now() - account.loan_start_date).days
        if days_since_loan < 3:
            return account.loan_amount  # 3天内只还本金

        # 计算利息
        total_with_interest = account.loan_amount
        for day in range(3, days_since_loan + 1):
            loan_rate = self.query_loan_interest_rate()["rate"]
            total_with_interest = int(total_with_interest * (1 + loan_rate))
            
            # 检查是否超过本金100%
            if total_with_interest >= account.loan_amount * 2:
                break
                
        return total_with_interest

    def _attempt_deduction_for_overdue_loan(self, account, user):
        """尝试扣除逾期贷款"""
        if user and user.coins >= account.loan_amount:
            # 从用户金币中扣除贷款
            user.coins -= account.loan_amount
            account.loan_amount = 0
            account.loan_start_date = None
            account.total_repaid = account.loan_amount
            
            self.user_repo.update(user)
            self.bank_repo.create_or_update(account)
        else:
            # 加入黑名单
            account.blacklisted = True
            self.bank_repo.create_or_update(account)

    def _create_new_account(self, user_id: str) -> "BankAccount":
        """创建新银行账户"""
        from ..domain.models import BankAccount
        account = BankAccount()
        account.user_id = user_id
        account.balance = 0
        account.loan_amount = 0
        account.total_repaid = 0
        account.blacklisted = False
        return account