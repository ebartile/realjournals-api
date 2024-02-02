import enum
from django.utils.translation import gettext_lazy as _

ADMIN_PAGE_CHOICES = (
    ("admin.dashboard", _("Terminal Dashboard")),
)

TERMINAL_PAGE_CHOICES = (
    ("terminal.dashboard", _("Terminal Dashboard")),
    ("terminal.journal", _("Terminal Journal")),
)

TERMINAL_MODULES_CHOICES = (
    ('welcome', 'Welcome'),
    ('total_trades', 'Total Trades'),
    ('winners', 'Winners'),
    ('lossers', 'Lossers'),
    ('trade_allocation', 'Trade Allocation'),
    ('account_margin', 'Account Margin'),
    ('account_leverage', 'Account Leverage'),
    ('account_free_margin', 'Account Free Margin'),
    ('account_profit', 'Account Profit'),

    ('invite_member_card', 'Invite Member'),
    ('net_profit_loss', 'Net Profit and Loss'),
    ('trade_win_percentage', 'Trade Win Percentage'),
    ('profit_factor', 'Profit Factor'),
    ('day_win_percentage', 'Day Win Percentage'),
    ('average_win_loss_trade', 'Average Win/Loss Trade'),
    ('daily_net_cummulative_profit_loss', 'Daily Net Cummulative Profit & Loss'),
    ('net_daily_profit_loss', 'Net Daily Profit & Loss'),
    ('recent_timeline', 'Recent Timeline'),
    ('recent_trades', 'Recent Trades'),
    ('calendar', 'Calendar'),
    ('account_balance', 'Account Balance'),
    ('account_balance_chart', 'Account Balance Chart'),
)

ADMIN_MODULES_CHOICES = (
    ('latest_users', 'Latest Users'),
    ('registration_chart', 'Registration Chart'),
    ('system_status', 'System Status'),
    ('earning_summary', 'Earning Summary')
)