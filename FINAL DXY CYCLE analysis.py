import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from datetime import datetime

# Configuration
TICKER = 'DX-Y.NYB'                  # DXY ticker symbol
FIB_SEQ = [7, 13, 21, 33]              # Fibonacci offsets (in bars).      do this but I want it also highlighted if the peak to peak or peak to trough or trough to peak and peak to trough only reach 20-22 in the cycle highlight this too showing 7 and 13 
INTERVAL_RANGE = (31, 35)              # Valid cycle range in bars (inclusive)
START_DATE = datetime(2021, 7, 1)      # Start date: July 1, 2021
END_DATE = datetime(2025, 2, 6)        # End date: February 6, 2025

# Fetch DXY data
dxy = yf.download(TICKER, start=START_DATE, end=END_DATE)

# Convert closing prices to a proper 1D NumPy array and get dates
close_prices = dxy['Close'].to_numpy().flatten()
dates = dxy.index

# Detect peaks and troughs with adjusted prominence and minimum distance
peaks, _ = find_peaks(close_prices, prominence=1.5, distance=10)
troughs, _ = find_peaks(-close_prices, prominence=1.5, distance=10)

# Create an events DataFrame (each event is a tuple: (type, date, index))
events = []
for idx in peaks:
    events.append(('peak', dates[idx], idx))
for idx in troughs:
    events.append(('trough', dates[idx], idx))
events_df = pd.DataFrame(events, columns=['type', 'date', 'index']).sort_values('date').reset_index(drop=True)

# Loop over all pairs of events (i, j) with i < j to find valid cycles (based on bar difference)
valid_cycles = []
for i in range(0, len(events_df) - 1):
    for j in range(i + 1, len(events_df)):
        start_event = events_df.iloc[i]
        curr_event = events_df.iloc[j]
        idx_diff = curr_event['index'] - start_event['index']  # Difference in bars
        
        if INTERVAL_RANGE[0] <= idx_diff <= INTERVAL_RANGE[1]:
            # Determine cycle type explicitly:
            if start_event['type'] == 'peak' and curr_event['type'] == 'peak':
                cycle_type = 'Peak-to-Peak'
            elif start_event['type'] == 'trough' and curr_event['type'] == 'trough':
                cycle_type = 'Trough-to-Trough'
            elif start_event['type'] == 'peak' and curr_event['type'] == 'trough':
                cycle_type = 'Peak-to-Trough'
            elif start_event['type'] == 'trough' and curr_event['type'] == 'peak':
                cycle_type = 'Trough-to-Peak'
            else:
                cycle_type = 'Unknown'
            
            # Calculate Fibonacci points within the cycle based on bar offsets
            fib_points = []
            for fib in FIB_SEQ:
                if fib < idx_diff:
                    fib_idx = start_event['index'] + fib
                    if fib_idx < len(dates):
                        fib_points.append((fib, dates[fib_idx]))
            
            valid_cycles.append({
                'cycle_type': cycle_type,
                'start_date': start_event['date'],
                'end_date': curr_event['date'],
                'duration_bars': idx_diff,
                'fib_points': fib_points
            })

# Print all valid cycles
print(f"Found {len(valid_cycles)} valid cycles (31-35 bars):")
for i, cycle in enumerate(valid_cycles, 1):
    print(f"Cycle {i}: {cycle['cycle_type']}, Duration: {cycle['duration_bars']} bars, "
          f"from {cycle['start_date']} to {cycle['end_date']}, "
          f"Fibonacci points found: {len(cycle['fib_points'])}")

# Visualization
plt.figure(figsize=(16, 8))
plt.plot(dates, close_prices, label='DXY Close Price', alpha=0.5)

# Plot peaks and troughs
plt.scatter(dates[peaks], close_prices[peaks], color='green', marker='^', label='Peaks')
plt.scatter(dates[troughs], close_prices[troughs], color='red', marker='v', label='Troughs')

# Highlight valid cycles and mark Fibonacci points
for cycle in valid_cycles:
    plt.axvspan(cycle['start_date'], cycle['end_date'], alpha=0.2, color='orange')
    for fib_day, fib_date in cycle['fib_points']:
        fib_idx = np.where(dates == fib_date)[0][0]
        fib_price = close_prices[fib_idx]
        plt.scatter(fib_date, fib_price, color='purple', s=100, edgecolors='gold', zorder=10)
        plt.text(fib_date, fib_price * 0.99, f'F{fib_day}', ha='center', va='top', color='darkblue')

plt.title(f"DXY Fibonacci Cycle Analysis ({START_DATE.date()} - {END_DATE.date()})")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
