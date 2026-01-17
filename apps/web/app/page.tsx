/**
 * Root Page - Customer Hub Entry Point
 *
 * Purpose: Main entry point showing Q1~Q4 navigation cards
 * Rules:
 * - NO legacy UI imports
 * - NO chat UI imports
 * - NO demo-q12 imports
 * - Clean customer hub ONLY
 */

import { CustomerHub } from '@/components/customer_hub/CustomerHub';

export default function HomePage() {
  return <CustomerHub />;
}
