"use client";

import { useState, useEffect, useRef } from "react";
import { EvidenceItem, EvidenceStoreItem } from "@/lib/types";
import { batchGetEvidence } from "@/lib/api";

interface EvidenceToggleProps {
  // Legacy mode (backward compatible)
  items?: EvidenceItem[];
  // Slim mode (lazy load)
  evidenceRefs?: string[];
  defaultCollapsed?: boolean;
}

export default function EvidenceToggle({
  items,
  evidenceRefs,
  defaultCollapsed = true,
}: EvidenceToggleProps) {
  const [isOpen, setIsOpen] = useState(!defaultCollapsed);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [loadedItems, setLoadedItems] = useState<EvidenceStoreItem[] | undefined>();

  // Cache to prevent duplicate fetches
  const cacheRef = useRef<Map<string, EvidenceStoreItem>>(new Map());
  const loadedRef = useRef(false);

  // Lazy load when opening for the first time
  useEffect(() => {
    // Skip if:
    // - Using legacy items mode
    // - Already loaded
    // - Not open
    // - No refs to load
    if (items || loadedRef.current || !isOpen || !evidenceRefs || evidenceRefs.length === 0) {
      return;
    }

    const loadEvidence = async () => {
      setLoading(true);
      setError(undefined);

      try {
        const result = await batchGetEvidence(evidenceRefs);

        // Update cache
        Object.entries(result).forEach(([ref, item]) => {
          cacheRef.current.set(ref, item);
        });

        // Convert to array
        const loaded = evidenceRefs
          .map(ref => result[ref])
          .filter(Boolean); // Remove nulls

        setLoadedItems(loaded);
        loadedRef.current = true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "근거를 불러오지 못했습니다");
      } finally {
        setLoading(false);
      }
    };

    loadEvidence();
  }, [isOpen, items, evidenceRefs]);

  // Determine display items (legacy or lazy-loaded)
  const displayItems = items || loadedItems;

  // Convert EvidenceStoreItem to EvidenceItem format for rendering
  const renderItems = displayItems?.map(item => {
    if ('evidence_ref_id' in item) {
      // Legacy EvidenceItem - use as is
      return item as EvidenceItem;
    } else {
      // EvidenceStoreItem - convert to EvidenceItem format
      const storeItem = item as EvidenceStoreItem;
      return {
        evidence_ref_id: storeItem.evidence_ref,
        insurer: storeItem.insurer,
        coverage_name: storeItem.coverage_code,
        doc_type: storeItem.doc_type,
        page: storeItem.page,
        snippet: storeItem.snippet,
      };
    }
  }) || [];

  // Hide if no items and no refs
  if (!items && (!evidenceRefs || evidenceRefs.length === 0)) {
    return null;
  }

  const count = items?.length || evidenceRefs?.length || 0;

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-t-lg"
      >
        <span className="font-medium text-gray-700">
          근거 자료 ({count}개)
        </span>
        <svg
          className={`w-5 h-5 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          {loading && (
            <div className="text-sm text-gray-500 text-center py-4">
              근거 불러오는 중…
            </div>
          )}

          {error && !loading && (
            <div className="text-sm text-red-600 text-center py-4">
              {error}
            </div>
          )}

          {!loading && !error && renderItems.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-4">
              근거 없음
            </div>
          )}

          {!loading && !error && renderItems.length > 0 && renderItems.map((item, idx) => (
            <div
              key={item.evidence_ref_id || idx}
              className="border-l-4 border-blue-300 pl-3 py-2 bg-blue-50 rounded"
            >
              <div className="text-sm font-medium text-gray-700">
                {item.insurer} - {item.coverage_name}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {item.doc_type}
                {item.page && ` p.${item.page}`}
              </div>
              {item.snippet && (
                <div className="text-xs text-gray-500 mt-2 italic">
                  {item.snippet}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
