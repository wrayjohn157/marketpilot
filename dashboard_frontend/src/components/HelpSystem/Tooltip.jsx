import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

const Tooltip = ({ content, position = 'top', children }) => {
  const [isVisible, setIsVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  };

  const arrowClasses = {
    top: 'top-full left-1/2 transform -translate-x-1/2 border-t-gray-800',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-b-gray-800',
    left: 'left-full top-1/2 transform -translate-y-1/2 border-l-gray-800',
    right: 'right-full top-1/2 transform -translate-y-1/2 border-r-gray-800'
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="inline-block"
      >
        {children || (
          <HelpCircle 
            size={16} 
            className="text-gray-400 hover:text-gray-600 cursor-help transition-colors" 
          />
        )}
      </div>

      {isVisible && (
        <div
          className={`absolute z-50 bg-gray-800 text-white text-sm rounded-lg px-3 py-2 max-w-xs shadow-lg ${positionClasses[position]}`}
        >
          <div className="whitespace-pre-line">{content}</div>
          
          {/* Arrow */}
          <div
            className={`absolute w-0 h-0 border-4 border-transparent ${arrowClasses[position]}`}
          />
        </div>
      )}
    </div>
  );
};

export default Tooltip;