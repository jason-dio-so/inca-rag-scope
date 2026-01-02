"use client";

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
  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-bold text-lg text-gray-800">보험 상품 비교</h2>
        <p className="text-xs text-gray-600 mt-1">카테고리를 선택하세요</p>
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
    </div>
  );
}
