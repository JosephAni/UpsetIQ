# Model Design

| Category         | Examples                                 |
| ---------------- | ---------------------------------------- |
| Team Performance | ELO, win streaks, injuries               |
| Market Signals   | Spread movement, opening vs closing odds |
| Public Bias      | % of public bets on favorite             |
| Momentum         | Recent form, fatigue                     |
| Anomalies        | Historical upset frequency vs matchup    |

Output

Upset Probability Score (0–100%)

You do not need deep neural nets initially.
Start with:

Gradient boosting (XGBoost / LightGBM)

Logistic regression ensemble
