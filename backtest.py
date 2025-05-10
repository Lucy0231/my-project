#!/usr/bin/env python
# coding: utf-8

# In[89]:


import pandas as pd
import numpy as np
import json
from itertools import product

class SmartOrderRouter:
    def __init__(self, lambda_over, lambda_under, theta_queue):
        self.lambda_over = lambda_over
        self.lambda_under = lambda_under
        self.theta_queue = theta_queue
    
    def allocate(self, order_size, venues):
        """Implementation that matches the description in allocator_pseudocode.txt"""
        step = 100
        splits = [[]]
        
        # Generate all possible splits
        for v in range(len(venues)):
            new_splits = []
            for alloc in splits:
                used = sum(alloc)
                max_v = min(order_size - used, venues[v]['ask_size'])
                for q in range(0, max_v + 1, step):
                    new_splits.append(alloc + [q])
            splits = new_splits
        
        # Find optimal split
        best_cost = float('inf')
        best_split = None
        for alloc in splits:
            if sum(alloc) != order_size:
                continue
            cost = self._compute_cost(alloc, venues, order_size)
            if cost < best_cost:
                best_cost = cost
                best_split = alloc
                
        return best_split or [0]*len(venues), best_cost  
    
    def _compute_cost(self, split, venues, order_size):
        """Calculation of cost that accounts for poetntial penalties"""
        executed = cash_spent = 0
        for i, qty in enumerate(split):
            exe = min(qty, venues[i]['ask_size'])
            executed += exe
            cash_spent += exe * (venues[i]['ask'] + venues[i]['fee'])
            cash_spent -= max(qty - exe, 0) * venues[i]['rebate']
        
        underfill = max(order_size - executed, 0)
        overfill = max(executed - order_size, 0)
        risk_pen = self.theta_queue * (underfill + overfill)
        cost_pen = self.lambda_under * underfill + self.lambda_over * overfill
        return cash_spent + risk_pen + cost_pen



# In[90]:


def load_and_preprocess(filepath):
    """Loading and preprocessing of market data"""
    df = pd.read_csv(filepath)
    
    # Filter to first message per publisher per timestamp
    df = df.sort_values(['ts_event', 'publisher_id'])
    df = df.groupby(['ts_event', 'publisher_id']).first().reset_index()
    
    # Convert and map data
    df['timestamp'] = pd.to_datetime(df['ts_event'], unit='ns')
    df['venue'] = df['publisher_id'].astype(str)
    df['ask'] = df['ask_px_00']
    df['ask_size'] = df['ask_sz_00']
    df['fee'] = 0.003
    df['rebate'] = 0.002
    
    return df

def run_backtest(df, params, order_size=5000):
    """Backtest with error handling"""
    router = SmartOrderRouter(**params)
    remaining_qty = order_size
    total_cost = 0
    filled_shares = 0
    
    timestamps = np.sort(df['timestamp'].unique())
    
    for ts in timestamps:
        if remaining_qty <= 0:
            break
            
        current_venues = df[df['timestamp'] == ts]
        venues = current_venues.to_dict('records')
        
        allocation, _ = router.allocate(remaining_qty, venues)
        
        # Handle potential None allocation
        if not allocation:
            allocation = [0]*len(venues)
            
        for i, venue in enumerate(venues):
            qty = allocation[i]
            if qty <= 0:
                continue
                
            executed = min(qty, venue['ask_size'])
            cost = executed * (venue['ask'] + venue['fee'])
            
            filled_shares += executed
            total_cost += cost
            remaining_qty -= executed
    
    avg_price = total_cost / filled_shares if filled_shares > 0 else 0
    return {
        'params': params,
        'total_cost': total_cost,
        'filled_shares': filled_shares,
        'avg_price': avg_price
    }


# In[91]:


def parameter_search(df, param_grid):
    """Search of parameters with validation"""
    best_result = None
    best_cost = float('inf')
    
    param_combinations = product(
        param_grid['lambda_over'],
        param_grid['lambda_under'],
        param_grid['theta_queue']
    )
    
    for lo, lu, tq in param_combinations:
        result = run_backtest(df, {
            'lambda_over': lo,
            'lambda_under': lu,
            'theta_queue': tq
        })
        
        if result['filled_shares'] > 0 and result['total_cost'] < best_cost:
            best_cost = result['total_cost']
            best_result = result
    
    return best_result or {  # Default result if none found
        'params': {'lambda_over': 0, 'lambda_under': 0, 'theta_queue': 0},
        'total_cost': float('inf'),
        'filled_shares': 0,
        'avg_price': 0
    }


# In[92]:


def calculate_savings(optimal, baseline):
    """Safe savings calculation"""
    if baseline['avg_price'] == 0:
        return 0
    return 10000 * (baseline['avg_price'] - optimal['avg_price']) / baseline['avg_price']

def main():
    try:
        df = load_and_preprocess('l1_day.csv')
        
        param_grid = {
            'lambda_over': [0.0005, 0.001, 0.002],
            'lambda_under': [0.0005, 0.001, 0.002],
            'theta_queue': [0.00005, 0.0001, 0.0002]
        }
        
        optimal_result = parameter_search(df, param_grid)
        
        baselines = [
            benchmark_naive(df),
            benchmark_twap(df),
            benchmark_vwap(df)
        ]
        
        output = {
            'optimal_parameters': optimal_result['params'],
            'optimal_results': {
                'total_cost': optimal_result['total_cost'],
                'avg_price': optimal_result['avg_price'],
                'filled_shares': optimal_result['filled_shares']
            },
            'baselines': {b['strategy']: {
                'total_cost': b['total_cost'],
                'avg_price': b['avg_price']
            } for b in baselines},
            'savings_bps': {b['strategy']: calculate_savings(optimal_result, b)
                          for b in baselines}
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}))

if __name__ == "__main__":
    main()


# In[ ]:




