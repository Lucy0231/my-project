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

## Suggested Search Improvements
1. **Adaptive Parameter Ranges**  
   ```python
   # Dynamically narrow ranges after initial search
   if best_lambda in [min_range, max_range]:
       new_range = np.linspace(best_lambda*0.5, best_lambda*1.5, 5)

# Search choices
## Search Methodology
### 1. Parameter Selection
| Parameter       | Tested Values       | Financial Rationale               | Effect on Execution |
|----------------|---------------------|----------------------------------|---------------------|
| `lambda_over`  | [0.0005, 0.001, 0.002] | 5-20bps penalty for overfilling | Limits overshooting |
| `lambda_under` | [0.0005, 0.001, 0.002] | 5-20bps penalty for underfilling | Ensures completion |
| `theta_queue`  | [0.00005, 0.0001, 0.0002] | 0.5-2bps queue position risk | Balances limit/market orders |

### 2. Search Strategy
**Grid Search** over all 27 combinations because:
- ✅ **Exhaustive**: Guarantees finding the global optimum in this small parameter space  
- ✅ **Interpretable**: Clear relationship between parameters and results  
- ✅ **Reproducible**: Same results on repeated runs  


