"""
Bar chart for hourly reading activity.
"""
import React from 'react';
import type { HourlyActivity } from '../types/analytics';

interface HourlyChartProps {
  data: HourlyActivity[];
}

export function HourlyChart({ data }: HourlyChartProps) {
  const maxCount = Math.max(...data.map(d => d.count), 1);
  
  return (
    <div className="h-48">
      <div className="flex items-end justify-between h-full gap-1">
        {data.map((hour) => (
          <div
            key={hour.hour}
            className="flex-1 flex flex-col items-center gap-1"
          >
            <div className="w-full relative group">
              <div
                className="bg-primary/80 rounded-t transition-all hover:bg-primary"
                style={{ 
                  height: `${(hour.count / maxCount) * 100}%`,
                  minHeight: hour.count > 0 ? 4 : 0
                }}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                {hour.hour}:00 - {hour.count} articles ({hour.percentage}%)
              </div>
            </div>
            {/* Hour label - show every 3rd hour */}
            {hour.hour % 3 === 0 && (
              <span className="text-xs text-muted-foreground">
                {hour.hour}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
