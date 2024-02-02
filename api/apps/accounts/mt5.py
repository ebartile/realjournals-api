from logging import getLogger
from django.db import models

logger = getLogger(__name__)

# timeframes
TIMEFRAME_M1                        = 1
TIMEFRAME_M2                        = 2
TIMEFRAME_M3                        = 3
TIMEFRAME_M4                        = 4
TIMEFRAME_M5                        = 5
TIMEFRAME_M6                        = 6
TIMEFRAME_M10                       = 10
TIMEFRAME_M12                       = 12
TIMEFRAME_M15                       = 15
TIMEFRAME_M20                       = 20
TIMEFRAME_M30                       = 30
TIMEFRAME_H1                        = 1  | 0x4000
TIMEFRAME_H2                        = 2  | 0x4000
TIMEFRAME_H4                        = 4  | 0x4000
TIMEFRAME_H3                        = 3  | 0x4000
TIMEFRAME_H6                        = 6  | 0x4000
TIMEFRAME_H8                        = 8  | 0x4000
TIMEFRAME_H12                       = 12 | 0x4000
TIMEFRAME_D1                        = 24 | 0x4000
TIMEFRAME_W1                        = 1  | 0x8000
TIMEFRAME_MN1                       = 1  | 0xC000
# tick copy flags
COPY_TICKS_ALL                      = -1
COPY_TICKS_INFO                     = 1
COPY_TICKS_TRADE                    = 2
# tick flags						  
TICK_FLAG_BID                       = 0x02
TICK_FLAG_ASK                       = 0x04
TICK_FLAG_LAST                      = 0x08
TICK_FLAG_VOLUME                    = 0x10
TICK_FLAG_BUY                       = 0x20
TICK_FLAG_SELL                      = 0x40
# position type, ENUM_POSITION_TYPE
POSITION_TYPE_BUY                   = 0      # Buy
POSITION_TYPE_SELL                  = 1      # Sell
# position reason, ENUM_POSITION_REASON
POSITION_REASON_CLIENT              = 0      # The position was opened as a result of activation of an order placed from a desktop terminal
POSITION_REASON_MOBILE              = 1      # The position was opened as a result of activation of an order placed from a mobile application
POSITION_REASON_WEB                 = 2      # The position was opened as a result of activation of an order placed from the web platform
POSITION_REASON_EXPERT              = 3      # The position was opened as a result of activation of an order placed from an MQL5 program, i.e. an Expert Advisor or a script
# order types, ENUM_ORDER_TYPE
ORDER_TYPE_BUY                      = 0      # Market Buy order
ORDER_TYPE_SELL                     = 1      # Market Sell order
ORDER_TYPE_BUY_LIMIT                = 2      # Buy Limit pending order
ORDER_TYPE_SELL_LIMIT               = 3      # Sell Limit pending order
ORDER_TYPE_BUY_STOP                 = 4      # Buy Stop pending order
ORDER_TYPE_SELL_STOP                = 5      # Sell Stop pending order
ORDER_TYPE_BUY_STOP_LIMIT           = 6      # Upon reaching the order price, a pending Buy Limit order is placed at the StopLimit price
ORDER_TYPE_SELL_STOP_LIMIT          = 7      # Upon reaching the order price, a pending Sell Limit order is placed at the StopLimit price
ORDER_TYPE_CLOSE_BY                 = 8      # Order to close a position by an opposite one
# order state, ENUM_ORDER_STATE
ORDER_STATE_STARTED                 = 0      # Order checked, but not yet accepted by broker
ORDER_STATE_PLACED                  = 1      # Order accepted
ORDER_STATE_CANCELED                = 2      # Order canceled by client
ORDER_STATE_PARTIAL                 = 3      # Order partially executed
ORDER_STATE_FILLED                  = 4      # Order fully executed
ORDER_STATE_REJECTED                = 5      # Order rejected
ORDER_STATE_EXPIRED                 = 6      # Order expired
ORDER_STATE_REQUEST_ADD             = 7      # Order is being registered (placing to the trading system)
ORDER_STATE_REQUEST_MODIFY          = 8      # Order is being modified (changing its parameters)
ORDER_STATE_REQUEST_CANCEL          = 9      # Order is being deleted (deleting from the trading system)
# ENUM_ORDER_TYPE_FILLING
ORDER_FILLING_FOK                   = 0      # Fill Or Kill order
ORDER_FILLING_IOC                   = 1      # Immediately Or Cancel
ORDER_FILLING_RETURN                = 2      # Return remaining volume to book
ORDER_FILLING_BOC                   = 3      # Book Or Cancel order
# ENUM_ORDER_TYPE_TIME
ORDER_TIME_GTC                      = 0      # Good till cancel order
ORDER_TIME_DAY                      = 1      # Good till current trade day order
ORDER_TIME_SPECIFIED                = 2      # Good till expired order
ORDER_TIME_SPECIFIED_DAY            = 3      # The order will be effective till 23:59:59 of the specified day. If this time is outside a trading session, the order expires in the nearest trading time.
# ENUM_ORDER_REASON
ORDER_REASON_CLIENT                 = 0      # The order was placed from a desktop terminal
ORDER_REASON_MOBILE                 = 1      # The order was placed from a mobile application
ORDER_REASON_WEB                    = 2      # The order was placed from a web platform
ORDER_REASON_EXPERT                 = 3      # The order was placed from an MQL5-program, i.e. by an Expert Advisor or a script
ORDER_REASON_SL                     = 4      # The order was placed as a result of Stop Loss activation
ORDER_REASON_TP                     = 5      # The order was placed as a result of Take Profit activation
ORDER_REASON_SO                     = 6      # The order was placed as a result of the Stop Out event
# deal types, ENUM_DEAL_TYPE
DEAL_TYPE_BUY                       = 0      # Buy
DEAL_TYPE_SELL                      = 1      # Sell
DEAL_TYPE_BALANCE                   = 2      # Balance
DEAL_TYPE_CREDIT                    = 3      # Credit
DEAL_TYPE_CHARGE                    = 4      # Additional charge
DEAL_TYPE_CORRECTION                = 5      # Correction
DEAL_TYPE_BONUS                     = 6      # Bonus
DEAL_TYPE_COMMISSION                = 7      # Additional commission
DEAL_TYPE_COMMISSION_DAILY          = 8      # Daily commission
DEAL_TYPE_COMMISSION_MONTHLY        = 9      # Monthly commission
DEAL_TYPE_COMMISSION_AGENT_DAILY    = 10     # Daily agent commission
DEAL_TYPE_COMMISSION_AGENT_MONTHLY  = 11     # Monthly agent commission
DEAL_TYPE_INTEREST                  = 12     # Interest rate
DEAL_TYPE_BUY_CANCELED              = 13     # Canceled buy deal.
DEAL_TYPE_SELL_CANCELED             = 14     # Canceled sell deal.
DEAL_DIVIDEND                       = 15     # Dividend operations
DEAL_DIVIDEND_FRANKED               = 16     # Franked (non-taxable) dividend operations
DEAL_TAX                            = 17     # Tax charges
# ENUM_DEAL_ENTRY
DEAL_ENTRY_IN                       = 0      # Entry in
DEAL_ENTRY_OUT                      = 1      # Entry out
DEAL_ENTRY_INOUT                    = 2      # Reverse
DEAL_ENTRY_OUT_BY                   = 3      # Close a position by an opposite one
# ENUM_DEAL_REASON
DEAL_REASON_CLIENT                  = 0      # The deal was executed as a result of activation of an order placed from a desktop terminal
DEAL_REASON_MOBILE                  = 1      # The deal was executed as a result of activation of an order placed from a mobile application
DEAL_REASON_WEB                     = 2      # The deal was executed as a result of activation of an order placed from the web platform
DEAL_REASON_EXPERT                  = 3      # The deal was executed as a result of activation of an order placed from an MQL5 program, i.e. an Expert Advisor or a script
DEAL_REASON_SL                      = 4      # The deal was executed as a result of Stop Loss activation
DEAL_REASON_TP                      = 5      # The deal was executed as a result of Take Profit activation
DEAL_REASON_SO                      = 6      # The deal was executed as a result of the Stop Out event
DEAL_REASON_ROLLOVER                = 7      # The deal was executed due to a rollover
DEAL_REASON_VMARGIN                 = 8      # The deal was executed after charging the variation margin
DEAL_REASON_SPLIT                   = 9      # The deal was executed after the split (price reduction) of an instrument, which had an open position during split announcement
# ENUM_TRADE_REQUEST_ACTIONS, Trade Operation Types
TRADE_ACTION_DEAL                   = 1      # Place a trade order for an immediate execution with the specified parameters (market order)
TRADE_ACTION_PENDING                = 5      # Place a trade order for the execution under specified conditions (pending order)
TRADE_ACTION_SLTP                   = 6      # Modify Stop Loss and Take Profit values of an opened position
TRADE_ACTION_MODIFY                 = 7      # Modify the parameters of the order placed previously
TRADE_ACTION_REMOVE                 = 8      # Delete the pending order placed previously
TRADE_ACTION_CLOSE_BY               = 10     # Close a position by an opposite one
# ENUM_SYMBOL_CHART_MODE
SYMBOL_CHART_MODE_BID               = 0
SYMBOL_CHART_MODE_LAST              = 1
# ENUM_SYMBOL_CALC_MODE
SYMBOL_CALC_MODE_FOREX              = 0
SYMBOL_CALC_MODE_FUTURES            = 1
SYMBOL_CALC_MODE_CFD                = 2
SYMBOL_CALC_MODE_CFDINDEX           = 3
SYMBOL_CALC_MODE_CFDLEVERAGE        = 4
SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE  = 5
SYMBOL_CALC_MODE_EXCH_STOCKS        = 32
SYMBOL_CALC_MODE_EXCH_FUTURES       = 33
SYMBOL_CALC_MODE_EXCH_OPTIONS       = 34
SYMBOL_CALC_MODE_EXCH_OPTIONS_MARGIN= 36
SYMBOL_CALC_MODE_EXCH_BONDS         = 37
SYMBOL_CALC_MODE_EXCH_STOCKS_MOEX   = 38
SYMBOL_CALC_MODE_EXCH_BONDS_MOEX    = 39
SYMBOL_CALC_MODE_SERV_COLLATERAL    = 64
# ENUM_SYMBOL_TRADE_MODE
SYMBOL_TRADE_MODE_DISABLED          = 0
SYMBOL_TRADE_MODE_LONGONLY          = 1
SYMBOL_TRADE_MODE_SHORTONLY         = 2
SYMBOL_TRADE_MODE_CLOSEONLY         = 3
SYMBOL_TRADE_MODE_FULL              = 4
# ENUM_SYMBOL_TRADE_EXECUTION
SYMBOL_TRADE_EXECUTION_REQUEST      = 0
SYMBOL_TRADE_EXECUTION_INSTANT      = 1
SYMBOL_TRADE_EXECUTION_MARKET       = 2
SYMBOL_TRADE_EXECUTION_EXCHANGE     = 3
# ENUM_SYMBOL_SWAP_MODE
SYMBOL_SWAP_MODE_DISABLED           = 0
SYMBOL_SWAP_MODE_POINTS             = 1
SYMBOL_SWAP_MODE_CURRENCY_SYMBOL    = 2
SYMBOL_SWAP_MODE_CURRENCY_MARGIN    = 3
SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT   = 4
SYMBOL_SWAP_MODE_INTEREST_CURRENT   = 5
SYMBOL_SWAP_MODE_INTEREST_OPEN      = 6
SYMBOL_SWAP_MODE_REOPEN_CURRENT     = 7
SYMBOL_SWAP_MODE_REOPEN_BID         = 8
# ENUM_DAY_OF_WEEK
DAY_OF_WEEK_SUNDAY                  = 0
DAY_OF_WEEK_MONDAY                  = 1
DAY_OF_WEEK_TUESDAY                 = 2
DAY_OF_WEEK_WEDNESDAY               = 3
DAY_OF_WEEK_THURSDAY                = 4
DAY_OF_WEEK_FRIDAY                  = 5
DAY_OF_WEEK_SATURDAY                = 6
# ENUM_SYMBOL_ORDER_GTC_MODE
SYMBOL_ORDERS_GTC                   = 0
SYMBOL_ORDERS_DAILY                 = 1
SYMBOL_ORDERS_DAILY_NO_STOPS        = 2
# ENUM_SYMBOL_OPTION_RIGHT
SYMBOL_OPTION_RIGHT_CALL            = 0
SYMBOL_OPTION_RIGHT_PUT             = 1
# ENUM_SYMBOL_OPTION_MODE
SYMBOL_OPTION_MODE_EUROPEAN         = 0
SYMBOL_OPTION_MODE_AMERICAN         = 1
# ENUM_ACCOUNT_TRADE_MODE
ACCOUNT_TRADE_MODE_DEMO             = 0
ACCOUNT_TRADE_MODE_CONTEST          = 1
ACCOUNT_TRADE_MODE_REAL             = 2
# ENUM_ACCOUNT_STOPOUT_MODE
ACCOUNT_STOPOUT_MODE_PERCENT        = 0
ACCOUNT_STOPOUT_MODE_MONEY          = 1
# ENUM_ACCOUNT_MARGIN_MODE
ACCOUNT_MARGIN_MODE_RETAIL_NETTING  = 0
ACCOUNT_MARGIN_MODE_EXCHANGE        = 1
ACCOUNT_MARGIN_MODE_RETAIL_HEDGING  = 2
# ENUM_BOOK_TYPE
BOOK_TYPE_SELL                      = 1
BOOK_TYPE_BUY                       = 2
BOOK_TYPE_SELL_MARKET               = 3
BOOK_TYPE_BUY_MARKET                = 4
# order send/check return codes
TRADE_RETCODE_REQUOTE               = 10004
TRADE_RETCODE_REJECT                = 10006
TRADE_RETCODE_CANCEL                = 10007
TRADE_RETCODE_PLACED                = 10008
TRADE_RETCODE_DONE                  = 10009
TRADE_RETCODE_DONE_PARTIAL          = 10010
TRADE_RETCODE_ERROR                 = 10011
TRADE_RETCODE_TIMEOUT               = 10012
TRADE_RETCODE_INVALID               = 10013
TRADE_RETCODE_INVALID_VOLUME        = 10014
TRADE_RETCODE_INVALID_PRICE         = 10015
TRADE_RETCODE_INVALID_STOPS         = 10016
TRADE_RETCODE_TRADE_DISABLED        = 10017
TRADE_RETCODE_MARKET_CLOSED         = 10018
TRADE_RETCODE_NO_MONEY              = 10019
TRADE_RETCODE_PRICE_CHANGED         = 10020
TRADE_RETCODE_PRICE_OFF             = 10021
TRADE_RETCODE_INVALID_EXPIRATION    = 10022
TRADE_RETCODE_ORDER_CHANGED         = 10023
TRADE_RETCODE_TOO_MANY_REQUESTS     = 10024
TRADE_RETCODE_NO_CHANGES            = 10025
TRADE_RETCODE_SERVER_DISABLES_AT    = 10026
TRADE_RETCODE_CLIENT_DISABLES_AT    = 10027
TRADE_RETCODE_LOCKED                = 10028
TRADE_RETCODE_FROZEN                = 10029
TRADE_RETCODE_INVALID_FILL          = 10030
TRADE_RETCODE_CONNECTION            = 10031
TRADE_RETCODE_ONLY_REAL             = 10032
TRADE_RETCODE_LIMIT_ORDERS          = 10033
TRADE_RETCODE_LIMIT_VOLUME          = 10034
TRADE_RETCODE_INVALID_ORDER         = 10035
TRADE_RETCODE_POSITION_CLOSED       = 10036
TRADE_RETCODE_INVALID_CLOSE_VOLUME  = 10038
TRADE_RETCODE_CLOSE_ORDER_EXIST     = 10039
TRADE_RETCODE_LIMIT_POSITIONS       = 10040
TRADE_RETCODE_REJECT_CANCEL         = 10041
TRADE_RETCODE_LONG_ONLY             = 10042
TRADE_RETCODE_SHORT_ONLY            = 10043
TRADE_RETCODE_CLOSE_ONLY            = 10044
TRADE_RETCODE_FIFO_CLOSE            = 10045
# functio error codes, last_error()
RES_S_OK                            =1           # generic success
RES_E_FAIL                          =-1          # generic fail
RES_E_INVALID_PARAMS                =-2          # invalid arguments/parameters
RES_E_NO_MEMORY                     =-3          # no memory condition
RES_E_NOT_FOUND                     =-4          # no history
RES_E_INVALID_VERSION               =-5          # invalid version
RES_E_AUTH_FAILED                   =-6          # authorization failed
RES_E_UNSUPPORTED                   =-7          # unsupported method
RES_E_AUTO_TRADING_DISABLED         =-8          # auto-trading disabled
RES_E_INTERNAL_FAIL                 =-10000      # internal IPC general error
RES_E_INTERNAL_FAIL_SEND            =-10001      # internal IPC send failed
RES_E_INTERNAL_FAIL_RECEIVE         =-10002      # internal IPC recv failed
RES_E_INTERNAL_FAIL_INIT            =-10003      # internal IPC initialization fail
RES_E_INTERNAL_FAIL_CONNECT         =-10004      # internal IPC no ipc
RES_E_INTERNAL_FAIL_TIMEOUT         =-10005      # internal timeout

class TradeAction(models.IntegerChoices):
    """TRADE_REQUEST_ACTION Enum.
    
    Attributes:
        DEAL (int): Delete the pending order placed previously Place a trade order for an immediate execution with the
            specified parameters (market order).
        PENDING (int): Delete the pending order placed previously
        SLTP (int): Modify Stop Loss and Take Profit values of an opened position
        MODIFY (int): Modify the parameters of the order placed previously
        REMOVE (int): Delete the pending order placed previously
        CLOSE_BY (int): Close a position by an opposite one 
    """
    DEAL = TRADE_ACTION_DEAL
    PENDING = TRADE_ACTION_PENDING
    SLTP = TRADE_ACTION_SLTP
    MODIFY = TRADE_ACTION_MODIFY
    REMOVE = TRADE_ACTION_REMOVE
    CLOSE_BY = TRADE_ACTION_CLOSE_BY


class OrderState(models.IntegerChoices):
    STARTED = (0, 'Checked, but not yet accepted by broker')
    PLACED = (1, 'Accepted')
    CANCELED = (2, 'Canceled by client')
    PARTIAL = (3, 'Partially executed')
    FILLED = (4, 'Fully executed')
    REJECTED = (5, 'Rejected')
    EXPIRED = (6, 'Expired')
    REQUEST_ADD = (7, 'Is being registered')
    REQUEST_MODIFY = (8, 'Is being modified')
    REQUEST_CANCEL = (9, 'Is being deleted')

class OrderFilling(models.IntegerChoices):
    """ORDER_TYPE_FILLING Enum.
    
    Attributes:
        FOK (int): This execution policy means that an order can be executed only in the specified volume.
            If the necessary amount of a financial instrument is currently unavailable in the market, the order will
            not be executed. The desired volume can be made up of several available offers.

        IOC (int): An agreement to execute a deal at the maximum volume available in the market within the volume
            specified in the order. If the request cannot be filled completely, an order with the available volume will
            be executed, and the remaining volume will be canceled.

        RETURN (int): This policy is used only for market (ORDER_TYPE_BUY and ORDER_TYPE_SELL), limit and stop limit
            orders (ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT,ORDER_TYPE_BUY_STOP_LIMIT and
            ORDER_TYPE_SELL_STOP_LIMIT) and only for the symbols with Market or Exchange execution modes. If filled
            partially, a market or limit order with the remaining volume is not canceled, and is processed further.
            During activation of the ORDER_TYPE_BUY_STOP_LIMIT and ORDER_TYPE_SELL_STOP_LIMIT orders, an appropriate
            limit order ORDER_TYPE_BUY_LIMIT/ORDER_TYPE_SELL_LIMIT with the ORDER_FILLING_RETURN type is created.
    """
    FOK = ORDER_FILLING_FOK
    IOC = ORDER_FILLING_IOC
    RETURN = ORDER_FILLING_RETURN

class OrderTime(models.IntegerChoices):
    """ORDER_TIME Enum.
    
    Attributes:
        GTC (int): Good till cancel order 
        DAY (int): Good till current trade day order 
        SPECIFIED (int): The order is active until the specified date 
        SPECIFIED_DAY (int): The order is active until 23:59:59 of the specified day. If this time appears to be out of
            a trading session, the expiration is processed at the nearest trading time.
    """
    GTC = (ORDER_TIME_GTC, 'Good till cancel order')
    DAY = (ORDER_TIME_DAY, 'Good till current trade day order')
    SPECIFIED = (ORDER_TIME_SPECIFIED, 'Order active until specified date')
    SPECIFIED_DAY = (
        ORDER_TIME_SPECIFIED_DAY,
        'Order active until 23:59:59 of the specified day. If this time is outside of a trading session, expiration is processed at the nearest trading time.'
    )

class OrderType(models.IntegerChoices):
    """ORDER_TYPE Enum.
    
    Attributes:
        BUY (int): Market buy order 
        SELL (int): Market sell order 
        BUY_LIMIT (int): Buy Limit pending order 
        SELL_LIMIT (int): Sell Limit pending order 
        BUY_STOP (int): Buy Stop pending order 
        SELL_STOP (int): Sell Stop pending order 
        BUY_STOP_LIMIT (int): Upon reaching the order price, Buy Limit pending order is placed at StopLimit price 
        SELL_STOP_LIMIT (int): Upon reaching the order price, Sell Limit pending order is placed at StopLimit price 
        CLOSE_BY (int): Order for closing a position by an opposite one 

    Properties:
        opposite (int): Gets the opposite of an order type
    """
    BUY = ORDER_TYPE_BUY
    SELL = ORDER_TYPE_SELL
    BUY_LIMIT = ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = ORDER_TYPE_SELL_LIMIT
    BUY_STOP = ORDER_TYPE_BUY_STOP
    SELL_STOP = ORDER_TYPE_SELL_STOP
    BUY_STOP_LIMIT = ORDER_TYPE_BUY_STOP_LIMIT
    SELL_STOP_LIMIT = ORDER_TYPE_SELL_STOP_LIMIT
    CLOSE_BY = ORDER_TYPE_CLOSE_BY

    @property
    def opposite(self):
        """Gets the opposite of an order type for closing an open position

        Returns:
            int: integer value of opposite order type
        """
        return {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4, 6: 7, 7: 6, 8: 8}[self]


class BookType(models.IntegerChoices):
    """BOOK_TYPE Enum.

    Attributes:
        SELL (int): Sell order (Offer) 
        BUY (int): Buy order (Bid) 
        SELL_MARKET (int): Sell order by Market 
        BUY_MARKET (int): Buy order by Market 
    """
    SELL = BOOK_TYPE_SELL
    BUY = BOOK_TYPE_BUY
    SELL_MARKET = BOOK_TYPE_SELL_MARKET
    BUY_MARKET = BOOK_TYPE_BUY_MARKET


class TimeFrame(models.IntegerChoices):
    """TIMEFRAME Enum.

    Attributes:
        M1 (int): One Minute
        M2 (int): Two Minutes
        M3 (int): Three Minutes
        M4 (int): Four Minutes
        M5 (int): Five Minutes
        M6 (int): Six Minutes
        M10 (int): Ten Minutes
        M15 (int): Fifteen Minutes
        M20 (int): Twenty Minutes
        M30 (int): Thirty Minutes
        H1 (int): One Hour
        H2 (int): Two Hours
        H3 (int): Three Hours
        H4 (int): Four Hours
        H6 (int): Six Hours
        H8 (int): Eight Hours
        D1 (int): One Day
        W1 (int): One Week
        MN1 (int): One Month

    Properties:
        time: return the value of the timeframe object in seconds. Used as a property

    Methods:
        get: get a timeframe object from a time value in seconds
    """

    def __str__(self):
        return self.name

    M1 = TIMEFRAME_M1
    M2 = TIMEFRAME_M2
    M3 = TIMEFRAME_M3
    M4 = TIMEFRAME_M4
    M5 = TIMEFRAME_M5
    M6 = TIMEFRAME_M6
    M10 = TIMEFRAME_M10
    M15 = TIMEFRAME_M15
    M20 = TIMEFRAME_M20
    M30 = TIMEFRAME_M30
    H1 = TIMEFRAME_H1
    H2 = TIMEFRAME_H2
    H3 = TIMEFRAME_H3
    H4 = TIMEFRAME_H4
    H6 = TIMEFRAME_H6
    H8 = TIMEFRAME_H8
    H12 = TIMEFRAME_H12
    D1 = TIMEFRAME_D1
    W1 = TIMEFRAME_W1
    MN1 = TIMEFRAME_MN1

    @property
    def time(self):
        """The number of seconds in a TIMEFRAME

        Returns:
            int: The number of seconds in a TIMEFRAME

        Examples:
            >>> t = TimeFrame.H1
            >>> print(t.time)
            3600
        """
        times = {1: 60, 2: 120, 3: 180, 4: 240, 5: 300, 6: 360, 10: 600, 15: 900, 20: 1200, 30: 1800, 16385: 3600,
                 16386: 7200, 16387: 10800, 16388: 14400, 16390: 21600, 16392: 28800, 16396: 43200, 16408: 86400,
                 32769: 604800, 49153: 2592000}
        return times[self]

    @classmethod
    def get(cls, time: int):
        times = {60: 1, 120: 2, 180: 3, 240: 4, 300: 5, 360: 6, 600: 10, 900: 15, 1200: 20, 1800: 30, 3600: 16385,
                 7200: 16386, 10800: 16387, 14400: 16388, 21600: 16390, 28800: 16392, 43200: 16396, 86400: 16408,
                 604800: 32769, 2592000: 49153}
        return TimeFrame(times[int(time)])


class CopyTicks(models.IntegerChoices):
    """COPY_TICKS Enum. This defines the types of ticks that can be requested using the copy_ticks_from() and
    copy_ticks_range() functions.

    Attributes:
        ALL (int): All ticks 
        INFO (int): Ticks containing Bid and/or Ask price changes 
        TRADE (int): Ticks containing Last and/or Volume price changes 
    """
    ALL = COPY_TICKS_ALL
    INFO = COPY_TICKS_INFO
    TRADE = COPY_TICKS_TRADE


class PositionType(models.IntegerChoices):
    """POSITION_TYPE Enum. Direction of an open position (buy or sell)

    Attributes:
        BUY (int): Buy 
        SELL (int): Sell
    """
    BUY = POSITION_TYPE_BUY
    SELL = POSITION_TYPE_SELL


class PositionReason(models.IntegerChoices):
    """POSITION_REASON Enum. The reason for opening a position is contained in the POSITION_REASON Enum

    Attributes:
       CLIENT (int): The position was opened as a result of activation of an order placed from a desktop terminal
       MOBILE (int): The position was opened as a result of activation of an order placed from a mobile application
       WEB (int): The position was opened as a result of activation of an order placed from the web platform
       EXPERT (int): The position was opened as a result of activation of an order placed from an MQL5 program,
           i.e. an Expert Advisor or a script
    """
    CLIENT = (DEAL_REASON_CLIENT, 'Desktop')
    MOBILE = (DEAL_REASON_MOBILE, 'Mobile')
    WEB = (DEAL_REASON_WEB, 'Web')
    EXPERT = (DEAL_REASON_EXPERT, 'MQL5 program')


class DealType(models.IntegerChoices):
    """DEAL_TYPE enum. Each deal is characterized by a type, allowed values are enumerated in this enum

    Attributes:
        BUY (int): Buy
        SELL (int): Sell
        BALANCE (int): Balance
        CREDIT (int): Credit
        CHARGE (int): Additional Charge
        CORRECTION (int): Correction
        BONUS (int): Bonus
        COMMISSION (int): Additional Commission
        COMMISSION_DAILY (int): Daily Commission
        COMMISSION_MONTHLY (int): Monthly Commission
        COMMISSION_AGENT_DAILY (int): Daily Agent Commission
        COMMISSION_AGENT_MONTHLY (int): Monthly Agent Commission
        INTEREST (int): Interest Rate
        DEAL_DIVIDEND (int): Dividend Operations
        DEAL_DIVIDEND_FRANKED (int): Franked (non-taxable) dividend operations
        DEAL_TAX (int): Tax Charges

        BUY_CANCELED (int): Canceled buy deal. There can be a situation when a previously executed buy deal is canceled.
            In this case, the type of the previously executed deal (DEAL_TYPE_BUY) is changed to DEAL_TYPE_BUY_CANCELED,
            and its profit/loss is zeroized. Previously obtained profit/loss is charged/withdrawn using a separated
            balance operation

        SELL_CANCELED (int): Canceled sell deal. There can be a situation when a previously executed sell deal is
            canceled. In this case, the type of the previously executed deal (DEAL_TYPE_SELL) is changed to
            DEAL_TYPE_SELL_CANCELED, and its profit/loss is zeroized. Previously obtained profit/loss is
            charged/withdrawn using a separated balance operation.
    """
    BUY = DEAL_TYPE_BUY
    SELL = DEAL_TYPE_SELL
    BALANCE = DEAL_TYPE_BALANCE
    CREDIT = DEAL_TYPE_CREDIT
    CHARGE = DEAL_TYPE_CHARGE
    CORRECTION = DEAL_TYPE_CORRECTION
    BONUS = DEAL_TYPE_BONUS
    COMMISSION = DEAL_TYPE_COMMISSION
    COMMISSION_DAILY = DEAL_TYPE_COMMISSION_DAILY
    COMMISSION_MONTHLY = DEAL_TYPE_COMMISSION_MONTHLY
    COMMISSION_AGENT_DAILY = DEAL_TYPE_COMMISSION_AGENT_DAILY
    COMMISSION_AGENT_MONTHLY = DEAL_TYPE_COMMISSION_AGENT_MONTHLY
    INTEREST = DEAL_TYPE_INTEREST
    BUY_CANCELED = DEAL_TYPE_BUY_CANCELED
    SELL_CANCELED = DEAL_TYPE_SELL_CANCELED
    DEAL_DIVIDEND = DEAL_DIVIDEND
    DEAL_DIVIDEND_FRANKED = DEAL_DIVIDEND_FRANKED
    DEAL_TAX = DEAL_TAX

    def __str__(self):
        if self.name in ('DEAL_DIVIDEND', 'DEAL_DIVIDEND_FRANKED', 'DEAL_TAX'):
            return self.name
        return super().__str__()


class DealEntry(models.IntegerChoices):
    """DEAL_ENTRY Enum. Deals differ not only in their types set in DEAL_TYPE enum, but also in the way they change
    positions. This can be a simple position opening, or accumulation of a previously opened position (market entering),
    position closing by an opposite deal of a corresponding volume (market exiting), or position reversing, if the
    opposite-direction deal covers the volume of the previously opened position.

    Attributes:
        IN (int): Entry In
        OUT (int): Entry Out
        INOUT (int): Reverse
        OUT_BY (int): Close a position by an opposite one
    """
    IN = DEAL_ENTRY_IN
    OUT = DEAL_ENTRY_OUT
    INOUT = DEAL_ENTRY_INOUT
    OUT_BY = DEAL_ENTRY_OUT_BY


class DealReason(models.IntegerChoices):
    """DEAL_REASON Enum. The reason for deal execution is contained in the DEAL_REASON property. A deal can be executed
    as a result of triggering of an order placed from a mobile application or an MQL5 program, as well as as a result
    of the StopOut event, variation margin calculation, etc.

    Attributes:
        CLIENT (int): The deal was executed as a result of activation of an order placed from a desktop terminal
        MOBILE (int): The deal was executed as a result of activation of an order placed from a desktop terminal
        WEB (int): The deal was executed as a result of activation of an order placed from the web platform
        EXPERT (int): The deal was executed as a result of activation of an order placed from an MQL5 program, i.e.
            an Expert Advisor or a script
        SL (int): The deal was executed as a result of Stop Loss activation
        TP (int): The deal was executed as a result of Take Profit activation
        SO (int): The deal was executed as a result of the Stop Out event
        ROLLOVER (int): The deal was executed due to a rollover
        VMARGIN (int): The deal was executed after charging the variation margin
        SPLIT (int): The deal was executed after the split (price reduction) of an instrument, which had an open
            position during split announcement
    """
    CLIENT = (DEAL_REASON_CLIENT, 'Desktop')
    MOBILE = (DEAL_REASON_MOBILE, 'Mobile')
    WEB = (DEAL_REASON_WEB, 'Web')
    EXPERT = (DEAL_REASON_EXPERT, 'MQL5 program')
    SL = (DEAL_REASON_SL, 'Stop Loss activation')
    TP = (DEAL_REASON_TP, 'Take Profit activation')
    SO = (DEAL_REASON_SO, 'Stop Out event')
    ROLLOVER = (DEAL_REASON_ROLLOVER, 'Rollover')
    VMARGIN = (DEAL_REASON_VMARGIN, 'Variation margin')
    SPLIT = (DEAL_REASON_SPLIT, 'Instrument split')


class OrderReason(models.IntegerChoices):
    """ORDER_REASON Enum.

    Attributes:
        CLIENT (int): The order was placed from a desktop terminal
        MOBILE (int): The order was placed from a mobile application
        WEB (int): The order was placed from a web platform
        EXPERT (int): The order was placed from an MQL5-program, i.e. by an Expert Advisor or a script
        SL (int): The order was placed as a result of Stop Loss activation
        TP (int): The order was placed as a result of Take Profit activation
        SO (int): The order was placed as a result of the Stop Out event
    """
    CLIENT = (ORDER_REASON_CLIENT, 'Desktop')
    MOBILE = (ORDER_REASON_MOBILE, 'Mobile')
    WEB = (ORDER_REASON_WEB, 'Web')
    EXPERT = (ORDER_REASON_EXPERT, 'MQL5 program')
    SL = (ORDER_REASON_SL, 'Stop Loss activation')
    TP = (ORDER_REASON_TP, 'Take Profit activation')
    SO = (ORDER_REASON_SO, 'Stop Out event')

class SymbolChartMode(models.IntegerChoices):
    """SYMBOL_CHART_MODE Enum. A symbol price chart can be based on Bid or Last prices. The price selected for symbol
    charts also affects the generation and display of bars in the terminal.
    Possible values of the SYMBOL_CHART_MODE property are described in this enum

    Attributes:
        BID (int): Bars are based on Bid prices
        LAST (int): Bars are based on last prices
    """
    BID = SYMBOL_CHART_MODE_BID
    LAST = SYMBOL_CHART_MODE_LAST


class SymbolCalcMode(models.IntegerChoices):
    """SYMBOL_CALC_MODE Enum. The SYMBOL_CALC_MODE enumeration is used for obtaining information about how the margin
    requirements for a symbol are calculated.

    Attributes:
        FOREX (int): Forex mode - calculation of profit and margin for Forex
        FOREX_NO_LEVERAGE (int): Forex No Leverage mode – calculation of profit and margin for Forex symbols without
            taking into account the leverage
        FUTURES (int): Futures mode - calculation of margin and profit for futures
        CFD (int): CFD mode - calculation of margin and profit for CFD
        CFDINDEX (int): CFD index mode - calculation of margin and profit for CFD by indexes
        CFDLEVERAGE (int): CFD Leverage mode - calculation of margin and profit for CFD at leverage trading
        EXCH_STOCKS (int): Calculation of margin and profit for trading securities on a stock exchange
        EXCH_FUTURES (int): Calculation of margin and profit for trading futures contracts on a stock exchange
        EXCH_OPTIONS (int): value is 34
        EXCH_OPTIONS_MARGIN (int): value is 36
        EXCH_BONDS (int): Exchange Bonds mode – calculation of margin and profit for trading bonds on a stock exchange
        STOCKS_MOEX (int): Exchange MOEX Stocks mode –calculation of margin and profit for trading securities on MOEX
        EXCH_BONDS_MOEX (int): Exchange MOEX Bonds mode – calculation of margin and profit for trading bonds on MOEX

        SERV_COLLATERAL (int): Collateral mode - a symbol is used as a non-tradable asset on a trading account.
            The market value of an open position is calculated based on the volume, current market price, contract size
            and liquidity ratio. The value is included into Assets, which are added to Equity. Open positions of such
            symbols increase the Free Margin amount and are used as additional margin (collateral) for open positions
    """
    FOREX = SYMBOL_CALC_MODE_FOREX
    FOREX_NO_LEVERAGE = SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE
    FUTURES = SYMBOL_CALC_MODE_FUTURES
    CFD = SYMBOL_CALC_MODE_CFD
    CFDINDEX = SYMBOL_CALC_MODE_CFDINDEX
    CFDLEVERAGE = SYMBOL_CALC_MODE_CFDLEVERAGE
    EXCH_STOCKS = SYMBOL_CALC_MODE_EXCH_STOCKS
    EXCH_FUTURES = SYMBOL_CALC_MODE_EXCH_FUTURES
    EXCH_OPTIONS = SYMBOL_CALC_MODE_EXCH_OPTIONS
    EXCH_OPTIONS_MARGIN = SYMBOL_CALC_MODE_EXCH_OPTIONS_MARGIN
    EXCH_BONDS = SYMBOL_CALC_MODE_EXCH_BONDS
    EXCH_STOCKS_MOEX = SYMBOL_CALC_MODE_EXCH_STOCKS_MOEX
    EXCH_BONDS_MOEX = SYMBOL_CALC_MODE_EXCH_BONDS_MOEX
    SERV_COLLATERAL = SYMBOL_CALC_MODE_SERV_COLLATERAL


class SymbolTradeMode(models.IntegerChoices):
    """SYMBOL_TRADE_MODE Enum. There are several symbol trading modes. Information about trading modes of a certain
    symbol is reflected in the values this enumeration

    Attributes:
        DISABLED (int): Trade is disabled for the symbol
        LONGONLY (int): Allowed only long positions
        SHORTONLY (int): Allowed only short positions
        CLOSEONLY (int): Allowed only position close operations
        FULL (int): No trade restrictions
    """

    DISABLED = SYMBOL_TRADE_MODE_DISABLED
    LONGONLY = SYMBOL_TRADE_MODE_LONGONLY
    SHORTONLY = SYMBOL_TRADE_MODE_SHORTONLY
    CLOSEONLY = SYMBOL_TRADE_MODE_CLOSEONLY
    FULL = SYMBOL_TRADE_MODE_FULL


class SymbolTradeExecution(models.IntegerChoices):
    """SYMBOL_TRADE_EXECUTION Enum. The modes, or execution policies, define the rules for cases when the price has
    changed or the requested volume cannot be completely fulfilled at the moment.

    Attributes:
        REQUEST (int): Executing a market order at the price previously received from the broker. Prices for a certain
            market order are requested from the broker before the order is sent. Upon receiving the prices, order
            execution at the given price can be either confirmed or rejected.

        INSTANT (int): Executing a market order at the specified price immediately. When sending a trade request to be
            executed, the platform automatically adds the current prices to the order.
            - If the broker accepts the price, the order is executed.
            - If the broker does not accept the requested price, a "Requote" is sent — the broker returns prices,
            at which this order can be executed.

        MARKET (int): A broker makes a decision about the order execution price without any additional discussion with the trader.
            Sending the order in such a mode means advance consent to its execution at this price.

        EXCHANGE (int): Trade operations are executed at the prices of the current market offers.
    """
    REQUEST = SYMBOL_TRADE_EXECUTION_REQUEST
    INSTANT = SYMBOL_TRADE_EXECUTION_INSTANT
    MARKET = SYMBOL_TRADE_EXECUTION_MARKET
    EXCHANGE = SYMBOL_TRADE_EXECUTION_EXCHANGE


class SymbolSwapMode(models.IntegerChoices):
    """SYMBOL_SWAP_MODE Enum. Methods of swap calculation at position transfer are specified in enumeration
    ENUM_SYMBOL_SWAP_MODE. The method of swap calculation determines the units of measure of the SYMBOL_SWAP_LONG and
    SYMBOL_SWAP_SHORT parameters. For example, if swaps are charged in the client deposit currency, then the values of
    those parameters are specified as an amount of money in the client deposit currency.

    Attributes:
        DISABLED (int): Swaps disabled (no swaps)
        POINTS (int): Swaps are charged in points
        CURRENCY_SYMBOL (int): Swaps are charged in money in base currency of the symbol
        CURRENCY_MARGIN (int): Swaps are charged in money in margin currency of the symbol
        CURRENCY_DEPOSIT (int): Swaps are charged in money, in client deposit currency

        INTEREST_CURRENT (int): Swaps are charged as the specified annual interest from the instrument price at
            calculation of swap (standard bank year is 360 days)

        INTEREST_OPEN (int): Swaps are charged as the specified annual interest from the open price of position
            (standard bank year is 360 days)

        REOPEN_CURRENT (int): Swaps are charged by reopening positions. At the end of a trading day the position is
            closed. Next day it is reopened by the close price +/- specified number of points
            (parameters SYMBOL_SWAP_LONG and SYMBOL_SWAP_SHORT)

        REOPEN_BID (int): Swaps are charged by reopening positions. At the end of a trading day the position is closed.
            Next day it is reopened by the current Bid price +/- specified number of
            points (parameters SYMBOL_SWAP_LONG and SYMBOL_SWAP_SHORT)
    """
    DISABLED = SYMBOL_SWAP_MODE_DISABLED
    POINTS = SYMBOL_SWAP_MODE_POINTS
    CURRENCY_SYMBOL = SYMBOL_SWAP_MODE_CURRENCY_SYMBOL
    CURRENCY_MARGIN = SYMBOL_SWAP_MODE_CURRENCY_MARGIN
    CURRENCY_DEPOSIT = SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT
    INTEREST_CURRENT = SYMBOL_SWAP_MODE_INTEREST_CURRENT
    INTEREST_OPEN = SYMBOL_SWAP_MODE_INTEREST_OPEN
    REOPEN_CURRENT = SYMBOL_SWAP_MODE_REOPEN_CURRENT
    REOPEN_BID = SYMBOL_SWAP_MODE_REOPEN_BID


class DayOfWeek(models.IntegerChoices):
    """DAY_OF_WEEK Enum.

    Attributes:
        SUNDAY (int): Sunday
        MONDAY (int): Monday
        TUESDAY (int): Tuesday
        WEDNESDAY (int): Wednesday
        THURSDAY (int): Thursday
        FRIDAY (int): Friday
        SATURDAY (int): Saturday
    """
    __enum__name__ = "DAY_OF_WEEK"
    SUNDAY = DAY_OF_WEEK_SUNDAY
    MONDAY = DAY_OF_WEEK_MONDAY
    TUESDAY = DAY_OF_WEEK_TUESDAY
    WEDNESDAY = DAY_OF_WEEK_WEDNESDAY
    THURSDAY = DAY_OF_WEEK_THURSDAY
    FRIDAY = DAY_OF_WEEK_FRIDAY
    SATURDAY = DAY_OF_WEEK_SATURDAY


class SymbolOrderGTCMode(models.IntegerChoices):
    """SYMBOL_ORDER_GTC_MODE Enum. If the SYMBOL_EXPIRATION_MODE property is set to SYMBOL_EXPIRATION_GTC
        (good till canceled), the expiration of pending orders, as well as of
        Stop Loss/Take Profit orders should be additionally set using the ENUM_SYMBOL_ORDER_GTC_MODE enumeration.

    Attributes:
        GTC (int): Pending orders and Stop Loss/Take Profit levels are valid for an unlimited period
            until theirConstants, Enumerations and explicit cancellation

        DAILY (int): Orders are valid during one trading day. At the end of the day, all Stop Loss and
            Take Profit levels, as well as pending orders are deleted.

        DAILY_NO_STOPS (int): When a trade day changes, only pending orders are deleted,
            while Stop Loss and Take Profit levels are preserved
    """
    GTC = SYMBOL_ORDERS_GTC
    DAILY = SYMBOL_ORDERS_DAILY
    DAILY_NO_STOPS = SYMBOL_ORDERS_DAILY_NO_STOPS


class SymbolOptionRight(models.IntegerChoices):
    """SYMBOL_OPTION_RIGHT Enum. An option is a contract, which gives the right, but not the obligation,
    to buy or sell an underlying asset (goods, stocks, futures, etc.) at a specified price on or before a specific date.
    The following enumerations describe option properties, including the option type and the right arising from it.

    Attributes:
        CALL (int): A call option gives you the right to buy an asset at a specified price.
        PUT (int): A put option gives you the right to sell an asset at a specified price.
    """
    CALL = SYMBOL_OPTION_RIGHT_CALL
    PUT = SYMBOL_OPTION_RIGHT_PUT


class SymbolOptionMode(models.IntegerChoices):
    """SYMBOL_OPTION_MODE Enum.

    Attributes:
        EUROPEAN (int): European option may only be exercised on a specified date (expiration, execution date, delivery date)
        AMERICAN (int): American option may be exercised on any trading day or before expiry. The period within which
        a buyer can exercise the option is specified for it.
    """
    EUROPEAN = SYMBOL_OPTION_MODE_EUROPEAN
    AMERICAN = SYMBOL_OPTION_MODE_AMERICAN


class AccountTradeMode(models.IntegerChoices):
    """ACCOUNT_TRADE_MODE Enum. There are several types of accounts that can be opened on a trade server.
    The type of account on which an MQL5 program is running can be found out using
    the ENUM_ACCOUNT_TRADE_MODE enumeration.

    Attributes:
        DEMO: Demo account
        CONTEST: Contest account
        REAL: Real Account
    """
    DEMO = ACCOUNT_TRADE_MODE_DEMO
    CONTEST = ACCOUNT_TRADE_MODE_CONTEST
    REAL = ACCOUNT_TRADE_MODE_REAL


class TickFlag(models.IntegerChoices):
    """TICK_FLAG Enum. TICK_FLAG defines possible flags for ticks. These flags are used to describe ticks obtained by the
    copy_ticks_from() and copy_ticks_range() functions.

    Attributes:
        BID (int): Bid price changed
        ASK (int): Ask price changed
        LAST (int): Last price changed
        VOLUME (int): Volume changed
        BUY (int): last Buy price changed
        SELL (int): last Sell price changed
        """
    BID = TICK_FLAG_BID
    ASK = TICK_FLAG_ASK
    LAST = TICK_FLAG_LAST
    VOLUME = TICK_FLAG_VOLUME
    BUY = TICK_FLAG_BUY
    SELL = TICK_FLAG_SELL


class TradeRetcode(models.IntegerChoices):
    """TRADE_RETCODE Enum. Return codes for order send/check operations

    Attributes:
        REQUOTE (int): Requote
        REJECT (int): Request rejected
        CANCEL (int): Request canceled by trader
        PLACED (int): Order placed
        DONE (int): Request completed
        DONE_PARTIAL (int): Only part of the request was completed
        ERROR (int): Request processing error
        TIMEOUT (int): Request canceled by timeout
        INVALID (int): Invalid request
        INVALID_VOLUME (int): Invalid volume in the request
        INVALID_PRICE (int): Invalid price in the request
        INVALID_STOPS (int): Invalid stops in the request
        TRADE_DISABLED (int): Trade is disabled
        MARKET_CLOSED (int): Market is closed
        NO_MONEY (int): There is not enough money to complete the request
        PRICE_CHANGED (int): Prices changed
        PRICE_OFF (int): There are no quotes to process the request
        INVALID_EXPIRATION (int): Invalid order expiration date in the request
        ORDER_CHANGED (int): Order state changed
        TOO_MANY_REQUESTS (int): Too frequent requests
        NO_CHANGES (int): No changes in request
        SERVER_DISABLES_AT (int): Autotrading disabled by server
        CLIENT_DISABLES_AT (int): Autotrading disabled by client terminal
        LOCKED (int): Request locked for processing
        FROZEN (int): Order or position frozen
        INVALID_FILL (int): Invalid order filling type
        CONNECTION (int): No connection with the trade server
        ONLY_REAL (int): Operation is allowed only for live accounts
        LIMIT_ORDERS (int): The number of pending orders has reached the limit
        LIMIT_VOLUME (int): The volume of orders and positions for the symbol has reached the limit
        INVALID_ORDER (int): Incorrect or prohibited order type
        POSITION_CLOSED (int): Position with the specified POSITION_IDENTIFIER has already been closed
        INVALID_CLOSE_VOLUME (int): A close volume exceeds the current position volume

        CLOSE_ORDER_EXIST (int): A close order already exists for a specified position. This may happen when working in
            the hedging system:
            · when attempting to close a position with an opposite one, while close orders for the position already exist
            · when attempting to fully or partially close a position if the total volume of the already present close
                orders and the newly placed one exceeds the current position volume

        LIMIT_POSITIONS (int): The number of open positions simultaneously present on an account can be limited by the
            server settings.After a limit is reached, the server returns the TRADE_RETCODE_LIMIT_POSITIONS error when
            attempting to place an order. The limitation operates differently depending on the position accounting type:
            · Netting — number of open positions is considered. When a limit is reached, the platform does not let
                placing new orders whose execution may increase the number of open positions. In fact, the platform
                allows placing orders only for the symbols that already have open positions.
                The current pending orders are not considered since their execution may lead to changes in the current
                positions but it cannot increase their number.

            · Hedging — pending orders are considered together with open positions, since a pending order activation
                always leads to opening a new position. When a limit is reached, the platform does not allow placing
                both new market orders for opening positions and pending orders.

        REJECT_CANCEL (int): The pending order activation request is rejected, the order is canceled.
        LONG_ONLY (int): The request is rejected, because the "Only long positions are allowed" rule is set for the
            symbol (POSITION_TYPE_BUY)
        SHORT_ONLY (int): The request is rejected, because the "Only short positions are allowed" rule is set for the
            symbol (POSITION_TYPE_SELL)
        CLOSE_ONLY (int): The request is rejected, because the "Only position closing is allowed" rule is set for the
            symbol
        FIFO_CLOSE (int): The request is rejected, because "Position closing is allowed only by FIFO rule" flag is set
            for the trading account (ACCOUNT_FIFO_CLOSE=true)
    """
    REQUOTE = TRADE_RETCODE_REQUOTE
    REJECT = TRADE_RETCODE_REJECT
    CANCEL = TRADE_RETCODE_CANCEL
    PLACED = TRADE_RETCODE_PLACED
    DONE = TRADE_RETCODE_DONE
    DONE_PARTIAL = TRADE_RETCODE_DONE_PARTIAL
    ERROR = TRADE_RETCODE_ERROR
    TIMEOUT = TRADE_RETCODE_TIMEOUT
    INVALID = TRADE_RETCODE_INVALID
    INVALID_VOLUME = TRADE_RETCODE_INVALID_VOLUME
    INVALID_PRICE = TRADE_RETCODE_INVALID_PRICE
    INVALID_STOPS = TRADE_RETCODE_INVALID_STOPS
    TRADE_DISABLED = TRADE_RETCODE_TRADE_DISABLED
    MARKET_CLOSED = TRADE_RETCODE_MARKET_CLOSED
    NO_MONEY = TRADE_RETCODE_NO_MONEY 
    PRICE_CHANGED = TRADE_RETCODE_PRICE_CHANGED
    PRICE_OFF = TRADE_RETCODE_PRICE_OFF
    INVALID_EXPIRATION = TRADE_RETCODE_INVALID_EXPIRATION
    ORDER_CHANGED = TRADE_RETCODE_ORDER_CHANGED
    TOO_MANY_REQUESTS = TRADE_RETCODE_TOO_MANY_REQUESTS
    NO_CHANGES = TRADE_RETCODE_NO_CHANGES
    SERVER_DISABLES_AT = TRADE_RETCODE_SERVER_DISABLES_AT
    CLIENT_DISABLES_AT = TRADE_RETCODE_CLIENT_DISABLES_AT
    LOCKED = TRADE_RETCODE_LOCKED
    FROZEN = TRADE_RETCODE_FROZEN
    INVALID_FILL = TRADE_RETCODE_INVALID_FILL
    CONNECTION = TRADE_RETCODE_CONNECTION
    ONLY_REAL = TRADE_RETCODE_ONLY_REAL
    LIMIT_ORDERS = TRADE_RETCODE_LIMIT_ORDERS
    LIMIT_VOLUME = TRADE_RETCODE_LIMIT_VOLUME
    INVALID_ORDER = TRADE_RETCODE_INVALID_ORDER
    POSITION_CLOSED = TRADE_RETCODE_POSITION_CLOSED
    INVALID_CLOSE_VOLUME = TRADE_RETCODE_INVALID_CLOSE_VOLUME
    CLOSE_ORDER_EXIST = TRADE_RETCODE_CLOSE_ORDER_EXIST
    LIMIT_POSITIONS = TRADE_RETCODE_LIMIT_POSITIONS
    REJECT_CANCEL = TRADE_RETCODE_REJECT_CANCEL
    LONG_ONLY = TRADE_RETCODE_LONG_ONLY
    SHORT_ONLY = TRADE_RETCODE_SHORT_ONLY
    CLOSE_ONLY = TRADE_RETCODE_CLOSE_ONLY
    FIFO_CLOSE = TRADE_RETCODE_FIFO_CLOSE
    

class AccountStopOutMode(models.IntegerChoices):
    """ACCOUNT_STOPOUT_MODE Enum.

    Attributes:
        PERCENT (int): Account stop out mode in percents
        MONEY (int): Account stop out mode in money
    """

    PERCENT = ACCOUNT_STOPOUT_MODE_PERCENT
    MONEY = ACCOUNT_STOPOUT_MODE_MONEY


class AccountMarginMode(models.IntegerChoices):
    """ACCOUNT_MARGIN_MODE Enum.

    Attributes:
        RETAIL_NETTING (int): Used for the OTC markets to interpret positions in the "netting"
            mode (only one position can exist for one symbol). The margin is calculated based on the symbol
            type (SYMBOL_TRADE_CALC_MODE).

        EXCHANGE (int): Used for the exchange markets. Margin is calculated based on the discounts specified in
            symbol settings. Discounts are set by the broker, but not less than the values set by the exchange.

        HEDGING (int): Used for the exchange markets where individual positions are possible
            (hedging, multiple positions can exist for one symbol). The margin is calculated based on the symbol
            type (SYMBOL_TRADE_CALC_MODE) taking into account the hedged margin (SYMBOL_MARGIN_HEDGED).
    """
    RETAIL_NETTING = ACCOUNT_MARGIN_MODE_RETAIL_NETTING
    EXCHANGE = ACCOUNT_MARGIN_MODE_EXCHANGE
    RETAIL_HEDGING = ACCOUNT_MARGIN_MODE_RETAIL_HEDGING


class AccountInfo:
    """Account Information Class.

    Attributes:
        login: int
        password: str
        server: str
        trade_mode: AccountTradeMode
        balance: float
        leverage: float
        profit: float
        point: float
        amount: float = 0
        equity: float
        credit: float
        margin: float
        margin_level: float
        margin_free: float
        margin_mode: AccountMarginMode
        margin_so_mode: AccountStopoutMode
        margin_so_call: float
        margin_so_so: float
        margin_initial: float
        margin_maintenance: float
        fifo_close: bool
        limit_orders: float
        currency: str = "USD"
        trade_allowed: bool = True
        trade_expert: bool = True
        currency_digits: int
        assets: float
        liabilities: float
        commission_blocked: float
        name: str
        company: str
    """
    login: int = 0
    password: str = ''
    server: str = ''
    trade_mode: AccountTradeMode
    balance: float
    leverage: float
    profit: float
    point: float
    amount: float = 0
    equity: float
    credit: float
    margin: float
    margin_level: float
    margin_free: float
    margin_mode: AccountMarginMode
    margin_so_mode: AccountStopOutMode
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    fifo_close: bool
    limit_orders: float
    currency: str = "USD"
    trade_allowed: bool = True
    trade_expert: bool = True
    currency_digits: int
    assets: float
    liabilities: float
    commission_blocked: float
    name: str
    company: str


class TerminalInfo:
    """Terminal information class. Holds information about the terminal.

    Attributes:
        community_account: bool
        community_connection: bool
        connected: bool
        dlls_allowed: bool
        trade_allowed: bool
        tradeapi_disabled: bool
        email_enabled: bool
        ftp_enabled: bool
        notifications_enabled: bool
        mqid: bool
        build: int
        maxbars: int
        codepage: int
        ping_last: int
        community_balance: float
        retransmission: float
        company: str
        name: str
        language: str
        path: str
        data_path: str
        commondata_path: str
    """
    community_account: bool
    community_connection: bool
    connected: bool
    dlls_allowed: bool
    trade_allowed: bool
    tradeapi_disabled: bool
    email_enabled: bool
    ftp_enabled: bool
    notifications_enabled: bool
    mqid: bool
    build: int
    maxbars: int
    codepage: int
    ping_last: int
    community_balance: float
    retransmission: float
    company: str
    name: str
    language: str
    path: str
    data_path: str
    commondata_path: str


class SymbolInfo:
    """Symbol Information Class. Symbols are financial instruments available for trading in the MetaTrader 5 terminal.

    Attributes:
        name: str
        custom: bool
        chart_mode: SymbolChartMode
        select: bool
        visible: bool
        session_deals: int
        session_buy_orders: int
        session_sell_orders: int
        volume: float
        volumehigh: float
        volumelow: float
        time: int
        digits: int
        spread: float
        spread_float: bool
        ticks_bookdepth: int
        trade_calc_mode: SymbolCalcMode
        trade_mode: SymbolTradeMode
        start_time: int
        expiration_time: int
        trade_stops_level: int
        trade_freeze_level: int
        trade_exemode: SymbolTradeExecution
        swap_mode: SymbolSwapMode
        swap_rollover3days: DayOfWeek
        margin_hedged_use_leg: bool
        expiration_mode: int
        filling_mode: int
        order_mode: int
        order_gtc_mode: SymbolOrderGTCMode
        option_mode: SymbolOptionMode
        option_right: SymbolOptionRight
        bid: float
        bidhigh: float
        bidlow: float
        ask: float
        askhigh: float
        asklow: float
        last: float
        lasthigh: float
        lastlow: float
        volume_real: float
        volumehigh_real: float
        volumelow_real: float
        option_strike: float
        point: float
        trade_tick_value: float
        trade_tick_value_profit: float
        trade_tick_value_loss: float
        trade_tick_size: float
        trade_contract_size: float
        trade_accrued_interest: float
        trade_face_value: float
        trade_liquidity_rate: float
        volume_min: float
        volume_max: float
        volume_step: float
        volume_limit: float
        swap_long: float
        swap_short: float
        margin_initial: float
        margin_maintenance: float
        session_volume: float
        session_turnover: float
        session_interest: float
        session_buy_orders_volume: float
        session_sell_orders_volume: float
        session_open: float
        session_close: float
        session_aw: float
        session_price_settlement: float
        session_price_limit_min: float
        session_price_limit_max: float
        margin_hedged: float
        price_change: float
        price_volatility: float
        price_theoretical: float
        price_greeks_delta: float
        price_greeks_theta: float
        price_greeks_gamma: float
        price_greeks_vega: float
        price_greeks_rho: float
        price_greeks_omega: float
        price_sensitivity: float
        basis: str
        category: str
        currency_base: str
        currency_profit: str
        currency_margin: Any
        bank: str
        description: str
        exchange: str
        formula: Any
        isin: Any
        name: str
        page: str
        path: str
    """
    custom: bool
    chart_mode: SymbolChartMode
    select: bool
    visible: bool
    session_deals: int
    session_buy_orders: int
    session_sell_orders: int
    volume: float
    volumehigh: float
    volumelow: float
    time: int
    digits: int
    spread: float
    spread_float: bool
    ticks_bookdepth: int
    trade_calc_mode: SymbolCalcMode
    trade_mode: SymbolTradeMode
    start_time: int
    expiration_time: int
    trade_stops_level: int
    trade_freeze_level: int
    trade_exemode: SymbolTradeExecution
    swap_mode: SymbolSwapMode
    swap_rollover3days: DayOfWeek
    margin_hedged_use_leg: bool
    expiration_mode: int
    filling_mode: int
    order_mode: int
    order_gtc_mode: SymbolOrderGTCMode
    option_mode: SymbolOptionMode
    option_right: SymbolOptionRight
    bid: float
    bidhigh: float
    bidlow: float
    ask: float
    askhigh: float
    asklow: float
    last: float
    lasthigh: float
    lastlow: float
    volume_real: float
    volumehigh_real: float
    volumelow_real: float
    option_strike: float
    point: float
    trade_tick_value: float
    trade_tick_value_profit: float
    trade_tick_value_loss: float
    trade_tick_size: float
    trade_contract_size: float
    trade_accrued_interest: float
    trade_face_value: float
    trade_liquidity_rate: float
    volume_min: float
    volume_max: float
    volume_step: float
    volume_limit: float
    swap_long: float
    swap_short: float
    margin_initial: float
    margin_maintenance: float
    session_volume: float
    session_turnover: float
    session_interest: float
    session_buy_orders_volume: float
    session_sell_orders_volume: float
    session_open: float
    session_close: float
    session_aw: float
    session_price_settlement: float
    session_price_limit_min: float
    session_price_limit_max: float
    margin_hedged: float
    price_change: float
    price_volatility: float
    price_theoretical: float
    price_greeks_delta: float
    price_greeks_theta: float
    price_greeks_gamma: float
    price_greeks_vega: float
    price_greeks_rho: float
    price_greeks_omega: float
    price_sensitivity: float
    basis: str
    category: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    bank: str
    description: str
    exchange: str
    formula: str
    isin: str
    name: str
    page: str
    path: str


class BookInfo:
    """Book Information Class.

    Attributes:
        type: BookType
        price: float
        volume: float
        volume_dbl: float
    """
    type: BookType
    price: float
    volume: float
    volume_dbl: float

class TradeOrder:
    """Trade Order Class.

    Attributes:
        ticket: int
        time_setup: int
        time_setup_msc: int
        time_expiration: int
        time_done: int
        time_done_msc: int
        type: OrderType
        type_time: OrderTime
        type_filling: OrderFilling
        state: OrderState
        magic: int
        position_id: int
        position_by_id: int
        reason: OrderReason
        volume_current: float
        volume_initial: float
        price_open: float
        sl: float
        tp: float
        price_current: float
        price_stoplimit: float
        symbol: str
        comment: str
        external_id: str
    """
    ticket: int
    time_setup: int
    time_setup_msc: int
    time_expiration: int
    time_done: int
    time_done_msc: int
    type: OrderType
    type_time: OrderTime
    type_filling: OrderFilling
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: OrderReason
    volume_current: float
    volume_initial: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str


class TradeRequest:
    """Trade Request Class.

    Attributes:
        action: TradeAction
        type: OrderType
        order: int
        symbol: str
        volume: float
        sl: float
        tp: float
        price: float
        deviation: float
        stop_limit: float
        type_time: OrderTime
        type_filling: OrderFilling
        expiration: int
        position: int
        position_by: int
        comment: str
        magic: int
        deviation: int
        comment: str
    """
    action: TradeAction
    type: OrderType
    order: int
    symbol: str
    volume: float
    sl: float
    tp: float
    price: float
    deviation: float
    stop_limit: float
    type_time: OrderTime
    type_filling: OrderFilling
    expiration: int
    position: int
    position_by: int
    comment: str
    magic: int
    deviation: int
    comment: str


class OrderCheckResult:
    """Order Check Result

    Attributes:
        retcode: int
        balance: float
        equity: float
        profit: float
        margin: float
        margin_free: float
        margin_level: float
        comment: str
        request: TradeRequest
    """
    retcode: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    comment: str
    request: TradeRequest


class OrderSendResult:
    """Order Send Result

    Attributes:
        retcode: int
        deal: int
        order: int
        volume: float
        price: float
        bid: float
        ask: float
        comment: str
        request: TradeRequest
        request_id: int
        retcode_external: int
        profit: float
    """
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request: TradeRequest
    request_id: int
    retcode_external: int
    profit: float


class TradePosition:
    """Trade Position

    Attributes:
        ticket: int
        time: int
        time_msc: int
        time_update: int
        time_update_msc: int
        type: OrderType
        magic: float
        identifier: int
        reason: PositionReason
        volume: float
        price_open: float
        sl: float
        tp: float
        price_current: float
        swap: float
        profit: float
        symbol: str
        comment: str
        external_id: str
    """
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: OrderType
    magic: float
    identifier: int
    reason: PositionReason
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str


class TradeDeal:
    """Trade Deal

    Attributes:
        ticket: int
        order: int
        time: int
        time_msc: int
        type: DealType
        entry: DealEntry
        magic: int
        position_id: int
        reason: DealReason
        volume: float
        price: float
        commission: float
        swap: float
        profit: float
        fee: float
        sl: float
        tp: float
        symbol: str
        comment: str
        external_id: str
    """
    ticket: int
    order: int
    time: int
    time_msc: int
    type: DealType
    entry: DealEntry
    magic: int
    position_id: int
    reason: DealReason
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    sl: float
    tp: float
    symbol: str
    comment: str
    external_id: str

class Tick:
    """Price Tick of a Financial Instrument.

    Attributes:
        time (int): Time of the last prices update for the symbol
        bid (float): Current Bid price
        ask (float): Current Ask price
        last (float): Price of the last deal (Last)
        volume (float): Volume for the current Last price
        time_msc (int): Time of the last prices update for the symbol in milliseconds
        flags (TickFlag): Tick flags
        volume_real (float): Volume for the current Last price
        Index (int): Custom attribute representing the position of the tick in a sequence.
    """
    time: float
    bid: float
    ask: float
    last: float
    volume: float
    time_msc:float
    flags: float
    volume_real:float
