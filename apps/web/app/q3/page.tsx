/**
 * Q3 Page - 종합 비교 리포트
 *
 * Purpose: Detailed coverage comparison with judgment and recommendation
 * Status: Evidence Rail integrated
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Q3ThreePartView, Q3Row } from '@/components/chat/Q3ThreePartView';
import { Q3EvidenceRail } from '@/components/q3/Q3EvidenceRail';

export default function Q3Page() {
  const [selectedRow, setSelectedRow] = useState<Q3Row | null>(null);

  // Mock data for demonstration
  const mockData = {
    coverage_code: 'C0001',
    canonical_name: '암진단비',
    insurer_rows: [
      {
        ins_cd: 'N03',
        product_name: '메리츠 무배당 The든든한 암보험',
        slots: {
          diagnosis_benefit_amount: { value: 5000000 }
        }
      },
      {
        ins_cd: 'N05',
        product_name: '삼성화재 무배당 삼성화재 암보험',
        slots: {
          diagnosis_benefit_amount: { value: 3000000 }
        }
      }
    ],
    overall_assessment: [
      '메리츠화재가 가장 높은 보장금액 제공',
      '삼성화재는 낮은 보장금액이지만 보험료가 저렴할 가능성'
    ],
    recommendation: {
      winner: '메리츠화재',
      reasons: [
        '가장 높은 진단비 보장 (500만원)',
        '암 진단 시 높은 보장금액으로 치료비 부담 완화'
      ]
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
            ← 메인으로
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Q3: 종합 비교 리포트
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            담보별 상세 조건 비교 + 종합 판단 + 추천
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Q3ThreePartView
          data={mockData}
          onRowClick={setSelectedRow}
          selectedRow={selectedRow}
        />
      </div>

      {/* Evidence Rail */}
      {selectedRow && (
        <Q3EvidenceRail
          selectedRow={selectedRow}
          coverageCode={mockData.coverage_code}
          canonicalName={mockData.canonical_name}
          onClose={() => setSelectedRow(null)}
        />
      )}
    </div>
  );
}
