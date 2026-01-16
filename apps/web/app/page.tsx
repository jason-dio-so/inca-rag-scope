/**
 * Root Launcher - Customer Entry Point
 *
 * Purpose: Report selection screen only (no data loading)
 * Routes:
 * - /demo-q12: Q12 Cancer Diagnosis Comparison Report
 * - /q13: Q13 In-Situ / Borderline Tumor Coverage Matrix
 * - /q14: Q14 Premium Ranking (Top 4)
 * - /q11: Q11 Cancer Hospitalization Coverage Limit Comparison
 */

'use client';

import Link from 'next/link';

export default function LauncherPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900 text-center">
            보험 상품 비교 리포트
          </h1>
          <p className="text-sm text-gray-600 text-center mt-3">
            아래에서 원하는 리포트를 선택해 주세요. (모든 내용은 약관 근거 기반이며, 근거가 없으면 "정보 없음"으로 표시됩니다.)
          </p>
        </div>
      </div>

      {/* Report Cards */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">

          {/* Q12 Card */}
          <Link href="/demo-q12">
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 hover:shadow-xl hover:border-blue-400 transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-blue-100 text-blue-600 text-xs font-bold px-3 py-1 rounded-full">
                  Q12
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-3">
                암진단비 비교 리포트
              </h2>

              <p className="text-sm text-gray-600 mb-4">
                보험료·보장 조건·종합 판단 및 추천 포함
              </p>

              <div className="border-t border-gray-100 pt-4">
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• 보험료 (월/총) 비교</li>
                  <li>• 보장 개시일 (면책/감액) 비교</li>
                  <li>• 종합 판단 및 최종 추천</li>
                </ul>
              </div>
            </div>
          </Link>

          {/* Q13 Card */}
          <Link href="/q13">
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 hover:shadow-xl hover:border-purple-400 transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-purple-100 text-purple-600 text-xs font-bold px-3 py-1 rounded-full">
                  Q13
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-purple-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-3">
                제자리암/경계성종양 보장 여부 매트릭스
              </h2>

              <p className="text-sm text-gray-600 mb-4">
                제자리암/경계성종양 보장 여부 O / X / – 비교
              </p>

              <div className="border-t border-gray-100 pt-4">
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• 제자리암 보장 여부 (O/X/-)</li>
                  <li>• 경계성종양 보장 여부 (O/X/-)</li>
                  <li>• 약관 근거 출처 표시</li>
                </ul>
              </div>
            </div>
          </Link>

          {/* Q14 Card */}
          <Link href="/q14">
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 hover:shadow-xl hover:border-green-400 transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-green-100 text-green-600 text-xs font-bold px-3 py-1 rounded-full">
                  Q14
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-green-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-3">
                보험료 비교 랭킹
              </h2>

              <p className="text-sm text-gray-600 mb-4">
                월납보험료 기준 Top 4 랭킹
              </p>

              <div className="border-t border-gray-100 pt-4">
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• 월납보험료 낮은 순서</li>
                  <li>• Top 4 상품 비교</li>
                  <li>• 총납입보험료 함께 표시</li>
                </ul>
              </div>
            </div>
          </Link>

          {/* Q11 Card */}
          <Link href="/q11">
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 hover:shadow-xl hover:border-orange-400 transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-orange-100 text-orange-600 text-xs font-bold px-3 py-1 rounded-full">
                  Q11
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-orange-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-3">
                암직접입원비 보장한도 비교
              </h2>

              <p className="text-sm text-gray-600 mb-4">
                보장한도 차이 확인
              </p>

              <div className="border-t border-gray-100 pt-4">
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• 보장한도 차이 식별</li>
                  <li>• 담보명 및 보장일수</li>
                  <li>• 보험사별 비교 표시</li>
                </ul>
              </div>
            </div>
          </Link>

        </div>
      </div>

      {/* Footer */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-xs text-blue-800">
            <strong>안내:</strong> 모든 비교 내용은 약관 및 상품 설명서를 기반으로 하며,
            근거가 명확하지 않은 경우 "정보 없음"으로 표시됩니다.
            최종 가입 전에는 반드시 상품 설명서와 약관을 직접 확인하시기 바랍니다.
          </p>
        </div>
      </div>
    </div>
  );
}
