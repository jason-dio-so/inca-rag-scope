/**
 * Q4 Support Matrix View
 *
 * Displays O/X/— matrix for coverage support status
 * Format: Support items (rows) x Insurers (columns)
 */

export interface Q4CellData {
  status_icon: string;
  display: string;
  color: string;
  coverage_kind?: string;
  evidence_refs?: string[];
}

export interface Q4SelectedCell {
  insurer_key: string;
  insurer_name: string;
  cellType: 'in_situ' | 'borderline';
  cellData: Q4CellData;
}

interface Q4ViewProps {
  data: {
    query_id?: string;
    matrix?: Array<{
      insurer_key: string;
      in_situ: Q4CellData;
      borderline: Q4CellData;
    }>;
    error?: string;
  };
  onCellClick?: (cell: Q4SelectedCell) => void;
  selectedCell?: Q4SelectedCell | null;
}

export function Q4SupportMatrixView({ data, onCellClick, selectedCell }: Q4ViewProps) {
  if (data.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="font-semibold text-red-800">{data.error}</p>
      </div>
    );
  }

  const INSURER_NAMES: Record<string, string> = {
    samsung: '삼성화재',
    meritz: '메리츠화재',
    db: 'DB손해보험',
    kb: 'KB손해보험',
    hanwha: '한화손해보험',
    hyundai: '현대해상',
    lotte: '롯데손해보험',
    heungkuk: '흥국화재',
  };

  const matrix = data.matrix || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h2 className="text-lg font-bold text-gray-900">제자리암/경계성종양 보장 여부 매트릭스</h2>
        <p className="text-sm text-gray-600 mt-1">
          ✅ O = 보장, ❌ X = 제외, — = 정보 없음
        </p>
      </div>

      {/* Matrix Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700 sticky left-0 bg-gray-50">
                  보험사
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-700 min-w-[150px]">
                  제자리암<br />(상피내암)
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-700 min-w-[150px]">
                  경계성종양
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {matrix.map((row, idx) => {
                const insurerName = INSURER_NAMES[row.insurer_key] || row.insurer_key;

                const getColorClass = (color: string) => {
                  switch (color) {
                    case 'green':
                      return 'bg-green-50 text-green-700';
                    case 'red':
                      return 'bg-red-50 text-red-700';
                    case 'orange':
                      return 'bg-orange-50 text-orange-700';
                    case 'gray':
                      return 'bg-gray-50 text-gray-500';
                    default:
                      return 'bg-gray-50 text-gray-700';
                  }
                };

                const isInSituSelected =
                  selectedCell?.insurer_key === row.insurer_key &&
                  selectedCell?.cellType === 'in_situ';
                const isBorderlineSelected =
                  selectedCell?.insurer_key === row.insurer_key &&
                  selectedCell?.cellType === 'borderline';

                const handleInSituClick = () => {
                  onCellClick?.({
                    insurer_key: row.insurer_key,
                    insurer_name: insurerName,
                    cellType: 'in_situ',
                    cellData: row.in_situ
                  });
                };

                const handleBorderlineClick = () => {
                  onCellClick?.({
                    insurer_key: row.insurer_key,
                    insurer_name: insurerName,
                    cellType: 'borderline',
                    cellData: row.borderline
                  });
                };

                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900 font-medium sticky left-0 bg-white">
                      {insurerName}
                    </td>
                    <td
                      className={`px-4 py-3 text-center cursor-pointer transition-all ${
                        isInSituSelected ? 'bg-blue-50 ring-2 ring-blue-500 ring-inset' : ''
                      }`}
                      onClick={handleInSituClick}
                    >
                      <div
                        className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-medium ${getColorClass(
                          row.in_situ.color
                        )}`}
                      >
                        {row.in_situ.status_icon === '✅' && 'O'}
                        {row.in_situ.status_icon === '❌' && 'X'}
                        {row.in_situ.status_icon === '—' && '—'}
                        {row.in_situ.status_icon === '⚠️' && '⚠️'}
                      </div>
                      {row.in_situ.coverage_kind === 'treatment_trigger' && (
                        <div className="text-xs text-orange-600 mt-1">진단비 아님</div>
                      )}
                    </td>
                    <td
                      className={`px-4 py-3 text-center cursor-pointer transition-all ${
                        isBorderlineSelected ? 'bg-blue-50 ring-2 ring-blue-500 ring-inset' : ''
                      }`}
                      onClick={handleBorderlineClick}
                    >
                      <div
                        className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-medium ${getColorClass(
                          row.borderline.color
                        )}`}
                      >
                        {row.borderline.status_icon === '✅' && 'O'}
                        {row.borderline.status_icon === '❌' && 'X'}
                        {row.borderline.status_icon === '—' && '—'}
                        {row.borderline.status_icon === '⚠️' && '⚠️'}
                      </div>
                      {row.borderline.coverage_kind === 'treatment_trigger' && (
                        <div className="text-xs text-orange-600 mt-1">진단비 아님</div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm font-semibold text-gray-900 mb-2">범례</p>
        <ul className="text-xs text-gray-700 space-y-1">
          <li>• <strong>✅ O</strong>: 진단비로 보장 (사용 가능)</li>
          <li>• <strong>❌ X</strong>: 명시적으로 제외됨</li>
          <li>• <strong>⚠️</strong>: 진단비 아님 (치료비 트리거로만 언급)</li>
          <li>• <strong>—</strong>: 정보 없음 (약관에서 확인되지 않음)</li>
        </ul>
      </div>

      {/* Note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-xs text-gray-600">
          <strong>안내:</strong> 모든 판정은 약관을 기반으로 합니다.
          최종 가입 전에는 반드시 약관을 직접 확인하시기 바랍니다.
        </p>
      </div>
    </div>
  );
}
