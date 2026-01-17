/**
 * Q2 Page - 보장한도 차이 비교
 *
 * Purpose: Compare coverage limit differences across insurers
 * Status: Evidence Rail integrated
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Q2LimitDiffView, Q2Row } from '@/components/chat/Q2LimitDiffView';
import { Q2EvidenceRail } from '@/components/q2/Q2EvidenceRail';

export default function Q2Page() {
  const [selectedRow, setSelectedRow] = useState<Q2Row | null>(null);

  // Mock data for demonstration
  const mockData = {
    coverage_code: 'C0001',
    canonical_name: '암진단비',
    insurer_rows: [
      {
        ins_cd: 'N03',
        product_name: '메리츠 무배당 The든든한 암보험',
        slots: {
          duration_limit_days: { value: 180 },
          daily_benefit_amount_won: { value: 50000 }
        }
      }
    ]
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
            Q2: 보장한도 차이 비교
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            특정 담보의 보장한도 차이 확인
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Q2LimitDiffView
          data={mockData}
          onRowClick={setSelectedRow}
          selectedRow={selectedRow}
        />
      </div>

      {/* Evidence Rail */}
      {selectedRow && (
        <Q2EvidenceRail
          selectedRow={selectedRow}
          coverageCode={mockData.coverage_code}
          canonicalName={mockData.canonical_name}
          onClose={() => setSelectedRow(null)}
        />
      )}
    </div>
  );
}
