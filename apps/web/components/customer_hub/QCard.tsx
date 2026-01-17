/**
 * QCard - Customer Hub Card Component
 *
 * Purpose: Display Q1~Q4 cards on main hub
 * Rules:
 * - NO legacy UI imports
 * - NO chat UI imports
 * - Simple click-to-route behavior
 */

'use client';

import Link from 'next/link';

export interface QCardProps {
  qNumber: string;
  title: string;
  description: string;
  example?: string;
  icon: string;
  route: string;
  color: string;
}

export function QCard({ qNumber, title, description, example, icon, route, color }: QCardProps) {
  return (
    <Link
      href={route}
      className={`block bg-white rounded-lg border-2 ${color} hover:shadow-lg transition-all duration-200 p-6 group`}
    >
      <div className="flex items-start gap-4">
        <div className={`text-4xl ${color.replace('border-', 'text-')}`}>
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 mb-2">
            {title}
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-2">
            {description}
          </p>
          {example && (
            <p className="text-xs text-gray-500 italic">
              예: "{example}"
            </p>
          )}
        </div>
        <div className="text-gray-400 group-hover:text-blue-600 transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
