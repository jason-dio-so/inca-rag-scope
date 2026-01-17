/**
 * CustomerHub - Main Entry Point Component
 *
 * Purpose: Display Q1~Q4 cards for customer navigation
 * Rules:
 * - NO legacy UI imports
 * - NO chat UI imports
 * - NO demo-q12 imports
 * - Clean, simple card grid
 */

'use client';

import { QCard, QCardProps } from './QCard';

const Q_CARDS: QCardProps[] = [
  {
    qNumber: 'Q1',
    title: 'Q1 보험료 비교',
    description: '같은 기준에서 보험사별 보험료를 저렴한 순으로 비교합니다.',
    example: '가장 저렴한 보험료 순서대로 4개만 비교해줘',
    icon: '💰',
    route: '/q1',
    color: 'border-blue-300 hover:border-blue-500'
  },
  {
    qNumber: 'Q2',
    title: 'Q2 보장한도 차이',
    description: '담보별 보장한도 차이를 보험사별로 비교합니다.',
    example: '암직접입원비 담보 중 보장한도가 다른 상품 찾아줘',
    icon: '📊',
    route: '/q2',
    color: 'border-green-300 hover:border-green-500'
  },
  {
    qNumber: 'Q3',
    title: 'Q3 종합 비교',
    description: '여러 요소를 종합해 비교 요약과 추천을 제공합니다.',
    example: '삼성 메리츠 암진단비 비교',
    icon: '📋',
    route: '/q3',
    color: 'border-purple-300 hover:border-purple-500'
  },
  {
    qNumber: 'Q4',
    title: 'Q4 경계 조건',
    description: '제자리암·경계성종양 등 경계 조건 보장 여부를 비교합니다.',
    example: '제자리암 경계성종양 보장 여부 비교',
    icon: '✓',
    route: '/q4',
    color: 'border-orange-300 hover:border-orange-500'
  }
];

export function CustomerHub() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            보험 비교 도우미
          </h1>
          <p className="text-lg text-gray-600">
            원하는 비교 유형을 선택하세요
          </p>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Q_CARDS.map((card) => (
            <QCard key={card.qNumber} {...card} />
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-sm font-bold text-gray-900 mb-2">
            안내사항
          </h3>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• 모든 비교 내용은 약관 및 상품 설명서 기준입니다</li>
            <li>• 기준일: 2025-11-26</li>
            <li>• 최종 가입 전 반드시 약관을 직접 확인하시기 바랍니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
