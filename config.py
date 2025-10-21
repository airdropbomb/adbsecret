import os
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Configuration
MANUAL_CLOSE_TIME = int(os.getenv('MANUAL_CLOSE_TIME', '25'))
LOOP_WAIT_MIN = int(os.getenv('LOOP_WAIT_MIN', '5'))
LOOP_WAIT_MAX = int(os.getenv('LOOP_WAIT_MAX', '10'))

# Transfer Amount Configuration - NEW
TRANSFER_ADJUSTMENT = Decimal(os.getenv('TRANSFER_ADJUSTMENT', '0.0007'))

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    END = '\033[0m'
    BOLD = '\033[1m'

# BTC MARGIN PAIRS - Organized according to group&pair.txt
BTC_GROUPS = {
    0: {
        'name': 'BTC/USDT',
        'category': 'Main Pair',
        'pairs': ['BTCUSDT']
    },
    
    1: {
        'name': 'Group 1',
        'category': 'A-B Pairs',
        'pairs': [
            '1INCHBTC', 'AAVEBTC', 'ADABTC', 'AGLDBTC', 'ALGOBTC',
            'APEBTC', 'ARBBTC', 'ARBTC', 'ARPABTC', 'ATOMBTC',
            'AUCTIONBTC', 'AUDIOBTC', 'AVAXBTC', 'AXSBTC', 'BATBTC'
        ]
    },
    
    2: {
        'name': 'Group 2', 
        'category': 'B-D Pairs',
        'pairs': [
            'BCHBTC', 'BNBBTC', 'CAKEBTC', 'CELOBTC', 'CFXBTC',
            'CHRBTC', 'CHZBTC', 'COMPBTC', 'COTIBTC', 'CRVBTC',
            'CTKBTC', 'CTSIBTC', 'DASHBTC', 'DIABTC', 'DOGEBTC'
        ]
    },
    
    3: {
        'name': 'Group 3',
        'category': 'D-I Pairs',
        'pairs': [
            'DOTBTC', 'DUSKBTC', 'DYDXBTC', 'EGLDBTC', 'ENABTC',
            'ENJBTC', 'ENSBTC', 'ETCBTC', 'ETHBTC', 'FETBTC',
            'FILBTC', 'GALABTC', 'GRTBTC', 'HBARBTC', 'INJBTC'
        ]
    },
    
    4: {
        'name': 'Group 4',
        'category': 'I-Y Pairs',
        'pairs': [
            'IOTXBTC', 'JSTBTC', 'KAVABTC', 'ONGBTC', 'OXTBTC',
            'SNXBTC', 'SUSHIBTC', 'UNIBTC', 'YFIBTC', 'ZRXBTC',
            'FLOWBTC', 'FLUXBTC', 'GASBTC', 'GLMBTC', 'HIVEBTC'
        ]
    },
    
    5: {
        'name': 'Group 5',
        'category': 'I-N Pairs',
        'pairs': [
            'ICPBTC', 'ICXBTC', 'IDBTC', 'IOTABTC', 'KNCBTC',
            'KSMBTC', 'LINKBTC', 'LPTBTC', 'LRCBTC', 'LTCBTC',
            'MANABTC', 'MINABTC', 'MOVRBTC', 'MTLBTC', 'NEARBTC'
        ]
    },
    
    6: {
        'name': 'Group 6',
        'category': 'N-R Pairs',
        'pairs': [
            'NEOBTC', 'NMRBTC', 'OGNBTC', 'OMBTC', 'ONGBTC',
            'OPBTC', 'PAXGBTC', 'PEOPLEBTC', 'POWRBTC', 'PYRBTC',
            'QNTBTC', 'RAREBTC', 'REQBTC', 'RLCBTC', 'ROSEBTC'
        ]
    },
    
    7: {
        'name': 'Group 7',
        'category': 'R-V Pairs',
        'pairs': [
            'RUNEBTC', 'SANDBTC', 'SEIBTC', 'SOLBTC', 'STORJBTC',
            'STXBTC', 'SUIBTC', 'SUPERBTC', 'SXPBTC', 'SYSBTC',
            'THETABTC', 'TRBBTC', 'TRXBTC', 'UMABTC', 'VETBTC'
        ]
    },
    
    8: {
        'name': 'Group 8',
        'category': 'W-Z & USDT',
        'pairs': [
            'WANBTC', 'WAXPBTC', 'WLDBTC', 'XLMBTC', 'XRPBTC',
            'XTZBTC', 'YGGBTC', 'ZECBTC', 'USDTBTC'
        ]
    }
}

# Global variables (will be initialized in main script)
INITIAL_BALANCE = Decimal('0')
PREVIOUS_LOOP_BALANCE = Decimal('0')
TOTAL_PROFIT = Decimal('0')
TOTAL_LOSS = Decimal('0')
PROFIT_QTY = 0
LOSS_QTY = 0
