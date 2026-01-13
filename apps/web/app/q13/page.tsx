import { Q13SubtypeCoverageCard } from '@/components/cards/Q13SubtypeCoverageCard';

export default function Q13Page() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Q13: 제자리암/경계성종양 보장 비교 (LIMITED MODE)
        </h1>
        <Q13SubtypeCoverageCard />
      </div>
    </div>
  );
}
