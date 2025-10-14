"""
Configuration settings for PEAD Trading System
"""

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
LOGS_DIR = PROJECT_ROOT / 'logs'
DOCS_DIR = PROJECT_ROOT / 'docs'

# Data paths
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
EXCLUSIONS_DIR = DATA_DIR / 'exclusions'
HISTORICAL_DATA_DIR = PROCESSED_DATA_DIR / 'historical_data'

# File paths
EARNINGS_FINAL_CSV = PROCESSED_DATA_DIR / 'earnings_final.csv'
MARKET_CAP_EXCLUSIONS_CSV = EXCLUSIONS_DIR / 'market_cap_exclusions.csv'
MA_EXCLUSIONS_CSV = EXCLUSIONS_DIR / 'ma_exclusions.csv'

# TWS API settings
TWS_PORT = 4002
TWS_CLIENT_ID = 25
TWS_HOST = "127.0.0.1"

# Data collection settings
SLEEP_BETWEEN_REQUESTS = 0.5  # seconds
SLEEP_BETWEEN_STOCKS = 0.8    # seconds
REQUEST_TIMEOUT = 30          # seconds

# Analysis settings
MIN_MARKET_CAP = 1_000_000_000  # $1B
TARGET_STOCKS = 80
MIN_EARNINGS_EVENTS = 5
MIN_WIN_RATE = 0.4

# Trading strategy settings
STRATEGY_1_HOLD_DAYS = 1      # Day -1 to Day +1
STRATEGY_2_HOLD_DAYS = 7      # Day -1 to Day +7
MAX_POSITION_SIZE = 0.05      # 5% of capital per trade
STOP_LOSS_STRATEGY_1 = -0.05  # -5%
STOP_LOSS_STRATEGY_2 = -0.07  # -7%

# Challenge settings
CHALLENGE_START_DATE = "2024-10-14"
CHALLENGE_END_DATE = "2024-11-13"
STARTING_CAPITAL = 100_000
TARGET_TRADES_PER_WEEK = 10

