/**
 * Q4 Page - 지원 여부 매트릭스
 *
 * Purpose: Coverage support matrix (O/X/-) for specific conditions
 * Status: Evidence Rail integrated
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Q4SupportMatrixView, Q4SelectedCell } from '@/components/chat/Q4SupportMatrixView';
import { Q4EvidenceRail } from '@/components/q4/Q4EvidenceRail';

export default function Q4Page() {
  const [selectedCell, setSelectedCell] = useState<Q4SelectedCell | null>(null);

  // Mock data for demonstration
  const mockData = {
    query_id: 'q4_demo',
    matrix: [
      {
        insurer_key: 'meritz',
        in_situ: {
          status_icon: '✅',
          display: 'O',
          color: 'green',
          coverage_kind: 'diagnosis_benefit',
          evidence_refs: ['meritz_cancer_policy_v1.pdf#page=12']
        },
        borderline: {
          status_icon: '❌',
          display: 'X',
          color: 'red',
          coverage_kind: 'excluded',
          evidence_refs: ['meritz_cancer_policy_v1.pdf#page=15']
        }
      },
      {
        insurer_key: 'samsung',
        in_situ: {
          status_icon: '✅',
          display: 'O',
          color: 'green',
          coverage_kind: 'diagnosis_benefit',
          evidence_refs: ['samsung_cancer_policy_v2.pdf#page=8']
        },
        borderline: {
          status_icon: '✅',
          display: 'O',
          color: 'green',
          coverage_kind: 'diagnosis_benefit',
          evidence_refs: ['samsung_cancer_policy_v2.pdf#page=9']
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
            Q4: 지원 여부 매트릭스
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            특정 질병/조건에 대한 보장 지원 여부
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Q4SupportMatrixView
          data={mockData}
          onCellClick={setSelectedCell}
          selectedCell={selectedCell}
        />
      </div>

      {/* Evidence Rail */}
      {selectedCell && (
        <Q4EvidenceRail
          selectedCell={selectedCell}
          onClose={() => setSelectedCell(null)}
        />
      )}
    </div>
  );
}
