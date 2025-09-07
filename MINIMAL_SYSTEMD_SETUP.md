# 🚀 Minimal Systemd Setup Guide - MarketPilot

## 📋 **OVERVIEW**

This guide shows you how to run MarketPilot with minimal systemd dependency, making refactoring much easier while maintaining reliability.

---

## 🎯 **DEPLOYMENT OPTIONS**

### **Option 1: Standalone Runner (Recommended)**
**Single process runs all services with internal coordination**

```bash
# Run everything in one process
python3 standalone_runner.py
```

**Pros:**
- ✅ No systemd required
- ✅ Easy to debug and refactor
- ✅ Single process to manage
- ✅ Built-in health monitoring

**Cons:**
- ⚠️ Single point of failure
- ⚠️ All services share resources

### **Option 2: Cron-based Execution**
**Services run as scheduled tasks via cron**

```bash
# Setup cron jobs
chmod +x setup_cron.sh
./setup_cron.sh

# Start services
./start_marketpilot.sh
```

**Pros:**
- ✅ No systemd required
- ✅ Services run independently
- ✅ Easy to schedule different intervals
- ✅ Built-in log rotation

**Cons:**
- ⚠️ No automatic restart on failure
- ⚠️ Cron dependency

### **Option 3: Simple Process Manager**
**Custom process manager with auto-restart**

```bash
# Run with process manager
python3 simple_manager.py
```

**Pros:**
- ✅ No systemd required
- ✅ Automatic restart on failure
- ✅ Independent processes
- ✅ Easy to manage

**Cons:**
- ⚠️ Custom process management
- ⚠️ More complex than standalone

---

## 🔧 **QUICK SETUP**

### **Step 1: Install Dependencies**

```bash
# Option A: Use system packages (recommended)
sudo apt update
sudo apt install python3-pip python3-venv python3-pandas python3-requests

# Option B: Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Step 2: Choose Your Approach**

#### **For Development/Testing:**
```bash
# Standalone runner (easiest)
python3 standalone_runner.py
```

#### **For Production:**
```bash
# Cron-based (most reliable)
./setup_cron.sh
./start_marketpilot.sh
```

#### **For Custom Management:**
```bash
# Process manager
python3 simple_manager.py
```

---

## 📊 **SERVICE CONFIGURATION**

### **Service Intervals (Configurable)**

| Service | Default Interval | Purpose |
|---------|------------------|---------|
| **Indicators** | 60 seconds | Calculate technical indicators |
| **DCA** | 30 seconds | Process DCA decisions |
| **Fork Detection** | 120 seconds | Detect trading opportunities |
| **ML Inference** | 300 seconds | Run ML predictions |

### **Modify Intervals**

Edit the configuration in your chosen runner:

```python
# In standalone_runner.py or simple_manager.py
self.config = {
    "indicator_interval": 60,  # seconds
    "dca_interval": 30,        # seconds
    "fork_interval": 120,      # seconds
    "ml_interval": 300,        # seconds
}
```

---

## 🚀 **EXECUTION EXAMPLES**

### **Standalone Runner**
```bash
# Start all services
python3 standalone_runner.py

# Check logs
tail -f logs/standalone_runner.log
```

### **Cron-based**
```bash
# Setup and start
./setup_cron.sh
./start_marketpilot.sh

# Check status
./status_marketpilot.sh

# Stop services
./stop_marketpilot.sh
```

### **Process Manager**
```bash
# Start with auto-restart
python3 simple_manager.py

# Check logs
tail -f logs/simple_manager.log
```

---

## 🔍 **MONITORING & DEBUGGING**

### **Check Service Status**
```bash
# For cron-based
./status_marketpilot.sh

# For standalone/manager
tail -f logs/*.log
```

### **View Logs**
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/indicators.log
tail -f logs/dca.log
tail -f logs/fork.log
```

### **Manual Service Testing**
```bash
# Test individual services
python3 data/rolling_indicators_standalone.py
python3 dca/smart_dca_core.py
python3 fork/fork_runner.py
```

---

## 🛠️ **REFACTORING FRIENDLY**

### **Easy Service Modification**
1. **Edit service scripts** - No systemd files to update
2. **Test changes** - Run individual services manually
3. **Deploy changes** - Restart the runner/manager
4. **No systemd reload** - Changes take effect immediately

### **Development Workflow**
```bash
# 1. Make changes to service
nano dca/smart_dca_core.py

# 2. Test the service
python3 dca/smart_dca_core.py

# 3. Restart runner
pkill -f standalone_runner.py
python3 standalone_runner.py
```

---

## ⚠️ **TROUBLESHOOTING**

### **Common Issues**

#### **1. Missing Dependencies**
```bash
# Install system packages
sudo apt install python3-pandas python3-requests python3-numpy

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **2. Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping

# Start Redis if needed
redis-server --daemonize yes
```

#### **3. Permission Issues**
```bash
# Make scripts executable
chmod +x *.py *.sh

# Check file permissions
ls -la *.py *.sh
```

#### **4. Service Not Starting**
```bash
# Check logs
tail -f logs/*.log

# Test individual service
python3 data/rolling_indicators_standalone.py
```

---

## 🎯 **RECOMMENDATIONS**

### **For Development:**
- **Use Standalone Runner** - Easiest to debug and modify
- **Manual testing** - Run individual services as needed
- **Quick iteration** - No systemd restart required

### **For Production:**
- **Use Cron-based** - Most reliable and standard
- **Process monitoring** - Add external monitoring if needed
- **Log rotation** - Built-in log management

### **For Custom Needs:**
- **Use Process Manager** - Full control over process lifecycle
- **Custom intervals** - Adjust timing as needed
- **Health checks** - Built-in service monitoring

---

## 🎉 **BENEFITS OF MINIMAL SYSTEMD**

✅ **Easy Refactoring** - No systemd files to update
✅ **Quick Testing** - Run services manually
✅ **Simple Debugging** - Direct process control
✅ **Flexible Deployment** - Multiple execution options
✅ **Development Friendly** - Fast iteration cycles
✅ **Production Ready** - Reliable execution methods

---

## 📞 **SUPPORT**

If you encounter issues:

1. **Check logs** - `tail -f logs/*.log`
2. **Test individual services** - Run each service manually
3. **Verify dependencies** - Ensure all packages are installed
4. **Check Redis** - Ensure Redis is running
5. **Review configuration** - Verify settings are correct

**This approach gives you maximum flexibility with minimal systemd dependency!** 🚀
