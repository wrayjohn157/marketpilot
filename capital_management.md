# Capital Protection Strategies for Fully Deployed Trades

This document outlines risk management options for trades that have reached their DCA budget limit, are near break-even (BE), and are exhibiting mixed recovery signals. These scenarios can serve as a reference for integrating dynamic exit logic in the future.

## Scenario Context: Example - USUAL/USDT
- Base Order + 9 Safety Orders fully used
- Spent: $2000
- Avg Entry: ~0.12885
- Current Price: ~0.1261 (Drawdown ~2.1%)
- TP1: ~0.1298 (~0.6% above BE)
- Recovery Odds: 0.94
- Confidence: 0.82
- SAFU Score: 0.85
- BTC Status: Technically bullish, but visually choppy on chart

---

## Option 1: Hold Fully
- **Upside:** TP1 hit yields small win ($10–20)
- **Downside:** Further drawdown to 0.123 or lower could mean -4% to -6% → $80–120 loss
- **Risk Level:** Medium
- **When to Use:** BTC shows momentum + trade structure improving

---

## Option 2: Sell Half Now
- **Action:** Realize 50% at current price (~0.1261)
- **Booked Loss:** ~$20 on half position
- **Remaining Trade:** Easier to hit BE/TP1
- **Benefit:** Frees $1000 to redeploy elsewhere
- **Risk Level:** Low to Medium
- **When to Use:** Mixed momentum, no strong recovery confirmation yet

---

## Option 3: Stop Loss or Trailing Stop
- **Hard SL:** At -4% (~0.1235) to cap max loss (~$80)
- **TSL:** At -2.5% to -3% to preserve capital if bounce fails
- **Risk Level:** Low
- **When to Use:** Market rolling over or BTC loses EMA50 support

---

## Option 4: Hybrid Approach (Recommended for Chop)
- **Sell 25–33% immediately** to reduce exposure
- **Hold remaining 66–75% with TSL at -3%**
- **Monitor**: RSI slope and MACD lift
- **Adjust:** Exit fully if no reclaim within 6–12 hours
- **Estimated Net Outcome:**
  - **Best Case:** +$5 to $10 profit (partial win)
  - **Worst Case:** -$20 to -30 (capped loss)
- **Risk Level:** Balanced
- **When to Use:** Chop conditions + decent recovery odds

---

## Future Automation Considerations
- YAML rule:
  - Trigger hybrid logic if: DCA maxed AND drawdown >1.5% AND TP1 < 1.5% away
  - Require BTC = NEUTRAL or BULLISH, RSI slope ≥ -5
- Integration target: smart_dca_signal.py fallback mode




# 🛡️ Capital Protection Strategies for Full-Spend Trades

This document outlines proposed strategies to manage capital risk in trades where DCA budget is fully deployed and the trade remains unresolved (e.g., stuck near BE/TP1, showing health decay, or facing choppy BTC conditions).

---

## 🔁 Core Trade Status: Full-Spend Recovery Case

- **Trade**: USUAL/USDT
- **Total Spent**: $2000
- **BE Zone**: ~0.1288
- **TTP**: 0.6% gain from BE
- **Drawdown**: 2.53%
- **Confidence**: 0.82
- **Recovery Odds**: 0.94
- **BTC Sentiment**: Marked as 'Bullish', but visually appears choppy

---

## 🎯 Option A: Hold and Wait

- **Description**: Take no action, wait for trade to recover
- **Upside**: Full TP1 gain (~0.6%)
- **Downside**: Greater drawdown if BTC/alt reverses further
- **Use If**:
  - BTC is clearly trending up
  - Recovery odds & confidence remain > 0.80
  - No worsening score decay

## ✂️ Option B: Partial Exit (Capital Return)

- **Description**: Sell 50% (or another portion) to recover capital
- **Upside**: Retain partial upside if market recovers
- **Downside**: Lower overall gain if trade resolves to TP
- **Use If**:
  - Trade confidence is deteriorating
  - BTC is choppy or neutral
  - You want to reduce exposure

## 🛑 Option C: Auto-Close (Full Exit)

- **Description**: Sell entire position immediately
- **Upside**: Lock in remaining capital
- **Downside**: Realize current loss, miss any rebound
- **Use If**:
  - BTC breaks down / flips bearish
  - Indicators show no lift (e.g., MACD down, RSI declining)
  - Recovery odds < 0.70

## 🔀 Option D: Hybrid (Trailing SL or Panic Close Trigger)

- **Description**: Set a tight stop-loss (manual or TSL)
- **Upside**: Exit gracefully if trade reverses
- **Downside**: Could stop out just before recovery
- **Use If**:
  - BTC is range-bound with possible drop
  - Recovery odds borderline (0.70–0.80)
  - RSI/MACD show flat/slight negative

---

## 📊 BTC-Aware Capital Protection Matrix

| BTC Condition       | Suggested Action                    | Reasoning                                                                 |
|---------------------|--------------------------------------|--------------------------------------------------------------------------|
| ✅ Bullish Strong     | Hold for TP1 (or tighten SL)         | Favorable macro, likely to lift altcoins                                 |
| ⚠️ Bullish Choppy    | Hybrid (partial + trailing SL)       | Risk of whipsaw — hedge downside while retaining some exposure           |
| 🟡 Neutral Flat      | Partial Exit                         | No strong trend to carry trade, reduce exposure                          |
| ❌ Bearish Weak      | Auto-Close or Tight SL               | Risk of loss increases sharply, protect principal                        |
| 🔻 Bearish Breakdown | Exit Immediately                     | Market deterioration — avoid full stop-out losses                        |

---

## 🔐 Future Enhancements

- Integrate this logic into smart DCA or SAFU pipeline
- Use BTC context + recovery snapshot to trigger overrides
- Add confidence-decay guardrails to switch protection mode dynamically

---

## ✅ Next Review
Revisit these ideas after next batch of failed/fragile trades. Consider if PnL delta between *Hold vs Partial Exit* is meaningful enough to automate decision logic.
