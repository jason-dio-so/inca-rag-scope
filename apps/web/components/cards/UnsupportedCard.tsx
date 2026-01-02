"use client";

interface UnsupportedCardProps {
  type: string;
}

export default function UnsupportedCard({ type }: UnsupportedCardProps) {
  return (
    <div className="border border-yellow-300 bg-yellow-50 rounded-lg p-4">
      <div className="text-yellow-800 font-medium">
        지원되지 않는 뷰 타입: {type}
      </div>
      <div className="text-sm text-yellow-700 mt-2">
        개발자에게 문의하세요.
      </div>
    </div>
  );
}
