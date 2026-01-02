"use client";

import { useState } from "react";
import { NormalizedTable } from "@/lib/normalize/table";
import { ProposalDetailStoreItem } from "@/lib/types";
import { getProposalDetail } from "@/lib/api";
import EvidenceToggle from "./EvidenceToggle";

interface TwoInsurerCompareCardProps {
  section: NormalizedTable;
}

export default function TwoInsurerCompareCard({
  section,
}: TwoInsurerCompareCardProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState<string | undefined>();
  const [modalDetail, setModalDetail] = useState<ProposalDetailStoreItem | undefined>();

  const handleViewDetail = async (ref: string) => {
    setModalOpen(true);
    setModalLoading(true);
    setModalError(undefined);
    setModalDetail(undefined);

    try {
      const detail = await getProposalDetail(ref);
      if (detail) {
        setModalDetail(detail);
      } else {
        setModalError("보장내용을 찾을 수 없습니다");
      }
    } catch (err) {
      setModalError(err instanceof Error ? err.message : "보장내용을 불러오지 못했습니다");
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalDetail(undefined);
    setModalError(undefined);
  };

  return (
    <>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-purple-50 px-4 py-2 border-b border-purple-200">
          <h3 className="font-medium text-purple-800">{section.title}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-purple-100">
              <tr>
                {section.columns.map((col, idx) => (
                  <th
                    key={idx}
                    className="px-4 py-2 text-left text-sm font-medium text-purple-700"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {section.rows.map((row, idx) => (
                <>
                  <tr key={idx} className="border-t border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-700 bg-gray-50">
                      <div className="flex items-center justify-between gap-2">
                        <span>{row.label}</span>
                        {row.meta?.proposal_detail_ref && (
                          <button
                            onClick={() => handleViewDetail(row.meta!.proposal_detail_ref!)}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline whitespace-nowrap"
                          >
                            보장내용 보기
                          </button>
                        )}
                      </div>
                    </td>
                    {row.values.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-2">
                        {cell}
                      </td>
                    ))}
                  </tr>
                  {/* Evidence toggle row (if evidence_refs exist) */}
                  {row.meta?.evidence_refs && row.meta.evidence_refs.length > 0 && (
                    <tr key={`${idx}-evidence`}>
                      <td colSpan={section.columns.length} className="px-4 py-2 bg-gray-50">
                        <EvidenceToggle evidenceRefs={row.meta.evidence_refs} defaultCollapsed={true} />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Proposal Detail Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={closeModal}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-purple-50 px-6 py-4 border-b border-purple-200 flex items-center justify-between">
              <h3 className="font-medium text-purple-800">보장내용 상세</h3>
              <button
                onClick={closeModal}
                className="text-gray-600 hover:text-gray-800"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {modalLoading && (
                <div className="text-center py-8 text-gray-500">
                  불러오는 중…
                </div>
              )}

              {modalError && !modalLoading && (
                <div className="text-center py-8 text-red-600">
                  {modalError}
                </div>
              )}

              {modalDetail && !modalLoading && (
                <div className="space-y-4">
                  {/* Metadata */}
                  <div className="text-sm text-gray-600 space-y-1">
                    <div><strong>보험사:</strong> {modalDetail.insurer}</div>
                    <div><strong>담보코드:</strong> {modalDetail.coverage_code}</div>
                    <div><strong>문서:</strong> {modalDetail.doc_type} (p.{modalDetail.page})</div>
                    {modalDetail.hash && (
                      <div className="text-xs text-gray-400">
                        <strong>Hash:</strong> {modalDetail.hash.substring(0, 16)}...
                      </div>
                    )}
                  </div>

                  {/* Benefit text */}
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-700 mb-2">보장 설명:</h4>
                    <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">
                      {modalDetail.benefit_description_text}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-3 border-t flex justify-end">
              <button
                onClick={closeModal}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm font-medium"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
