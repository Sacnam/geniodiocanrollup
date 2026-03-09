"""
GitHub-style activity heatmap component.
"""
import React, { useMemo } from 'react';
import type { ActivityHeatmapData } from '../types/analytics';

interface ActivityHeatmapProps {
  data: ActivityHeatmapData;
}

export function ActivityHeatmap({ data }: ActivityHeatmapProps) {
  const weeks = useMemo(() => {
    // Group days into weeks
    const weeks: typeof data.data[] = [];
    let currentWeek: typeof data.data = [];
    
    data.data.forEach((day, index) => {
      const date = new Date(day.date);
      const dayOfWeek = date.getDay();
      
      // Start new week on Sunday (0)
      if (dayOfWeek === 0 && currentWeek.length > 0) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      
      currentWeek.push(day);
    });
    
    if (currentWeek.length > 0) {
      weeks.push(currentWeek);
    }
    
    return weeks;
  }, [data.data]);
  
  const monthLabels = useMemo(() => {
    const labels: { month: string; weekIndex: number }[] = [];
    let lastMonth = '';
    
    weeks.forEach((week, weekIndex) => {
      const firstDay = week[0];
      if (firstDay) {
        const date = new Date(firstDay.date);
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        
        if (month !== lastMonth) {
          labels.push({ month, weekIndex });
          lastMonth = month;
        }
      }
    });
    
    return labels;
  }, [weeks]);
  
  const getTooltip = (day: typeof data.data[0]) => {
    const date = new Date(day.date).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
    
    if (day.count === 0) {
      return `${date}: No reading`;
    }
    
    return `${date}: ${day.count} articles read (${day.minutes_spent} min)`;
  };
  
  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        {/* Month labels */}
        <div className="flex mb-1 text-xs text-muted-foreground">
          <div className="w-8" /> {/* Spacer for day labels */}
          {monthLabels.map(({ month, weekIndex }) => (
            <div
              key={`${month}-${weekIndex}`}
              className="flex-shrink-0"
              style={{ 
                width: `${weekIndex === 0 ? 1 : 2}em`,
                marginLeft: weekIndex === 0 ? 0 : `${(weekIndex - 1) * 0.5}em`
              }}
            >
              {month}
            </div>
          ))}
        </div>
        
        <div className="flex">
          {/* Day labels */}
          <div className="flex flex-col gap-1 mr-2 text-xs text-muted-foreground">
            <div className="h-3" /> {/* Spacer */}
            <div className="h-3">Mon</div>
            <div className="h-3" />
            <div className="h-3">Wed</div>
            <div className="h-3" />
            <div className="h-3">Fri</div>
            <div className="h-3" />
          </div>
          
          {/* Heatmap grid */}
          <div className="flex gap-1">
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex flex-col gap-1">
                {Array.from({ length: 7 }).map((_, dayIndex) => {
                  const day = week.find((d) => {
                    const date = new Date(d.date);
                    // Adjust so Monday is 0
                    const adjustedDay = (date.getDay() + 6) % 7;
                    return adjustedDay === dayIndex;
                  });
                  
                  if (!day) {
                    return <div key={dayIndex} className="w-3 h-3" />;
                  }
                  
                  return (
                    <div
                      key={day.date}
                      className={`w-3 h-3 rounded-sm transition-all hover:ring-2 hover:ring-primary ${
                        day.level === 0 ? 'bg-muted' :
                        day.level === 1 ? 'bg-green-200' :
                        day.level === 2 ? 'bg-green-300' :
                        day.level === 3 ? 'bg-green-400' :
                        'bg-green-500'
                      }`}
                      title={getTooltip(day)}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
