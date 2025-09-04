import React, { createContext, useContext, useReducer, useEffect } from 'react';
import apiClient from '../lib/api';

// Initial state
const initialState = {
  user: null,
  settings: {
    theme: 'dark',
    refreshInterval: 30000,
    notifications: true
  },
  system: {
    status: 'loading',
    lastUpdate: null,
    errors: []
  },
  trading: {
    activeTrades: [],
    accountSummary: null,
    btcContext: null
  }
};

// Action types
const ActionTypes = {
  SET_USER: 'SET_USER',
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
  SET_SYSTEM_STATUS: 'SET_SYSTEM_STATUS',
  ADD_ERROR: 'ADD_ERROR',
  CLEAR_ERRORS: 'CLEAR_ERRORS',
  UPDATE_TRADING_DATA: 'UPDATE_TRADING_DATA',
  SET_LOADING: 'SET_LOADING'
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_USER:
      return { ...state, user: action.payload };
    
    case ActionTypes.UPDATE_SETTINGS:
      return { 
        ...state, 
        settings: { ...state.settings, ...action.payload } 
      };
    
    case ActionTypes.SET_SYSTEM_STATUS:
      return { 
        ...state, 
        system: { ...state.system, ...action.payload } 
      };
    
    case ActionTypes.ADD_ERROR:
      return {
        ...state,
        system: {
          ...state.system,
          errors: [...state.system.errors, action.payload]
        }
      };
    
    case ActionTypes.CLEAR_ERRORS:
      return {
        ...state,
        system: { ...state.system, errors: [] }
      };
    
    case ActionTypes.UPDATE_TRADING_DATA:
      return {
        ...state,
        trading: { ...state.trading, ...action.payload }
      };
    
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        system: { ...state.system, status: 'loading' }
      };
    
    default:
      return state;
  }
};

// Context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Initialize app data
  useEffect(() => {
    const initializeApp = async () => {
      try {
        dispatch({ type: ActionTypes.SET_LOADING });
        
        // Load initial data
        const [accountSummary, activeTrades, btcContext] = await Promise.all([
          apiClient.getAccountSummary(),
          apiClient.getActiveTrades(),
          apiClient.getBTCContext()
        ]);

        dispatch({
          type: ActionTypes.UPDATE_TRADING_DATA,
          payload: {
            accountSummary,
            activeTrades: activeTrades.dca_trades || [],
            btcContext
          }
        });

        dispatch({
          type: ActionTypes.SET_SYSTEM_STATUS,
          payload: {
            status: 'ready',
            lastUpdate: new Date().toISOString()
          }
        });
      } catch (error) {
        dispatch({
          type: ActionTypes.ADD_ERROR,
          payload: {
            message: 'Failed to initialize app',
            error: error.message,
            timestamp: new Date().toISOString()
          }
        });
        
        dispatch({
          type: ActionTypes.SET_SYSTEM_STATUS,
          payload: { status: 'error' }
        });
      }
    };

    initializeApp();
  }, []);

  // Auto-refresh trading data
  useEffect(() => {
    if (state.system.status !== 'ready') return;

    const interval = setInterval(async () => {
      try {
        const [accountSummary, activeTrades, btcContext] = await Promise.all([
          apiClient.getAccountSummary(),
          apiClient.getActiveTrades(),
          apiClient.getBTCContext()
        ]);

        dispatch({
          type: ActionTypes.UPDATE_TRADING_DATA,
          payload: {
            accountSummary,
            activeTrades: activeTrades.dca_trades || [],
            btcContext
          }
        });

        dispatch({
          type: ActionTypes.SET_SYSTEM_STATUS,
          payload: {
            lastUpdate: new Date().toISOString()
          }
        });
      } catch (error) {
        dispatch({
          type: ActionTypes.ADD_ERROR,
          payload: {
            message: 'Auto-refresh failed',
            error: error.message,
            timestamp: new Date().toISOString()
          }
        });
      }
    }, state.settings.refreshInterval);

    return () => clearInterval(interval);
  }, [state.system.status, state.settings.refreshInterval]);

  // Context value
  const value = {
    state,
    dispatch,
    actions: {
      setUser: (user) => dispatch({ type: ActionTypes.SET_USER, payload: user }),
      updateSettings: (settings) => dispatch({ 
        type: ActionTypes.UPDATE_SETTINGS, 
        payload: settings 
      }),
      addError: (error) => dispatch({ 
        type: ActionTypes.ADD_ERROR, 
        payload: error 
      }),
      clearErrors: () => dispatch({ type: ActionTypes.CLEAR_ERRORS }),
      refreshData: async () => {
        try {
          dispatch({ type: ActionTypes.SET_LOADING });
          
          const [accountSummary, activeTrades, btcContext] = await Promise.all([
            apiClient.getAccountSummary(),
            apiClient.getActiveTrades(),
            apiClient.getBTCContext()
          ]);

          dispatch({
            type: ActionTypes.UPDATE_TRADING_DATA,
            payload: {
              accountSummary,
              activeTrades: activeTrades.dca_trades || [],
              btcContext
            }
          });

          dispatch({
            type: ActionTypes.SET_SYSTEM_STATUS,
            payload: {
              status: 'ready',
              lastUpdate: new Date().toISOString()
            }
          });
        } catch (error) {
          dispatch({
            type: ActionTypes.ADD_ERROR,
            payload: {
              message: 'Manual refresh failed',
              error: error.message,
              timestamp: new Date().toISOString()
            }
          });
        }
      }
    }
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export default AppContext;