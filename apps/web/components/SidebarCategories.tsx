"use client";

import { useState } from "react";
import { Category } from "@/lib/types";

interface SidebarCategoriesProps {
  categories: Category[];
  selectedCategory?: string;
  onSelectCategory: (categoryId: string) => void;
}

export default function SidebarCategories({
  categories,
  selectedCategory,
  onSelectCategory,
}: SidebarCategoriesProps) {
  // STEP NEXT-97: Start collapsed in demo mode (minimize category/explore mode by default)
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={`bg-gray-50 border-r border-gray-200 h-full overflow-y-auto transition-all duration-300 ${
        isExpanded ? "w-64" : "w-12"
      }`}
    >
      {/* STEP NEXT-97: Toggle button */}
      <div className="p-2 border-b border-gray-200 flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center p-2 hover:bg-gray-100 rounded transition-colors"
          title={isExpanded ? "카테고리 숨기기" : "카테고리 보기"}
        >
          {isExpanded ? (
            <svg
              className="w-5 h-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          ) : (
            <svg
              className="w-5 h-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          )}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-bold text-lg text-gray-800">지식 탐색</h2>
            <p className="text-xs text-gray-600 mt-1">카테고리 선택 (선택사항)</p>
          </div>

          <div className="p-2 space-y-1">
            {categories.map((category) => (
              <div key={category.id}>
                <button
                  onClick={() => onSelectCategory(category.id)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    selectedCategory === category.id
                      ? "bg-blue-100 text-blue-800 font-medium"
                      : "text-gray-700 hover:bg-gray-100"
                  } ${category.status === "준비중" ? "opacity-50" : ""}`}
                  disabled={category.status === "준비중"}
                >
                  <div className="text-sm font-medium">{category.label}</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {category.description}
                  </div>
                </button>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-gray-200 mt-4">
            <div className="text-xs text-gray-500">
              <p className="font-medium mb-1">사용 가능 보험사 (8개)</p>
              <p>삼성, 메리츠, DB, KB, 한화, 현대, 롯데, 흥국</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
