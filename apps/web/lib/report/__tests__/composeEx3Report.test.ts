/**
 * STEP NEXT-132: Contract Tests for EX3 Report Composer
 *
 * PURPOSE:
 * - Verify composeEx3Report() deterministic logic
 * - Ensure EX3 SSOT (NO EX4/EX2 mixing)
 * - Test all documented scenarios
 *
 * TEST COUNT: 6 minimum (per spec)
 */

import { composeEx3Report } from '../composeEx3Report';
import { AssistantMessageVM } from '../../types';

describe('composeEx3Report', () => {
  /**
   * Test 1: NO EX3_COMPARE messages → returns null
   */
  test('returns null when no EX3_COMPARE messages exist', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX2_DETAIL',
        title: 'EX2 Title',
        sections: [],
      },
      {
        kind: 'EX4_ELIGIBILITY',
        title: 'EX4 Title',
        sections: [],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).toBeNull();
  });

  /**
   * Test 2: Latest EX3_COMPARE selected (not first)
   */
  test('selects latest EX3_COMPARE message', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX3_COMPARE',
        title: '암진단비(유사암제외)',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암진단비(유사암제외) 비교',
            columns: ['비교 항목', '삼성화재', '메리츠화재'],
            rows: [
              {
                cells: [
                  { text: '보장 정의 기준' },
                  { text: '지급 한도/횟수 기준' },
                  { text: '보장금액(정액) 기준' },
                ],
              },
            ],
          },
        ],
      },
      {
        kind: 'EX4_ELIGIBILITY',
        title: 'EX4 Middle',
        sections: [],
      },
      {
        kind: 'EX3_COMPARE',
        title: '암수술비',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암수술비 비교',
            columns: ['비교 항목', '삼성화재', '메리츠화재'],
            rows: [
              {
                cells: [
                  { text: '보장 정의 기준' },
                  { text: '지급 한도/횟수 기준' },
                  { text: '보장금액(정액) 기준' },
                ],
              },
            ],
          },
        ],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).not.toBeNull();
    expect(report?.title).toBe('암수술비 비교 요약');
  });

  /**
   * Test 3: Summary lines composition (3 lines max)
   * Line 1: Fixed template
   * Line 2: "보장 정의 기준" row (if exists)
   * Line 3: "핵심 보장 내용" row (if exists)
   */
  test('builds summary_lines correctly (max 3 lines)', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX3_COMPARE',
        title: '암진단비(유사암제외)',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암진단비(유사암제외) 비교',
            columns: ['비교 항목', '삼성화재', '메리츠화재'],
            rows: [
              {
                cells: [
                  { text: '보장 정의 기준' },
                  { text: '지급 한도/횟수 기준' },
                  { text: '보장금액(정액) 기준' },
                ],
              },
              {
                cells: [
                  { text: '핵심 보장 내용' },
                  { text: '보험기간 중 1회' },
                  { text: '3천만원' },
                ],
              },
            ],
          },
        ],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).not.toBeNull();
    expect(report?.summary_lines).toHaveLength(3);

    // Line 1: Fixed template
    expect(report?.summary_lines[0]).toContain('삼성화재와 메리츠화재');
    expect(report?.summary_lines[0]).toContain('암진단비(유사암제외)');
    expect(report?.summary_lines[0]).toContain('보장 정의 기준 차이');

    // Line 2: "보장 정의 기준" row
    expect(report?.summary_lines[1]).toBe(
      '삼성화재: 지급 한도/횟수 기준 / 메리츠화재: 보장금액(정액) 기준'
    );

    // Line 3: "핵심 보장 내용" row
    expect(report?.summary_lines[2]).toBe(
      '삼성화재: 보험기간 중 1회 / 메리츠화재: 3천만원'
    );
  });

  /**
   * Test 4: Summary lines omit missing rows (no blank lines)
   */
  test('omits missing rows in summary_lines (no blank lines)', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX3_COMPARE',
        title: '암진단비(유사암제외)',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암진단비(유사암제외) 비교',
            columns: ['비교 항목', '삼성화재', '메리츠화재'],
            rows: [
              {
                cells: [
                  { text: '보장 정의 기준' },
                  { text: '지급 한도/횟수 기준' },
                  { text: '보장금액(정액) 기준' },
                ],
              },
              // NO "핵심 보장 내용" row
            ],
          },
        ],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).not.toBeNull();
    expect(report?.summary_lines).toHaveLength(2); // Line 1 + Line 2 only

    expect(report?.summary_lines[0]).toContain('보장 정의 기준 차이');
    expect(report?.summary_lines[1]).toContain('지급 한도/횟수 기준');
  });

  /**
   * Test 5: Notes copied from common_notes section
   */
  test('copies notes from common_notes section', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX3_COMPARE',
        title: '암진단비(유사암제외)',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암진단비(유사암제외) 비교',
            columns: ['비교 항목', '삼성화재', '메리츠화재'],
            rows: [],
          },
          {
            kind: 'common_notes',
            title: '유의사항',
            bullets: [
              '가입설계서 기준입니다',
              '실제 보장 여부는 약관을 확인하세요',
            ],
          },
        ],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).not.toBeNull();
    expect(report?.notes).toHaveLength(2);
    expect(report?.notes[0]).toBe('가입설계서 기준입니다');
    expect(report?.notes[1]).toBe('실제 보장 여부는 약관을 확인하세요');
  });

  /**
   * Test 6: Insurer names extracted from table columns
   */
  test('extracts insurer names from table columns', () => {
    const messages: AssistantMessageVM[] = [
      {
        kind: 'EX3_COMPARE',
        title: '암진단비(유사암제외)',
        sections: [
          {
            kind: 'comparison_table',
            table_kind: 'INTEGRATED_COMPARE',
            title: '암진단비(유사암제외) 비교',
            columns: ['비교 항목', 'KB손해보험', '한화손해보험'],
            rows: [
              {
                cells: [
                  { text: '보장 정의 기준' },
                  { text: 'A' },
                  { text: 'B' },
                ],
              },
            ],
          },
        ],
      },
    ];

    const report = composeEx3Report(messages);

    expect(report).not.toBeNull();
    expect(report?.subtitle[0]).toBe('KB손해보험 vs 한화손해보험');
    expect(report?.summary_lines[0]).toContain('KB손해보험와 한화손해보험');
  });
});
