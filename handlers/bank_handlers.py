from astrbot.api.event import AstrMessageEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import FishingPlugin

async def bank_deposit(self: "FishingPlugin", event: AstrMessageEvent):
    """存钱到银行"""
    args = event.message_str.split()
    if len(args) < 2:
        yield event.plain_result("❌ 用法：/存钱 <金额>")
    
    try:
        amount = int(args[1])
        result = self.bank_service.deposit(self._get_effective_user_id(event), amount)
        yield event.plain_result(f"{'✅' if result['success'] else '❌'} {result['message']}")
    except ValueError:
        yield event.plain_result("❌ 请输入正确的金额")

async def bank_withdraw(self: "FishingPlugin", event: AstrMessageEvent):
    """从银行取钱"""
    args = event.message_str.split()
    if len(args) < 2:
        yield event.plain_result("❌ 用法：/取钱 <金额>")
    
    try:
        amount = int(args[1])
        result = self.bank_service.withdraw(self._get_effective_user_id(event), amount)
        yield event.plain_result(f"{'✅' if result['success'] else '❌'} {result['message']}")
    except ValueError:
        yield event.plain_result("❌ 请输入正确的金额")

async def bank_loan(self: "FishingPlugin", event: AstrMessageEvent):
    """向银行贷款"""
    args = event.message_str.split()
    if len(args) < 2:
        yield event.plain_result("❌ 用法：/贷款 <金额>")
    
    try:
        amount = int(args[1])
        result = self.bank_service.loan(self._get_effective_user_id(event), amount)
        yield event.plain_result(f"{'✅' if result['success'] else '❌'} {result['message']}")
    except ValueError:
        yield event.plain_result("❌ 请输入正确的金额")

async def bank_repay(self: "FishingPlugin", event: AstrMessageEvent):
    """还款"""
    result = self.bank_service.repay(self._get_effective_user_id(event))
    yield event.plain_result(f"{'✅' if result['success'] else '❌'} {result['message']}")

async def bank_query_balance(self: "FishingPlugin", event: AstrMessageEvent):
    """查询银行余额"""
    result = self.bank_service.query_bank_balance(self._get_effective_user_id(event))
    if result['success']:
        yield event.plain_result(f"🏦 银行余额：{result['balance']} 金币")
    else:
        yield event.plain_result(f"❌ {result['message']}")

async def bank_query_deposit_rate(self: "FishingPlugin", event: AstrMessageEvent):
    """查询存款利率"""
    result = self.bank_service.query_deposit_interest_rate()
    yield event.plain_result(f"📈 当前存款利率：{result['rate_percent']}")

async def bank_query_loan(self: "FishingPlugin", event: AstrMessageEvent):
    """查询贷款信息"""
    result = self.bank_service.query_loan_info(self._get_effective_user_id(event))
    if result['success']:
        yield event.plain_result(
            f"💳 贷款信息：\n"
            f"贷款本金：{result['loan_amount']} 金币\n"
            f"应还总额：{result['total_due']} 金币\n"
            f"已还金额：{result['repaid_amount']} 金币\n"
            f"贷款天数：{result['days_since_loan']} 天"
        )
    else:
        yield event.plain_result(f"❌ {result['message']}")

async def bank_query_loan_rate(self: "FishingPlugin", event: AstrMessageEvent):
    """查询贷款利率"""
    result = self.bank_service.query_loan_interest_rate()
    yield event.plain_result(f"📈 当前贷款利率：{result['rate_percent']}")

async def bank_query_blacklist(self: "FishingPlugin", event: AstrMessageEvent):
    """查询失信名单"""
    blacklist = self.bank_service.get_blacklist()
    if not blacklist:
        yield event.plain_result("📋 失信名单为空")
    else:
        message = "📋 失信名单：\n"
        for user_id in blacklist:
            message += f"- {user_id}\n"
        yield event.plain_result(message)

async def bank_help(self: "FishingPlugin", event: AstrMessageEvent):
    """银行帮助信息"""
    message = """【🏦 银行系统帮助】：

🔹 银行是一个安全的资金存放空间，放入银行的金币不会产生行为消耗，如电鱼、擦弹、命运之轮等
🔹 存入银行的金币于存入次日可享受每日存款利息，存款利率为2%~3%波动
🔹 可以向银行贷款金币，贷款额度=历史最高持有金币的10%
🔹 同一时间只能进行一次金币贷款，当身上有债务存在时无法二次贷款
🔹 成功贷款的后一日起开始计息，每日利率为4%~5%波动
🔹 借款日起的后三日内不可还款，不支持分期还款
🔹 当欠款超过借款的100%时停止计息，银行会于次日0点尝试从当前持有金币扣除全部欠款，若扣除失败，银行将自动收缴玩家所有的道具并录入失信名单
🔹 处于失信名单的玩家获得的金币时会自动扣除其中的80%所得，且不可参与擦弹、命运之轮、竞猜、抽卡活动，直至还清所有欠款方可移出失信名单

📋 可用命令：
• /存钱 <数量> - 存入银行 <数量> 金币
• /取钱 <数量> - 从银行取出金币
• /贷款 <数量> - 向银行贷款 <数量> 金币
• /还款  - 全额还款
• /查询存款 - 查询银行余额
• /查询存款利率 - 查询存款利率
• /查询贷款 - 查询贷款情况
• /查询贷款利率 - 查询贷款利率
• /查询失信名单 - 查询失信名单
• /银行 帮助 - 显示此帮助信息
"""
    yield event.plain_result(message)