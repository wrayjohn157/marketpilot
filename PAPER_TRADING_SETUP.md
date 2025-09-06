# 🧪 Paper Trading Setup Guide - MarketPilot

## 📋 **OVERVIEW**

This guide will help you configure MarketPilot for paper trading on 3Commas. Paper trading allows you to test the system with virtual money without risking real funds.

---

## 🔑 **STEP 1: Get 3Commas Paper Trading Credentials**

### **1.1 Create 3Commas Account**
1. Go to [3Commas.io](https://3commas.io)
2. Sign up for a free account
3. Verify your email address

### **1.2 Enable Paper Trading**
1. Log into your 3Commas account
2. Go to **Settings** → **API Keys**
3. Create a new API key with **Paper Trading** permissions
4. Note down your:
   - **API Key**
   - **API Secret**
   - **Account ID** (for paper trading)

### **1.3 Create Paper Trading Bots**
1. Go to **Bots** → **Create Bot**
2. Select **Paper Trading** mode
3. Create at least 2 bots:
   - **Bot 1**: For fork trading signals
   - **Bot 2**: For DCA trading signals
4. Note down the **Bot IDs**

---

## ⚙️ **STEP 2: Configure MarketPilot**

### **2.1 Update Paper Trading Credentials**

Edit `/home/signal/marketpilot/config/paper_cred.json`:

```json
{
  "3commas_api_key": "YOUR_PAPER_API_KEY_HERE",
  "3commas_api_secret": "YOUR_PAPER_API_SECRET_HERE",
  "3commas_bot_id": "YOUR_FORK_BOT_ID_HERE",
  "3commas_bot_id2": "YOUR_DCA_BOT_ID_HERE",
  "3commas_email_token": "YOUR_EMAIL_TOKEN_HERE",
  "3commas_account_id": "YOUR_PAPER_ACCOUNT_ID_HERE"
}
```

### **2.2 Verify Configuration**

The system is already configured to use paper trading credentials. Key files:

- **Main Config**: `config/paths_config.yaml` → `paper_cred_path`
- **Credential Manager**: `utils/credential_manager.py`
- **Fork Runner**: `fork/fork_runner.py`
- **DCA System**: `dca/smart_dca_core.py`
- **Dashboard Backend**: `dashboard_backend/threecommas_metrics.py`

---

## 🚀 **STEP 3: Test Paper Trading Setup**

### **3.1 Test API Connection**

```bash
cd /home/signal/marketpilot
python3 -c "
import json
from utils.credential_manager import get_3commas_credentials
try:
    creds = get_3commas_credentials()
    print('✅ Paper trading credentials loaded successfully')
    print(f'Bot ID 1: {creds.get(\"3commas_bot_id\")}')
    print(f'Bot ID 2: {creds.get(\"3commas_bot_id2\")}')
    print(f'Account ID: {creds.get(\"3commas_account_id\")}')
except Exception as e:
    print(f'❌ Error loading credentials: {e}')
"
```

### **3.2 Test Fork Detection**

```bash
cd /home/signal/marketpilot
python3 fork/fork_runner.py --test
```

### **3.3 Test DCA System**

```bash
cd /home/signal/marketpilot
python3 dca/smart_dca_core.py --test
```

---

## 📊 **STEP 4: Monitor Paper Trading**

### **4.1 Dashboard Access**

1. Start the backend:
   ```bash
   cd /home/signal/marketpilot/dashboard_backend
   python3 main.py
   ```

2. Start the frontend:
   ```bash
   cd /home/signal/marketpilot/dashboard_frontend
   npm install
   npm start
   ```

3. Access: `http://localhost:3000`

### **4.2 3Commas Dashboard**

- Monitor your paper trading bots in the 3Commas interface
- Check trade execution and performance
- Verify that signals are being received correctly

---

## 🔧 **STEP 5: Configuration Options**

### **5.1 Paper Trading Specific Settings**

The system automatically detects paper trading mode and adjusts:

- **API Endpoints**: Uses 3Commas paper trading API
- **Risk Management**: Conservative settings for testing
- **Logging**: Enhanced logging for paper trading activities
- **Simulation**: Full simulation mode enabled

### **5.2 Custom Paper Trading Config**

You can create custom paper trading configurations:

```yaml
# config/paper_trading_config.yaml
paper_trading:
  enabled: true
  risk_multiplier: 0.1  # 10% of normal risk
  max_position_size: 100  # $100 max per trade
  test_mode: true
  detailed_logging: true
```

---

## ⚠️ **IMPORTANT NOTES**

### **Security**
- **Never commit real API keys** to version control
- **Use paper trading credentials only** for testing
- **Keep credentials secure** and private

### **Testing Best Practices**
- **Start with small amounts** even in paper trading
- **Test all features** before going live
- **Monitor performance** and adjust settings
- **Document any issues** you encounter

### **Paper Trading Limitations**
- **No real money** at risk
- **Market conditions** may differ from live trading
- **Execution delays** may not reflect real trading
- **Emotional factors** not present in paper trading

---

## 🎯 **NEXT STEPS**

### **After Paper Trading Setup:**
1. **Test all features** thoroughly
2. **Monitor performance** for at least a week
3. **Adjust parameters** based on results
4. **Document any issues** or improvements
5. **Prepare for live trading** when ready

### **Live Trading Transition:**
1. **Create live trading credentials**
2. **Update configuration** to use live credentials
3. **Start with small amounts**
4. **Monitor closely** for the first few days
5. **Scale up gradually** as confidence grows

---

## 📞 **SUPPORT**

If you encounter any issues:

1. **Check the logs** in `/home/signal/marketpilot/logs/`
2. **Verify credentials** are correct
3. **Test API connection** manually
4. **Review configuration** files
5. **Check 3Commas dashboard** for bot status

---

## 🎉 **CONCLUSION**

Paper trading is an excellent way to test MarketPilot without risk. Follow this guide carefully, and you'll have a fully functional paper trading system ready for testing!

**Happy Paper Trading!** 🚀
