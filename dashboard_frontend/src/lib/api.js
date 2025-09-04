/**
 * Unified API Client for Market7 Dashboard
 * Handles all API calls with proper error handling and retry logic
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeout = 30000; // 30 seconds
    this.retryAttempts = 3;
    this.retryDelay = 1000; // 1 second
  }

  /**
   * Make HTTP request with retry logic
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: this.timeout,
      ...options,
    };

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
      } catch (error) {
        console.warn(`API request attempt ${attempt} failed:`, error.message);
        
        if (attempt === this.retryAttempts) {
          throw new Error(`API request failed after ${this.retryAttempts} attempts: ${error.message}`);
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
      }
    }
  }

  /**
   * Get account summary
   */
  async getAccountSummary() {
    try {
      return await this.request('/api/account/summary');
    } catch (error) {
      console.error('Failed to fetch account summary:', error);
      return {
        summary: {
          balance: 0,
          today_pnl: 0,
          total_pnl: 0,
          active_trades: 0,
          allocated: 0,
          upnl: 0
        },
        error: error.message
      };
    }
  }

  /**
   * Get active trades
   */
  async getActiveTrades() {
    try {
      return await this.request('/api/trades/active');
    } catch (error) {
      console.error('Failed to fetch active trades:', error);
      return {
        dca_trades: [],
        count: 0,
        error: error.message
      };
    }
  }

  /**
   * Get 3Commas metrics
   */
  async get3CommasMetrics() {
    try {
      return await this.request('/api/3commas/metrics');
    } catch (error) {
      console.error('Failed to fetch 3Commas metrics:', error);
      return {
        error: error.message,
        metrics: {
          open_pnl: 0,
          daily_realized_pnl: 0,
          realized_pnl_alltime: 0,
          total_deals: 0,
          win_rate: 0,
          active_deals: []
        }
      };
    }
  }

  /**
   * Get BTC context
   */
  async getBTCContext() {
    try {
      return await this.request('/api/btc/context');
    } catch (error) {
      console.error('Failed to fetch BTC context:', error);
      return {
        status: 'UNKNOWN',
        rsi: 0,
        adx: 0,
        ema: 0,
        close: 0,
        error: error.message
      };
    }
  }

  /**
   * Get fork metrics
   */
  async getForkMetrics() {
    try {
      return await this.request('/api/fork/metrics');
    } catch (error) {
      console.error('Failed to fetch fork metrics:', error);
      return {
        error: error.message,
        summary: {
          balance: 0,
          today_pnl: 0,
          total_pnl: 0,
          active_trades: 0,
          allocated: 0,
          upnl: 0
        }
      };
    }
  }

  /**
   * Get ML confidence data
   */
  async getMLConfidence() {
    try {
      return await this.request('/api/ml/confidence');
    } catch (error) {
      console.error('Failed to fetch ML confidence:', error);
      return {
        error: error.message,
        confidence: 0
      };
    }
  }

  /**
   * Get trade health for specific symbol
   */
  async getTradeHealth(symbol) {
    try {
      return await this.request(`/api/trade-health/${symbol}`);
    } catch (error) {
      console.error(`Failed to fetch trade health for ${symbol}:`, error);
      return {
        symbol: symbol,
        score: 0,
        error: error.message
      };
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      return await this.request('/health');
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message
      };
    }
  }
}

// Create singleton instance
const apiClient = new ApiClient();

export default apiClient;