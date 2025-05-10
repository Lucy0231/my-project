# Smart Order Router Backtest

## Overview
This implementation backtests a Smart Order Router based on Cont & Kukanov's optimal allocation model, splitting 5,000-share orders across multiple venues using three risk parameters:
- `lambda_over`: Penalty for overfilling (0.0005-0.002)
- `lambda_under`: Penalty for underfilling (0.0005-0.002)  
- `theta_queue`: Queue risk factor (0.00005-0.0002)
  
### Code Structure:
1. **Allocator**  
   - Exhaustive search over 100-share chunks
   - Computes costs with all penalties (overfill, underfill, queue risk)
   - Returns optimal venue allocation

2. **Backtest Engine**  
   - Processes L1 market data chronologically
   - Tracks unfilled shares between snapshots
   - Records execution prices/quantities

3. **Parameter Search**  
   Grid search over:
   ```python
   param_grid = {
       'lambda_over': [0.0005, 0.001, 0.002],      # 5-20bps
       'lambda_under': [0.0005, 0.001, 0.002],     # 5-20bps  
       'theta_queue': [0.00005, 0.0001, 0.0002]    # Small queue weights
   }

## Search Methodology
### Parameter Selection
| Parameter       | Tested Values       | Financial Rationale               |
|-----------------|---------------------|-----------------------------------|
| `lambda_over`   | [0.0005, 0.001, 0.002] | 5-20bps penalty for overfilling  |
| `lambda_under`  | [0.0005, 0.001, 0.002] | 5-20bps penalty for underfilling |
| `theta_queue`   | [0.00005, 0.0001, 0.0002] | 0.5-2bps queue position risk    |

### Search Strategy
**Grid Search** was chosen because:
- ✅ Complete coverage of parameter space (27 combinations)
- ✅ Clear interpretation of parameter-performance relationships
- ✅ Perfect reproducibility of results

## Suggested Improvement: Enhanced Fill Realism
### Queue-Aware Execution Model
```python
def execute_order(qty, venue):
    """
    Simulates realistic fill probabilities considering:
    - Queue position (0=front, 1=back)
    - Slippage effects
    - Time decay
    """
    # Queue position effect
    queue_depth = venue.get('queue_position', 0.5)
    fill_prob = 0.9 * (1 - queue_depth)  # 90% max fill at front
    
    # Slippage model
    slippage = 0.0005 * (qty / venue['ask_size'])  # 0.05% impact
    
    executed_qty = min(qty, venue['ask_size']) * fill_prob
    executed_price = venue['ask'] * (1 + slippage)
    
    return round(executed_qty), executed_price

