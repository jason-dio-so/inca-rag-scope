/**
 * Q12 Report View - Customer-Facing Report
 *
 * Purpose: Display Q12 report in 3-block structure:
 *   1. Comparison table (insurers as columns, items as rows)
 *   2. Summary (pros/cons bullets with evidence)
 *   3. Recommendation (rule-based, deterministic)
 *
 * Rules (HARD):
 * - Facts from q12_report only (DB SSOT)
 * - NO arbitrary text generation
 * - Missing data → "약관에서 근거를 찾지 못했습니다(정보 없음)"
 * - All values must trace to evidence
 */

'use client';

interface EvidenceRef {
  doc_type: string;
  page_range: string;
  excerpt: string;
}

interface ItemValue {
  value: string | string[];
  evidence_ref?: EvidenceRef;
}

interface InsurerReport {
  ins_cd: string;
  insurer_name_ko: string;
  monthly_premium: number | null;
  total_premium: number | null;
  items: Record<string, ItemValue>;
}

interface ProsCons {
  ins_cd: string;
  insurer_name_ko: string;
  pros: string[];
  cons: string[];
  evidence_refs: EvidenceRef[];
}

interface Recommendation {
  winner_ins_cd: string | null;
  reason_bullets: string[];
  rule_trace: {
    rules_fired: string[];
    inputs_used: string[];
  };
}

interface Q12Report {
  title: string;
  scenario: {
    age: number;
    sex: string;
    pay_term_years: number;
    ins_term_years: number;
    as_of_date: string;
    note: string;
  };
  insurers: InsurerReport[];
  summary: {
    pros_cons: ProsCons[];
    recommendation: Recommendation;
  };
}

interface Q12ReportViewProps {
  report: Q12Report;
}

export function Q12ReportView({ report }: Q12ReportViewProps) {
  if (!report || !report.insurers || report.insurers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-500">Q12 리포트 데이터가 없습니다.</p>
      </div>
    );
  }

  const allItemKeys = Array.from(
    new Set(
      report.insurers.flatMap(ins => Object.keys(ins.items))
    )
  );

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-blue-50 border-b border-blue-100 p-4">
        <h2 className="text-xl font-bold text-gray-900 mb-1">
          {report.title}
        </h2>
        <p className="text-xs text-gray-600">
          {report.scenario.note}
        </p>
      </div>

      {/* Block 1: Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-300">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 w-[20%]">
                항목
              </th>
              {report.insurers.map((insurer) => (
                <th key={insurer.ins_cd} className="px-4 py-3 text-center text-sm font-bold text-gray-700">
                  {insurer.insurer_name_ko}
                  <div className="text-xs font-normal text-gray-500">{insurer.ins_cd}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {/* Row: 월보험료 */}
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-semibold text-gray-700">
                월보험료
              </td>
              {report.insurers.map((insurer) => (
                <td key={insurer.ins_cd} className="px-4 py-3 text-center">
                  {insurer.monthly_premium ? (
                    <div className="text-base font-bold text-gray-900">
                      {insurer.monthly_premium.toLocaleString()}원
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400">약관에서 근거를 찾지 못했습니다(정보 없음)</div>
                  )}
                </td>
              ))}
            </tr>

            {/* Row: 총납입보험료 */}
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-semibold text-gray-700">
                총납입보험료
              </td>
              {report.insurers.map((insurer) => (
                <td key={insurer.ins_cd} className="px-4 py-3 text-center">
                  {insurer.total_premium ? (
                    <div>
                      <div className="text-base font-bold text-gray-900">
                        {insurer.total_premium.toLocaleString()}원
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {report.scenario.pay_term_years}년 납입 기준
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400">약관에서 근거를 찾지 못했습니다(정보 없음)</div>
                  )}
                </td>
              ))}
            </tr>

            {/* Dynamic rows from items */}
            {allItemKeys.map((itemKey) => (
              <tr key={itemKey} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-semibold text-gray-700">
                  {itemKey}
                </td>
                {report.insurers.map((insurer) => {
                  const item = insurer.items[itemKey];
                  if (!item) {
                    return (
                      <td key={insurer.ins_cd} className="px-4 py-3 text-center">
                        <div className="text-sm text-gray-400">약관에서 근거를 찾지 못했습니다(정보 없음)</div>
                      </td>
                    );
                  }

                  const value = item.value;

                  return (
                    <td key={insurer.ins_cd} className="px-4 py-3 text-sm">
                      <div className="text-gray-800">
                        {Array.isArray(value) ? (
                          <ul className="list-disc list-inside">
                            {value.map((v, idx) => (
                              <li key={idx}>{v}</li>
                            ))}
                          </ul>
                        ) : (
                          <div>{value}</div>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Block 2: Summary (Pros/Cons) */}
      <div className="border-t-2 border-gray-300 bg-gray-50 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          📊 종합 판단
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {report.summary.pros_cons.map((pc) => (
            <div key={pc.ins_cd} className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="font-bold text-gray-900 mb-2">
                {pc.insurer_name_ko} ({pc.ins_cd})
              </h4>

              <div className="mb-3">
                <div className="text-sm font-semibold text-green-700 mb-1">✅ 장점</div>
                <ul className="text-sm text-gray-700 space-y-1">
                  {pc.pros.map((pro, idx) => (
                    <li key={idx}>• {pro}</li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="text-sm font-semibold text-red-700 mb-1">⚠️ 단점</div>
                <ul className="text-sm text-gray-700 space-y-1">
                  {pc.cons.map((con, idx) => (
                    <li key={idx}>• {con}</li>
                  ))}
                </ul>
              </div>

              {pc.evidence_refs.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    근거: {pc.evidence_refs.length}개 문서
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Block 3: Recommendation */}
      <div className="border-t-2 border-gray-300 bg-blue-50 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          🎯 최종 추천
        </h3>

        {report.summary.recommendation.winner_ins_cd ? (
          <div className="bg-white rounded-lg border-2 border-blue-400 p-4">
            {report.summary.recommendation.reason_bullets.map((bullet, idx) => (
              <div key={idx} className={`${idx === 0 ? 'text-lg font-bold text-blue-700 mb-2' : 'text-sm text-gray-700 ml-4'}`}>
                {bullet}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-300 p-4">
            <div className="text-base font-semibold text-gray-700">
              판단 보류 (정보 부족)
            </div>
            <div className="text-sm text-gray-600 mt-2">
              {report.summary.recommendation.reason_bullets.join(', ')}
            </div>
          </div>
        )}

        {/* Rule trace (debug info) */}
        <details className="mt-4">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
            규칙 적용 내역 (디버그)
          </summary>
          <div className="mt-2 p-3 bg-gray-100 rounded text-xs text-gray-700">
            <div className="font-semibold mb-1">Rules Fired:</div>
            <ul className="list-disc list-inside mb-2">
              {report.summary.recommendation.rule_trace.rules_fired.map((rule, idx) => (
                <li key={idx}>{rule}</li>
              ))}
            </ul>
            <div className="font-semibold mb-1">Inputs Used:</div>
            <div>{report.summary.recommendation.rule_trace.inputs_used.join(', ')}</div>
          </div>
        </details>
      </div>

      {/* Footer */}
      <div className="bg-gray-100 border-t border-gray-200 p-4">
        <p className="text-xs text-gray-600">
          본 리포트는 약관 근거 기반으로 정리되며, 근거 미확인 항목은 "정보 없음"으로 표기됩니다.
        </p>
        <p className="text-xs text-gray-600 mt-1">
          보험료: premium_raw JSON (2025-11-26)
        </p>
        <p className="text-xs text-gray-500 mt-1">
          기준일: {report.scenario.as_of_date}
        </p>
      </div>
    </div>
  );
}
