import os
import time
import random
import threading
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Import configuration
from config import *

# Initialize client
client = Client(API_KEY, API_SECRET, testnet=False)

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_size():
    """Get terminal size for responsive design"""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24  # Default size for Termux

def get_assets_from_symbol(symbol):
    """Extract base and quote assets from symbol"""
    if symbol == 'BTCUSDT':
        return 'BTC', 'USDT'
    elif symbol.endswith('BTC'):
        return symbol[:-3], 'BTC'
    else:
        return symbol[:-4], symbol[-4:]

def get_display_name(symbol):
    base, quote = get_assets_from_symbol(symbol)
    return f"{base}/{quote}"

def get_current_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return Decimal(ticker['price'])
    except Exception:
        return Decimal('0')

def get_portfolio_value():
    try:
        account = client.get_account()
        total_value = Decimal('0')
        
        for asset in account['balances']:
            free = Decimal(asset['free'])
            locked = Decimal(asset['locked'])
            total_balance = free + locked
            
            if total_balance == Decimal('0'):
                continue
                
            if asset['asset'] == 'USDT':
                total_value += total_balance
                continue
            
            try:
                usdt_pair = f"{asset['asset']}USDT"
                price = get_current_price(usdt_pair)
                
                if price == Decimal('0'):
                    btc_pair = f"{asset['asset']}BTC"
                    btc_price = get_current_price(btc_pair)
                    btc_usdt_price = get_current_price('BTCUSDT')
                    
                    if btc_price > Decimal('0') and btc_usdt_price > Decimal('0'):
                        price = btc_price * btc_usdt_price
                    else:
                        continue
                        
                total_value += total_balance * price
            except Exception:
                continue
        
        return total_value
    except Exception:
        return Decimal('0')

def initialize_balance_tracking():
    """Initialize global balance tracking variables"""
    global INITIAL_BALANCE, PREVIOUS_LOOP_BALANCE, TOTAL_PROFIT, TOTAL_LOSS, PROFIT_QTY, LOSS_QTY
    INITIAL_BALANCE = get_portfolio_value()
    PREVIOUS_LOOP_BALANCE = INITIAL_BALANCE
    TOTAL_PROFIT = Decimal('0')
    TOTAL_LOSS = Decimal('0')
    PROFIT_QTY = 0
    LOSS_QTY = 0

def calculate_loop_profit_loss(before_balance, after_balance, loop_number):
    """Calculate profit/loss for each loop"""
    global PREVIOUS_LOOP_BALANCE, TOTAL_PROFIT, TOTAL_LOSS, PROFIT_QTY, LOSS_QTY
    
    loop_profit = after_balance - before_balance
    
    # Update totals
    if loop_profit > Decimal('0'):
        TOTAL_PROFIT += loop_profit
        PROFIT_QTY += 1
    elif loop_profit < Decimal('0'):
        TOTAL_LOSS += abs(loop_profit)
        LOSS_QTY += 1
    
    PREVIOUS_LOOP_BALANCE = after_balance
    return loop_profit

def print_parallel_header(loop_number, total_loops=80, mode="PARALLEL", remaining_time="06:08:35"):
    """Print responsive parallel trading header"""
    clear_screen()
    
    # Get terminal width for responsive design
    terminal_width, _ = get_terminal_size()
    
    # Adjust layout based on terminal width
    if terminal_width >= 100:
        # Full layout for wide screens
        title = "PARALLEL TRADING STATUS"
        border_length = min(120, terminal_width - 2)
        padding = (border_length - len(title) - 2) // 2
        print(f"{Colors.BOLD}{Colors.BLUE}┌{'─' * padding}{title}{'─' * (border_length - len(title) - 2 - padding)}┐{Colors.END}")
        
        phase_info = f"Phase: Loop : {loop_number:2d} | Remaining Time: {remaining_time}"
        trader_info = f"BTC-Trader @yannaingko2"
        available_width = border_length - len(phase_info) - len(trader_info) - 4
        if available_width > 10:
            center_padding = available_width // 2
            print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.END} {Colors.YELLOW}{phase_info}{Colors.END}{' ' * center_padding}{Colors.CYAN}{trader_info}{Colors.END} {Colors.BOLD}{Colors.BLUE}│{Colors.END}")
        else:
            # Stack the information if not enough width
            print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.END} {Colors.YELLOW}{phase_info}{Colors.END}{' ' * (border_length - len(phase_info) - 4)} {Colors.BOLD}{Colors.BLUE}│{Colors.END}")
            print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.END} {Colors.CYAN}{trader_info:^{border_length-4}}{Colors.END} {Colors.BOLD}{Colors.BLUE}│{Colors.END}")
        
        print(f"{Colors.BOLD}{Colors.BLUE}└{'─' * border_length}┘{Colors.END}")
    else:
        # Compact layout for narrow screens
        title = "TRADING STATUS"
        border_length = min(80, terminal_width - 2)
        print(f"{Colors.BOLD}{Colors.BLUE}┌{'─' * ((border_length - len(title) - 2) // 2)}{title}{'─' * ((border_length - len(title) - 2) // 2)}┐{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.END} Loop:{Colors.CYAN}{loop_number:2d}{Colors.END} Time:{Colors.CYAN}{remaining_time}{Colors.END} Trader:{Colors.CYAN}@yannaingko2{Colors.END}{' ' * (border_length-40)} {Colors.BOLD}{Colors.BLUE}│{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}└{'─' * border_length}┘{Colors.END}")

def print_parallel_status_table(pairs_status, loop_number, remaining_time="06:08:35"):
    """Print clean parallel trading status display with proper borders"""
    
    # Get terminal size for responsive design
    terminal_width, terminal_height = get_terminal_size()
    
    # Fixed column widths for stability
    col_no = 4
    col_pairs = 12
    col_status = 18
    col_market = 12
    col_value = 10
    col_profit = 10
    col_loss = 10
    col_total_profit = 12
    col_total_loss = 12
    
    # Calculate total table width
    total_width = (col_no + col_pairs + col_status + col_market + col_value + 
                  col_profit + col_loss + col_total_profit + col_total_loss + 18)
    
    # Adjust if table is too wide for terminal
    if total_width > terminal_width:
        scale_factor = terminal_width / total_width
        col_no = max(3, int(col_no * scale_factor))
        col_pairs = max(8, int(col_pairs * scale_factor))
        col_status = max(12, int(col_status * scale_factor))
        col_market = max(8, int(col_market * scale_factor))
        col_value = max(8, int(col_value * scale_factor))
        col_profit = max(8, int(col_profit * scale_factor))
        col_loss = max(8, int(col_loss * scale_factor))
        col_total_profit = max(10, int(col_total_profit * scale_factor))
        col_total_loss = max(10, int(col_total_loss * scale_factor))
    
    # Print table header with proper borders
    print(f"{Colors.BOLD}{Colors.BLUE}┌{'─' * col_no}┬{'─' * col_pairs}┬{'─' * col_status}┬{'─' * col_market}┬{'─' * col_value}┬{'─' * col_profit}┬{'─' * col_loss}┬{'─' * col_total_profit}┬{'─' * col_total_loss}┐{Colors.END}")
    
    # Column headers
    headers = [
        f"{Colors.BOLD}{Colors.CYAN}{'NO':^{col_no}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'PAIRS':^{col_pairs}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'STATUS':^{col_status}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'MARKET':^{col_market}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'VALUE':^{col_value}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'PROFIT':^{col_profit}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'LOSS':^{col_loss}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'T_PROFIT':^{col_total_profit}}{Colors.END}",
        f"{Colors.BOLD}{Colors.CYAN}{'T_LOSS':^{col_total_loss}}{Colors.END}"
    ]
    
    header_line = f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}" + f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}".join(headers) + f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}"
    print(header_line)
    
    print(f"{Colors.BOLD}{Colors.BLUE}├{'─' * col_no}┼{'─' * col_pairs}┼{'─' * col_status}┼{'─' * col_market}┼{'─' * col_value}┼{'─' * col_profit}┼{'─' * col_loss}┼{'─' * col_total_profit}┼{'─' * col_total_loss}┤{Colors.END}")
    
    # Data rows
    active_pairs = [pair for pair, status in pairs_status.items() if status['status'] not in ['STOPPED', 'No Balance']]
    
    for i, (pair, status_info) in enumerate(pairs_status.items(), 1):
        # Get status with appropriate color
        status = status_info['status']
        if status == "Transfer OP":
            status_display = f"{Colors.YELLOW}{status:^{col_status}}{Colors.END}"
        elif status == "Transfer Completed":
            status_display = f"{Colors.GREEN}{status:^{col_status}}{Colors.END}"
        elif status == "No Balance":
            status_display = f"{Colors.RED}{status:^{col_status}}{Colors.END}"
        elif status == "Waiting Manual":
            status_display = f"{Colors.BLUE}{status:^{col_status}}{Colors.END}"
        elif status == "STOPPED":
            status_display = f"{Colors.RED}{status:^{col_status}}{Colors.END}"
        elif status == "Completed":
            status_display = f"{Colors.GREEN}{status:^{col_status}}{Colors.END}"
        elif "FAILED" in status:
            status_display = f"{Colors.RED}{status:^{col_status}}{Colors.END}"
        elif "WORKING" in status:
            status_display = f"{Colors.YELLOW}{status:^{col_status}}{Colors.END}"
        elif "WAITING" in status:
            status_display = f"{Colors.BLUE}{status:^{col_status}}{Colors.END}"
        else:
            status_display = f"{Colors.CYAN}{status:^{col_status}}{Colors.END}"
        
        # Format data with proper padding and truncation
        no_display = f"{Colors.CYAN}{i:^{col_no}}{Colors.END}"
        
        pair_name = get_display_name(pair)
        if len(pair_name) > col_pairs:
            pair_name = pair_name[:col_pairs-2] + ".."
        pair_display = f"{pair_name:^{col_pairs}}"
        
        market_price = status_info.get('market_price', '0.00000000')
        if len(market_price) > col_market:
            market_price = market_price[:col_market-2] + ".."
        market_display = f"{market_price:^{col_market}}"
        
        value_display_val = status_info.get('value', '$0.000000')
        if len(value_display_val) > col_value:
            value_display_val = value_display_val[:col_value-2] + ".."
        value_display = f"{value_display_val:^{col_value}}"
        
        # Get profit/loss data
        profit = status_info.get('profit', '$0.00000')
        loss = status_info.get('loss', '$0.00000')
        
        # Get total profit/loss for this pair
        total_profit_val = status_info.get('total_profit', '$0.00000')
        total_loss_val = status_info.get('total_loss', '$0.00000')
        
        # Color coding - PROFIT in GREEN, LOSS in RED
        if profit != '$0.00000' and profit != '' and profit != '$0.00000':
            profit_display = f"{Colors.GREEN}{profit:^{col_profit}}{Colors.END}"
        else:
            profit_display = f"{profit:^{col_profit}}"
            
        if loss != '$0.00000' and loss != '' and loss != '$0.00000':
            loss_display = f"{Colors.RED}{loss:^{col_loss}}{Colors.END}"
        else:
            loss_display = f"{loss:^{col_loss}}"
            
        if total_profit_val != '$0.00000' and total_profit_val != '' and total_profit_val != '$0.00000':
            total_profit_display = f"{Colors.GREEN}{total_profit_val:^{col_total_profit}}{Colors.END}"
        else:
            total_profit_display = f"{total_profit_val:^{col_total_profit}}"
            
        if total_loss_val != '$0.00000' and total_loss_val != '' and total_loss_val != '$0.00000':
            total_loss_display = f"{Colors.RED}{total_loss_val:^{col_total_loss}}{Colors.END}"
        else:
            total_loss_display = f"{total_loss_val:^{col_total_loss}}"
        
        # Create row data
        row_data = [
            no_display,
            pair_display,
            status_display,
            market_display,
            value_display,
            profit_display,
            loss_display,
            total_profit_display,
            total_loss_display
        ]
        
        row_line = f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}" + f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}".join(row_data) + f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}"
        print(row_line)
    
    # Complete bottom border
    print(f"{Colors.BOLD}{Colors.BLUE}└{'─' * col_no}┴{'─' * col_pairs}┴{'─' * col_status}┴{'─' * col_market}┴{'─' * col_value}┴{'─' * col_profit}┴{'─' * col_loss}┴{'─' * col_total_profit}┴{'─' * col_total_loss}┘{Colors.END}")
    
    # Show active pairs count
    print(f"\n{Colors.CYAN}Active Pairs: {len(active_pairs)}/{len(pairs_status)} | Stopped: {len(pairs_status) - len(active_pairs)}{Colors.END}")

def calculate_transfer_amount(symbol):
    """Calculate transfer amount using new formula: ((btc price × 0.0000001) - TRANSFER_ADJUSTMENT) ÷ coin price"""
    base_asset, quote_asset = get_assets_from_symbol(symbol)
    
    if symbol == 'BTCUSDT':
        # For BTC/USDT: ((btc price × 0.0000001) - TRANSFER_ADJUSTMENT)
        btc_price = get_current_price('BTCUSDT')
        if btc_price == Decimal('0'):
            amount = Decimal('0.0001')
            return 'USDT', amount, amount, 'Default'
        
        step1 = btc_price * Decimal('0.0000001')
        step2 = step1 - TRANSFER_ADJUSTMENT  # Changed from hardcoded 0.0007
        
        # Ensure minimum amount
        if step2 <= Decimal('0'):
            step2 = Decimal('0.0001')
            
        return 'USDT', step2, step2, f'{btc_price:.2f}'
    
    try:
        # Get current prices
        btc_price = get_current_price('BTCUSDT')
        pair_price = get_current_price(symbol)
        
        if btc_price == Decimal('0') or pair_price == Decimal('0'):
            amount = Decimal('0.00000001')
            return base_asset, amount, Decimal('0'), 'Default'
        
        # New formula: ((btc price × 0.0000001) - TRANSFER_ADJUSTMENT) ÷ coin price
        step1 = btc_price * Decimal('0.0000001')
        step2 = step1 - TRANSFER_ADJUSTMENT  # Changed from hardcoded 0.0007
        
        # Ensure minimum USDT value
        if step2 <= Decimal('0'):
            step2 = Decimal('0.0001')
            
        # For BTC pairs, we need to convert the BTC pair price to USDT value first
        # BTC pair price is in BTC, so we multiply by BTC price to get USDT value
        coin_price_in_usdt = pair_price * btc_price
        
        # Calculate coin amount: step2 ÷ coin price in USDT
        calculated_amount = step2 / coin_price_in_usdt
        calculated_amount = calculated_amount.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
        
        if calculated_amount < Decimal('0.00000001'):
            calculated_amount = Decimal('0.00000001')
        
        return base_asset, calculated_amount, step2, f'{pair_price:.8f}'
            
    except Exception:
        amount = Decimal('0.00000001')
        return base_asset, amount, Decimal('0'), 'Default'

def check_spot_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return Decimal(balance['free'])
    except Exception:
        return Decimal('0')

def ensure_isolated_margin_account(symbol):
    try:
        client.enable_isolated_margin_account(symbol=symbol)
        return True
    except BinanceAPIException:
        return True

def transfer_spot_to_margin_thread(symbol, pairs_status):
    """Thread function for transferring spot to margin"""
    try:
        transfer_asset, amount, usdt_value, market_price = calculate_transfer_amount(symbol)
        current_balance = check_spot_balance(transfer_asset)
        
        # Update status to show transfer in progress
        pairs_status[symbol]['status'] = "Transfer OP"
        pairs_status[symbol]['market_price'] = market_price
        pairs_status[symbol]['value'] = f"${usdt_value:.6f}"
        # Reset to $0.00000 during process
        pairs_status[symbol]['profit'] = "$0.00000"
        pairs_status[symbol]['loss'] = "$0.00000"
        
        # Check balance and handle no balance case
        if current_balance < amount:
            pairs_status[symbol]['status'] = "No Balance"
            pairs_status[symbol]['profit'] = "$0.00000"
            pairs_status[symbol]['loss'] = "$0.00000"
            return False
        
        # Execute transfer
        client.transfer_spot_to_isolated_margin(
            asset=transfer_asset, 
            symbol=symbol, 
            amount=float(amount)
        )
        
        # Update status to completed
        pairs_status[symbol]['status'] = "Transfer Completed"
        pairs_status[symbol]['profit'] = "$0.00000"
        pairs_status[symbol]['loss'] = "$0.00000"
        return True
        
    except BinanceAPIException as e:
        if "insufficient balance" in str(e).lower():
            pairs_status[symbol]['status'] = "No Balance"
        else:
            pairs_status[symbol]['status'] = "FAILED"
        pairs_status[symbol]['profit'] = "$0.00000"
        pairs_status[symbol]['loss'] = "$0.00000"
        return False

def clean_margin_account_thread(symbol, pairs_status):
    """Thread function for cleaning margin account"""
    try:
        pairs_status[symbol]['status'] = "Cleaning"
        
        account = client.get_isolated_margin_account(symbols=symbol)
        if not account['assets']:
            pairs_status[symbol]['status'] = "Completed"
            return True
            
        asset_info = account['assets'][0]
        base_asset, quote_asset = get_assets_from_symbol(symbol)
        
        base_free = Decimal(asset_info['baseAsset']['free'])
        quote_free = Decimal(asset_info['quoteAsset']['free'])
        base_borrowed = Decimal(asset_info['baseAsset']['borrowed'])
        quote_borrowed = Decimal(asset_info['quoteAsset']['borrowed'])
        
        # Repay borrowed assets
        if base_borrowed > Decimal('0'):
            try:
                client.repay_isolated_margin_asset(
                    asset=base_asset, 
                    symbol=symbol, 
                    amount=float(base_borrowed)
                )
            except BinanceAPIException:
                pass
        
        if quote_borrowed > Decimal('0'):
            try:
                client.repay_isolated_margin_asset(
                    asset=quote_asset, 
                    symbol=symbol, 
                    amount=float(quote_borrowed)
                )
            except BinanceAPIException:
                pass
        
        # Remove free assets
        if base_free > Decimal('0.00000001'):
            try:
                client.transfer_isolated_margin_to_spot(
                    asset=base_asset, 
                    symbol=symbol, 
                    amount=float(base_free)
                )
            except BinanceAPIException:
                pass
        
        if quote_free > Decimal('0.00000001'):
            try:
                client.transfer_isolated_margin_to_spot(
                    asset=quote_asset, 
                    symbol=symbol, 
                    amount=float(quote_free)
                )
            except BinanceAPIException:
                pass
                
        pairs_status[symbol]['status'] = "Completed"
        return True
        
    except Exception:
        pairs_status[symbol]['status'] = "Cleaning Failed"
        return False

def wait_for_manual_close_parallel(loop_number, pairs_status, remaining_time="06:08:35"):
    """Wait for manual close with process status updates - FIXED VERSION"""
    # Update status for active pairs
    for pair, status_info in pairs_status.items():
        if status_info['status'] not in ['No Balance', 'STOPPED']:
            pairs_status[pair]['status'] = "Waiting Manual"
    
    # Print table once at the beginning
    print_parallel_header(loop_number, remaining_time=remaining_time)
    print_parallel_status_table(pairs_status, loop_number, remaining_time)
    
    print(f"\n{Colors.YELLOW}Please manually close all positions in Binance{Colors.END}")
    
    # Countdown without refreshing the table
    for i in range(MANUAL_CLOSE_TIME, 0, -1):
        hours = i // 3600
        minutes = (i % 3600) // 60
        seconds = i % 60
        current_remaining = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Use carriage return to update only the countdown line
        print(f"{Colors.CYAN}Time remaining: {current_remaining}{Colors.END}", end='\r')
        time.sleep(1)
    
    # Clear the countdown line
    print(' ' * 50, end='\r')
    
    print(f"\n{Colors.GREEN}Manual close phase completed{Colors.END}")
    time.sleep(2)

def print_balance_display(before_balance, after_balance, loop_profit):
    """Print clean balance display without borders"""
    # Calculate net difference
    net_difference = TOTAL_PROFIT - TOTAL_LOSS
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== LOOP RESULTS ==={Colors.END}")
    print(f"Before Balance: {Colors.YELLOW}${before_balance:.5f}{Colors.END}")
    print(f"After Balance:  {Colors.YELLOW}${after_balance:.5f}{Colors.END}")
    
    if loop_profit > Decimal('0'):
        print(f"Loop P/L:      {Colors.GREEN}+${loop_profit:.5f}{Colors.END}")
    elif loop_profit < Decimal('0'):
        print(f"Loop P/L:      {Colors.RED}-${abs(loop_profit):.5f}{Colors.END}")
    else:
        print(f"Loop P/L:      ${loop_profit:.5f}")
    
    print(f"Total Profit:  {Colors.GREEN}${TOTAL_PROFIT:.5f}{Colors.END} (Qty: {Colors.CYAN}{PROFIT_QTY:2d}{Colors.END})")
    print(f"Total Loss:    {Colors.RED}${TOTAL_LOSS:.5f}{Colors.END} (Qty: {Colors.CYAN}{LOSS_QTY:2d}{Colors.END})")
    
    # Add NET DIFFERENCE (Total Profit - Total Loss)
    if net_difference > Decimal('0'):
        print(f"Net P/L:       {Colors.GREEN}+${net_difference:.5f}{Colors.END}")
    elif net_difference < Decimal('0'):
        print(f"Net P/L:       {Colors.RED}-${abs(net_difference):.5f}{Colors.END}")
    else:
        print(f"Net P/L:       ${net_difference:.5f}")
    
    print(f"{Colors.BOLD}{Colors.CYAN}==================={Colors.END}")

def run_parallel_trading_loop(selected_pairs):
    """Run trading loop in parallel mode with immediate profit/loss display"""
    
    # Initialize pair-specific profit/loss tracking
    pair_totals = {}
    for pair in selected_pairs:
        pair_totals[pair] = {
            'total_profit': Decimal('0'),
            'total_loss': Decimal('0'),
            'profit_qty': 0,
            'loss_qty': 0
        }
    
    for loop in range(1, 81):
        # Initialize status tracking for all pairs
        pairs_status = {}
        for pair in selected_pairs:
            ensure_isolated_margin_account(pair)
            pairs_status[pair] = {
                'status': "WAITING",
                'market_price': "0.00000000",
                'value': "$0.000000",
                'profit': "$0.00000",  # Always start with $0.00000
                'loss': "$0.00000",    # Always start with $0.00000
                'total_profit': f"${pair_totals[pair]['total_profit']:.5f}",  # Show accumulated total with 5 decimals
                'total_loss': f"${pair_totals[pair]['total_loss']:.5f}"       # Show accumulated total with 5 decimals
            }
        
        # Get balance BEFORE transfer
        before_balance = get_portfolio_value()
        
        # Step 1: Show initial status - ONLY ONCE
        remaining_time = "06:08:35"
        print_parallel_header(loop, remaining_time=remaining_time)
        print_parallel_status_table(pairs_status, loop, remaining_time)
        
        # Step 2: Parallel Transfer with process status
        print(f"\n{Colors.YELLOW}Starting parallel transfers...{Colors.END}")
        time.sleep(1)
        
        # Update status to show transfer starting - DO NOT REDRAW TABLE HERE
        for pair in selected_pairs:
            pairs_status[pair]['status'] = "Starting Transfer"
            # Generate realistic market prices
            market_price = Decimal(str(random.uniform(0.00001, 0.001))).quantize(Decimal('0.00000000'))
            pairs_status[pair]['market_price'] = f"{market_price:.8f}"
            pairs_status[pair]['value'] = "$0.010500"
            # Reset current profit/loss but keep totals
            pairs_status[pair]['profit'] = "$0.00000"
            pairs_status[pair]['loss'] = "$0.00000"
        
        # Show updated status only once after setting all to "Starting Transfer"
        print_parallel_header(loop, remaining_time=remaining_time)
        print_parallel_status_table(pairs_status, loop, remaining_time)
        
        # Execute transfers in threads only for pairs with balance
        threads = []
        active_pairs = []
        
        for pair in selected_pairs:
            # Check balance before starting thread
            transfer_asset, amount, usdt_value, market_price = calculate_transfer_amount(pair)
            current_balance = check_spot_balance(transfer_asset)
            
            if current_balance >= amount:
                active_pairs.append(pair)
                thread = threading.Thread(target=transfer_spot_to_margin_thread, args=(pair, pairs_status))
                threads.append(thread)
                thread.start()
            else:
                pairs_status[pair]['status'] = "No Balance"
                pairs_status[pair]['profit'] = "$0.00000"
                pairs_status[pair]['loss'] = "$0.00000"
            
            time.sleep(0.05)  # Faster rate limiting
        
        # Wait for all transfers to complete
        for thread in threads:
            thread.join()
        
        # Show final transfer status - ONLY ONCE
        print_parallel_header(loop, remaining_time=remaining_time)
        print_parallel_status_table(pairs_status, loop, remaining_time)
        
        # Step 3: Manual Close with countdown (only for active pairs)
        if active_pairs:
            wait_for_manual_close_parallel(loop, pairs_status, remaining_time)
        else:
            print(f"\n{Colors.RED}No active pairs with balance - skipping manual close{Colors.END}")
            time.sleep(1)
        
        # Step 4: Parallel Cleanup (only for active pairs)
        print_parallel_header(loop, remaining_time=remaining_time)
        print_parallel_status_table(pairs_status, loop, remaining_time)
        
        # Update status for cleaning only active pairs
        cleanup_threads = []
        for pair in active_pairs:
            if pairs_status[pair]['status'] in ["Transfer Completed", "Waiting Manual"]:
                pairs_status[pair]['status'] = "Cleaning"
                thread = threading.Thread(target=clean_margin_account_thread, args=(pair, pairs_status))
                cleanup_threads.append(thread)
                thread.start()
                time.sleep(0.05)  # Faster rate limiting
        
        # Wait for all cleanups to complete
        for thread in cleanup_threads:
            thread.join()
        
        # Get balance AFTER cleanup
        after_balance = get_portfolio_value()
        
        # Step 5: Profit/Loss Calculation - IMMEDIATE UPDATE
        loop_profit = calculate_loop_profit_loss(before_balance, after_balance, loop)
        
        # IMMEDIATELY update pairs status with actual profit/loss data
        for pair in active_pairs:
            if pairs_status[pair]['status'] == "Completed":
                # Calculate this pair's share of the profit/loss
                if loop_profit > Decimal('0'):
                    pair_profit = loop_profit / len(active_pairs)
                    pairs_status[pair]['profit'] = f"${pair_profit:.5f}"  # 5 decimal places
                    pairs_status[pair]['loss'] = "$0.00000"
                    # Update pair totals
                    pair_totals[pair]['total_profit'] += pair_profit
                    pair_totals[pair]['profit_qty'] += 1
                elif loop_profit < Decimal('0'):
                    pair_loss = abs(loop_profit) / len(active_pairs)
                    pairs_status[pair]['profit'] = "$0.00000"
                    pairs_status[pair]['loss'] = f"${pair_loss:.5f}"  # 5 decimal places
                    # Update pair totals
                    pair_totals[pair]['total_loss'] += pair_loss
                    pair_totals[pair]['loss_qty'] += 1
                else:
                    pairs_status[pair]['profit'] = "$0.00000"
                    pairs_status[pair]['loss'] = "$0.00000"
                
                # IMMEDIATELY update display of accumulated totals
                pairs_status[pair]['total_profit'] = f"${pair_totals[pair]['total_profit']:.5f}"  # 5 decimal places
                pairs_status[pair]['total_loss'] = f"${pair_totals[pair]['total_loss']:.5f}"      # 5 decimal places
        
        # IMMEDIATE final display with updated profit/loss
        print_parallel_header(loop, remaining_time=remaining_time)
        print_parallel_status_table(pairs_status, loop, remaining_time)
        
        # Display results with clean, consistent formatting
        print_balance_display(before_balance, after_balance, loop_profit)
        
        # Wait for next loop with overwriting countdown
        if loop < 80:
            wait_time = random.randint(LOOP_WAIT_MIN, LOOP_WAIT_MAX)
            print(f"\n{Colors.CYAN}Next loop in {wait_time} seconds...{Colors.END}", end='')
            
            for i in range(wait_time, 0, -1):
                print(f"\r{Colors.CYAN}Next loop in {i:2d} seconds...{Colors.END}", end='')
                time.sleep(1)
            
            print('\r' + ' ' * 50 + '\r')  # Clear the countdown line

def run_single_trading_loop(selected_pair):
    """Single pair trading loop"""
    display_name = get_display_name(selected_pair)
    
    ensure_isolated_margin_account(selected_pair)
    
    for loop in range(1, 81):
        print(f"\n" + "="*50)
        print(f"LOOP {Colors.CYAN}{loop}{Colors.END}/80 - {display_name}")
        print("="*50)
        
        # Get balance BEFORE transfer
        before_balance = get_portfolio_value()
        
        # Step 1: Transfer with detailed amount info
        if not transfer_spot_to_margin(selected_pair):
            print("Skipping loop")
            if loop < 80:
                wait_between_loops()
            continue

        # Step 2: Manual close
        wait_for_manual_close()

        # Step 3: Cleanup
        print(f"Cleaning up margin account...")
        clean_margin_account(selected_pair)
        
        # Get balance AFTER cleanup
        after_balance = get_portfolio_value()
        
        # Step 4: Profit/Loss - Calculate using before and after balance
        loop_profit = calculate_loop_profit_loss(before_balance, after_balance, loop)
        
        print(f"\n--- Loop {Colors.CYAN}{loop}{Colors.END} Completed ---")
        print(f"Before Balance: ${before_balance:.5f}")
        print(f"After Balance: ${after_balance:.5f}")
        
        # CURRENT PROFIT or CURRENT LOSS
        if loop_profit > Decimal('0'):
            print(f"{Colors.GREEN}CURRENT PROFIT: ${loop_profit:+.5f}{Colors.END}")
        elif loop_profit < Decimal('0'):
            print(f"{Colors.RED}CURRENT LOSS: ${loop_profit:.5f}{Colors.END}")
        else:
            print(f"CURRENT PROFIT OR LOSS: $ {loop_profit:.5f}")
        
        # TOTAL PROFIT and PROFIT QTY
        print(f"{Colors.GREEN}TOTAL PROFIT : ${TOTAL_PROFIT:.5f} | PROFIT QTY : {Colors.CYAN}{PROFIT_QTY}{Colors.END}{Colors.END}")
        
        # TOTAL LOSS and LOSS QTY
        print(f"{Colors.RED}TOTAL LOSS     : ${TOTAL_LOSS:.5f} | LOSS QTY     : {Colors.CYAN}{LOSS_QTY}{Colors.END}{Colors.END}")

        # Wait for next loop
        if loop < 80:
            wait_between_loops()

def transfer_spot_to_margin(symbol):
    """Single pair transfer function"""
    transfer_asset, amount, usdt_value, price_info = calculate_transfer_amount(symbol)
    
    print(f"\nTransfer Details:")
    print(f"Pair: {get_display_name(symbol)}")
    print(f"USDT Value: ${usdt_value:.8f}")
    
    if symbol != 'BTCUSDT':
        print(f"Market Price: {price_info}")
    
    print(f"Amount: {amount:.8f} {transfer_asset}")
    
    try:
        current_balance = check_spot_balance(transfer_asset)
        print(f"Spot Balance: {current_balance:.8f} {transfer_asset}")
        
        if current_balance < amount:
            print("Insufficient balance")
            return False
        
        client.transfer_spot_to_isolated_margin(
            asset=transfer_asset, 
            symbol=symbol, 
            amount=float(amount)
        )
        print("Transfer successful")
        return True
        
    except BinanceAPIException:
        print("Transfer failed")
        return False

def wait_for_manual_close():
    """Single pair manual close function"""
    print(f"Waiting {Colors.CYAN}{MANUAL_CLOSE_TIME}{Colors.END}s for manual close...")
    
    for i in range(MANUAL_CLOSE_TIME, 0, -1):
        print(f"Time remaining: {Colors.CYAN}{i}{Colors.END}s", end='\r')
        time.sleep(1)
    
    print("Manual close completed")
def clean_margin_account(symbol):
    """Single pair cleanup function"""
    try:
        account = client.get_isolated_margin_account(symbols=symbol)
        if not account['assets']:
            return True
            
        asset_info = account['assets'][0]
        base_asset, quote_asset = get_assets_from_symbol(symbol)
        
        base_free = Decimal(asset_info['baseAsset']['free'])
        quote_free = Decimal(asset_info['quoteAsset']['free'])
        base_borrowed = Decimal(asset_info['baseAsset']['borrowed'])
        quote_borrowed = Decimal(asset_info['quoteAsset']['borrowed'])
        
        # Repay borrowed assets
        if base_borrowed > Decimal('0'):
            try:
                client.repay_isolated_margin_asset(
                    asset=base_asset, 
                    symbol=symbol, 
                    amount=float(base_borrowed)
                )
                time.sleep(1)
            except BinanceAPIException:
                pass
        
        if quote_borrowed > Decimal('0'):
            try:
                client.repay_isolated_margin_asset(
                    asset=quote_asset, 
                    symbol=symbol, 
                    amount=float(quote_borrowed)
                )
                time.sleep(1)
            except BinanceAPIException:
                pass
        
        # Remove free assets
        if base_free > Decimal('0.00000001'):
            try:
                client.transfer_isolated_margin_to_spot(
                    asset=base_asset, 
                    symbol=symbol, 
                    amount=float(base_free)
                )
                time.sleep(1)
            except BinanceAPIException:
                pass
        
        if quote_free > Decimal('0.00000001'):
            try:
                client.transfer_isolated_margin_to_spot(
                    asset=quote_asset, 
                    symbol=symbol, 
                    amount=float(quote_free)
                )
                time.sleep(1)
            except BinanceAPIException:
                pass
                
        return True
        
    except Exception:
        return False

def wait_between_loops():
    wait_time = random.randint(LOOP_WAIT_MIN, LOOP_WAIT_MAX)
    print(f"Next loop in {Colors.CYAN}{wait_time}{Colors.END}s...")
    time.sleep(wait_time)

def select_group():
    """Select trading group"""
    print(f"\nAvailable Groups:")
    for group_num in sorted(BTC_GROUPS.keys()):
        group_info = BTC_GROUPS[group_num]
        pairs_count = len(group_info['pairs'])
        if group_num == 0:
            print(f"[{Colors.CYAN}{group_num}{Colors.END}] {Colors.BOLD}{group_info['name']}{Colors.END} [{group_info['category']}] ({Colors.CYAN}{pairs_count}{Colors.END} pair)")
        else:
            print(f"[{Colors.CYAN}{group_num}{Colors.END}] {Colors.BOLD}{group_info['name']}{Colors.END} [{group_info['category']}] ({Colors.CYAN}{pairs_count}{Colors.END} pairs)")
    
    while True:
        choice = input(f"\n{Colors.CYAN}Select group: {Colors.END}").strip()
        if choice.lower() == 'exit':
            return None
        try:
            choice = int(choice)
            if choice in BTC_GROUPS:
                return choice
            else:
                print(f"{Colors.RED}Please enter number {min(BTC_GROUPS.keys())}-{max(BTC_GROUPS.keys())}{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.END}")

def select_trading_mode(group_num):
    """Let user select between single and parallel mode with pair display"""
    group_info = BTC_GROUPS[group_num]
    group_pairs = group_info['pairs']
    
    # Display pairs in balanced format before mode selection
    display_pairs_balanced(group_pairs, group_info)
    
    print(f"\n{Colors.BOLD}Select Trading Mode:{Colors.END}")
    print(f"        [{Colors.CYAN}1{Colors.END}] {Colors.YELLOW}Single Pair{Colors.END} - Trade one pair at a time")
    
    if group_num != 0:
        print(f"        [{Colors.CYAN}2{Colors.END}] {Colors.GREEN}Parallel Mode{Colors.END} - Trade all {Colors.CYAN}{len(group_pairs)}{Colors.END} pairs simultaneously")
    
    while True:
        choice = input(f"\n{Colors.CYAN}Select mode (1{' or 2' if group_num != 0 else ''}): {Colors.END}").strip()
        if choice.lower() == 'back':
            return None
        try:
            choice = int(choice)
            if choice == 1:
                return "single"
            elif choice == 2 and group_num != 0:
                return "parallel"
            else:
                if group_num == 0:
                    print(f"{Colors.RED}Please enter 1{Colors.END}")
                else:
                    print(f"{Colors.RED}Please enter 1 or 2{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.END}")

def select_pair_from_group(group_num, mode="single"):
    """Select pair(s) based on mode"""
    group_info = BTC_GROUPS[group_num]
    group_pairs = group_info['pairs']
    
    if mode == "parallel":
        print(f"\n{Colors.GREEN}✓ Parallel Mode Selected{Colors.END}")
        print(f"Trading all {Colors.CYAN}{len(group_pairs)}{Colors.END} pairs in {group_info['name']} [{group_info['category']}]")
        return group_pairs
    
    # Single mode - show pair selection
    if group_num == 0:
        # Only one pair available
        selected_pair = group_pairs[0]
        print(f"\n{Colors.GREEN}✓ Selected: {get_display_name(selected_pair)}{Colors.END}")
        return selected_pair
    
    # Single mode for groups with multiple pairs
    print(f"\n{Colors.BOLD}Select a pair from {group_info['name']} [{group_info['category']}]:{Colors.END}")
    display_pairs_balanced(group_pairs, group_info)
    
    while True:
        choice = input(f"\n{Colors.CYAN}Select pair (1-{len(group_pairs)}): {Colors.END}").strip()
        if choice.lower() == 'back':
            return None
        try:
            choice = int(choice)
            if 1 <= choice <= len(group_pairs):
                selected_pair = group_pairs[choice - 1]
                print(f"{Colors.GREEN}✓ Selected: {get_display_name(selected_pair)}{Colors.END}")
                return selected_pair
            else:
                print(f"{Colors.RED}Please enter number 1-{len(group_pairs)}{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.END}")

def display_pairs_balanced(group_pairs, group_info):
    """Display pairs in balanced column format"""
    pairs = group_pairs
    print(f"\n< {group_info['name']} [{group_info['category']}] Pairs:")
    
    if len(pairs) == 15:
        # Special balanced display for 15 pairs (3 columns, 5 rows)
        for i in range(5):
            row_pairs = []
            for j in range(3):
                index = i + j * 5
                if index < len(pairs):
                    pair_num = index + 1
                    row_pairs.append(f"[{pair_num:2d}] {get_display_name(pairs[index]):<12}")
            print(" ".join(row_pairs))
    elif len(pairs) == 1:
        # Single pair display
        print(f"[ 1] {get_display_name(pairs[0])}")
    else:
        # Default balanced display for other group sizes (3 columns)
        rows = (len(pairs) + 2) // 3  # Ceiling division
        for i in range(rows):
            row_pairs = []
            for j in range(3):
                index = i + j * rows
                if index < len(pairs):
                    pair_num = index + 1
                    row_pairs.append(f"[{pair_num:2d}] {get_display_name(pairs[index]):<12}")
            print(" ".join(row_pairs))

def main():
    # Get terminal size for responsive design
    terminal_width, terminal_height = get_terminal_size()
    
    print(f"{Colors.BOLD}Binance Margin Trading Bot{Colors.END}")
    print("=" * min(64, terminal_width))
    print(f"Dynamic USDT Value: ((BTC Price × 0.0000001) - {TRANSFER_ADJUSTMENT})")  # Updated to show TRANSFER_ADJUSTMENT
    print(f"Manual Close Time: {Colors.CYAN}{MANUAL_CLOSE_TIME}{Colors.END}s")
    print(f"Loop Wait: {Colors.CYAN}{LOOP_WAIT_MIN}{Colors.END}-{Colors.CYAN}{LOOP_WAIT_MAX}{Colors.END}s")
    print(f"Transfer Adjustment: {Colors.CYAN}{TRANSFER_ADJUSTMENT}{Colors.END}")  # New line to show current adjustment
    print(f"Total Groups: {Colors.CYAN}{len(BTC_GROUPS)}{Colors.END}")
    total_pairs = sum(len(group_info['pairs']) for group_info in BTC_GROUPS.values())
    print(f"Total Pairs: {Colors.CYAN}{total_pairs}{Colors.END}")
    print("=" * min(64, terminal_width))
    
    initialize_balance_tracking()
    print(f"Initial Balance: ${Colors.CYAN}{INITIAL_BALANCE:.5f}{Colors.END}")
    
    # Display terminal info for debugging
    print(f"{Colors.CYAN}Terminal: {terminal_width}x{terminal_height}{Colors.END}")
    
    while True:
        selected_group = select_group()
        if not selected_group:
            break
        
        trading_mode = select_trading_mode(selected_group)
        if not trading_mode:
            continue
        
        selected_pairs = select_pair_from_group(selected_group, trading_mode)
        if not selected_pairs:
            continue
        
        if trading_mode == "single":
            run_single_trading_loop(selected_pairs)
        else:
            run_parallel_trading_loop(selected_pairs)
        
        group_info = BTC_GROUPS[selected_group]
        print(f"\nTrading completed for {group_info['name']} [{group_info['category']}]!")
        continue_choice = input("Trade another group? (y/n): ").strip().lower()
        if continue_choice != 'y':
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\nScript stopped")
    except Exception as e:
        print(f"\nError: {e}")
