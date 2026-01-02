/**
 * STEP NEXT-UI-02-FIX2: Value Renderer Tests
 *
 * Minimal test cases to verify renderCellValue handles various data structures.
 * Run manually or integrate with existing test infrastructure.
 */

import { renderCellValue } from "../lib/renderers/valueRenderer";

// Manual test runner (for environments without Jest/Vitest)
function test(description: string, fn: () => void) {
  try {
    fn();
    console.log(`✓ ${description}`);
  } catch (error) {
    console.error(`✗ ${description}`);
    console.error(error);
  }
}

function assertEquals(actual: any, expected: any, message?: string) {
  if (actual !== expected) {
    throw new Error(
      `${message || "Assertion failed"}: expected "${expected}", got "${actual}"`
    );
  }
}

function assertIncludes(actual: string, substring: string, message?: string) {
  if (!actual.includes(substring)) {
    throw new Error(
      `${message || "Assertion failed"}: expected "${actual}" to include "${substring}"`
    );
  }
}

// Test Cases

test("renders null/undefined as '-'", () => {
  assertEquals(renderCellValue(null), "-");
  assertEquals(renderCellValue(undefined), "-");
  assertEquals(renderCellValue(""), "-");
});

test("renders primitives as strings", () => {
  assertEquals(renderCellValue("test"), "test");
  assertEquals(renderCellValue(123), "123");
  assertEquals(renderCellValue(true), "true");
});

test("renders amount with KRW unit (만원/억원)", () => {
  const result = renderCellValue({ amount: 30000000, unit: "KRW" });
  // Should be "3,000만원" or similar Korean format
  assertIncludes(result, "만원", "Should format large KRW amounts");
});

test("renders amount with percentage", () => {
  const result = renderCellValue({ amount: 50, unit: "%" });
  assertEquals(result, "50%");
});

test("renders object with text field", () => {
  assertEquals(renderCellValue({ text: "Hello" }), "Hello");
});

test("renders object with label field", () => {
  assertEquals(renderCellValue({ label: "Label" }), "Label");
});

test("renders object with value field", () => {
  assertEquals(renderCellValue({ value: "Value" }), "Value");
});

test("renders value_text (TableCell pattern)", () => {
  assertEquals(renderCellValue({ value_text: "Cell Text" }), "Cell Text");
});

test("renders payment_type", () => {
  assertEquals(renderCellValue({ payment_type: "lump_sum" }), "정액(진단금)");
  assertEquals(renderCellValue({ payment_type: "per_day" }), "일당");
});

test("renders array by joining with comma", () => {
  assertEquals(renderCellValue(["A", "B", "C"]), "A, B, C");
  assertEquals(
    renderCellValue(["A", { text: "B" }, "C"]),
    "A, B, C",
    "Should recursively render array items"
  );
});

test("renders unknown objects as JSON string", () => {
  const result = renderCellValue({ foo: "bar", baz: 123 });
  assertIncludes(result, "foo", "Should include JSON representation");
  assertIncludes(result, "bar");
});

test("truncates long JSON strings", () => {
  const longObject = {
    field1: "a".repeat(50),
    field2: "b".repeat(50),
    field3: "c".repeat(50),
  };
  const result = renderCellValue(longObject);
  assertIncludes(result, "...", "Should truncate long JSON");
  assertEquals(result.length <= 120, true, "Should be under 120 chars");
});

// Run all tests
console.log("\n=== Value Renderer Test Results ===\n");

export { test, assertEquals, assertIncludes };
