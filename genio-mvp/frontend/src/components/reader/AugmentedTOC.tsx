/**
 * Augmented Table of Contents with Concept Density Heatmap
 * From LIBRARY_PRD.md §3.5
 */
import React from 'react';
import { BookOpen, ChevronRight } from 'lucide-react';

interface Chapter {
  title: string;
  position: number;  // 0-1 position in document
  concept_density: number;  // 0-1 density score
  atom_count: number;
  is_core_thesis: boolean;
}

interface AugmentedTOCProps {
  chapters: Chapter[];
  currentPosition: number;
  onChapterClick: (position: number) => void;
  documentProgress: number;
}

export const AugmentedTOC: React.FC<AugmentedTOCProps> = ({
  chapters,
  currentPosition,
  onChapterClick,
  documentProgress,
}) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          Contents
        </h3>
        <span className="text-sm text-gray-500">
          {Math.round(documentProgress * 100)}% read
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${documentProgress * 100}%` }}
        />
      </div>

      {/* Chapter list */}
      <div className="space-y-1 max-h-[400px] overflow-y-auto">
        {chapters.map((chapter, index) => {
          const isActive = currentPosition >= chapter.position && 
                          (index === chapters.length - 1 || currentPosition < chapters[index + 1].position);
          
          return (
            <button
              key={index}
              onClick={() => onChapterClick(chapter.position)}
              className={`
                w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3
                ${isActive ? 'bg-blue-50 border-l-4 border-blue-500' : 'hover:bg-gray-50'}
              `}
            >
              {/* Concept density indicator */}
              <div 
                className="w-2 h-8 rounded-full"
                style={{
                  backgroundColor: getDensityColor(chapter.concept_density),
                }}
                title={`Concept density: ${Math.round(chapter.concept_density * 100)}%`}
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`
                    font-medium truncate
                    ${isActive ? 'text-blue-900' : 'text-gray-700'}
                  `}>
                    {chapter.title}
                  </span>
                  {chapter.is_core_thesis && (
                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                      Core
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{chapter.atom_count} atoms</span>
                  <span>·</span>
                  <span>{Math.round(chapter.concept_density * 100)}% density</span>
                </div>
              </div>

              <ChevronRight className={`
                w-4 h-4 flex-shrink-0
                ${isActive ? 'text-blue-600' : 'text-gray-400'}
              `} />
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t text-xs text-gray-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            High density
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-gray-300" />
            Low
          </span>
        </div>
      </div>
    </div>
  );
};

function getDensityColor(density: number): string {
  if (density > 0.7) return '#22c55e';  // Green - high density
  if (density > 0.4) return '#eab308';  // Yellow - medium
  return '#d1d5db';  // Gray - low
}
