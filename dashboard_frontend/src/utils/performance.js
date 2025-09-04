/**
 * Performance monitoring utilities
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.init();
  }

  init() {
    // Monitor Core Web Vitals
    this.observeWebVitals();
    
    // Monitor API performance
    this.observeAPICalls();
    
    // Monitor component render times
    this.observeComponentPerformance();
  }

  observeWebVitals() {
    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.recordMetric('lcp', lastEntry.startTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          this.recordMetric('fid', entry.processingStart - entry.startTime);
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });

      // Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            this.recordMetric('cls', clsValue);
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    }
  }

  observeAPICalls() {
    const originalFetch = window.fetch;
    const self = this;

    window.fetch = function(...args) {
      const startTime = performance.now();
      const url = args[0];
      
      return originalFetch.apply(this, args)
        .then(response => {
          const endTime = performance.now();
          const duration = endTime - startTime;
          
          self.recordMetric('api_call', {
            url,
            duration,
            status: response.status,
            success: response.ok
          });
          
          return response;
        })
        .catch(error => {
          const endTime = performance.now();
          const duration = endTime - startTime;
          
          self.recordMetric('api_error', {
            url,
            duration,
            error: error.message
          });
          
          throw error;
        });
    };
  }

  observeComponentPerformance() {
    // This would be implemented with React DevTools Profiler
    // or custom hooks in production
  }

  recordMetric(name, value) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    const metric = {
      name,
      value,
      timestamp: Date.now(),
      url: window.location.href
    };
    
    this.metrics.get(name).push(metric);
    
    // Keep only last 100 entries per metric
    if (this.metrics.get(name).length > 100) {
      this.metrics.get(name).shift();
    }
    
    // Notify observers
    this.notifyObservers(name, metric);
  }

  getMetric(name) {
    return this.metrics.get(name) || [];
  }

  getMetricAverage(name) {
    const values = this.getMetric(name);
    if (values.length === 0) return 0;
    
    const sum = values.reduce((acc, metric) => acc + metric.value, 0);
    return sum / values.length;
  }

  subscribe(name, callback) {
    if (!this.observers.has(name)) {
      this.observers.set(name, []);
    }
    this.observers.get(name).push(callback);
  }

  unsubscribe(name, callback) {
    if (this.observers.has(name)) {
      const callbacks = this.observers.get(name);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyObservers(name, metric) {
    if (this.observers.has(name)) {
      this.observers.get(name).forEach(callback => {
        try {
          callback(metric);
        } catch (error) {
          console.error('Performance observer error:', error);
        }
      });
    }
  }

  getReport() {
    const report = {};
    
    for (const [name, values] of this.metrics) {
      report[name] = {
        count: values.length,
        average: this.getMetricAverage(name),
        latest: values[values.length - 1]?.value || 0,
        min: Math.min(...values.map(v => v.value)),
        max: Math.max(...values.map(v => v.value))
      };
    }
    
    return report;
  }

  sendReport() {
    const report = this.getReport();
    
    // Send to analytics service
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/analytics/performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report)
      }).catch(error => {
        console.error('Failed to send performance report:', error);
      });
    } else {
      console.log('Performance Report:', report);
    }
  }
}

// Create global instance
const performanceMonitor = new PerformanceMonitor();

// Send report every 5 minutes
setInterval(() => {
  performanceMonitor.sendReport();
}, 5 * 60 * 1000);

export default performanceMonitor;