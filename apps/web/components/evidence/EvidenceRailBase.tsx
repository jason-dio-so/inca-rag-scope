/**
 * EvidenceRailBase - Base Component for Evidence Panel
 *
 * Purpose: Shared UI structure for Q2-Q4 Evidence Rails
 * Rules:
 * - This component is Evidence-only (forbidden terms allowed)
 * - Fixed right-side panel (384px width)
 * - Sections-based content rendering
 * - Close button functionality
 */

'use client';

import { ReactNode } from 'react';

export interface EvidenceSection {
  heading: string;
  body: ReactNode;
}

interface EvidenceRailBaseProps {
  title: string;
  subtitle?: string;
  isOpen: boolean;
  onClose: () => void;
  sections: EvidenceSection[];
  badge?: string | number;
}

export function EvidenceRailBase({
  title,
  subtitle,
  isOpen,
  onClose,
  sections,
  badge
}: EvidenceRailBaseProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-300 shadow-xl overflow-y-auto z-50">
      {/* Header */}
      <div className="sticky top-0 bg-blue-600 text-white px-6 py-4 border-b border-blue-700">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {badge !== undefined && (
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-700 text-white text-sm font-bold">
                  {badge}
                </span>
              )}
              <h2 className="text-lg font-bold">{title}</h2>
            </div>
            {subtitle && (
              <p className="text-sm text-blue-100 line-clamp-2">
                {subtitle}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-2 text-white hover:text-blue-200 transition-colors"
            aria-label="Close evidence rail"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Content - Sections */}
      <div className="px-6 py-6 space-y-6">
        {sections.map((section, idx) => (
          <section key={idx} className="space-y-3">
            <h3 className="text-base font-bold text-gray-900 border-b-2 border-blue-500 pb-2">
              {section.heading}
            </h3>
            <div>{section.body}</div>
          </section>
        ))}
      </div>
    </div>
  );
}
