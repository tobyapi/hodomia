import { expect, test } from "vitest";
import { beatGrid, replaceRow, validRow } from "./editing";

test("beat grid preserves anchor and bar boundaries", () => {
  const rows = beatGrid(120, 1, 4, 3);
  expect(rows.map(r => r.start)).toEqual([1, 1.5, 2, 2.5, 3, 3.5]);
  expect(rows.filter(r => r.label === "1").map(r => r.start)).toEqual([1, 2.5]);
  expect(() => beatGrid(0, 0, 10, 4)).toThrow();
});
test("unknown lyric timing stays null and invalid ranges are rejected", () => {
  expect(validRow({ id: "a", label: "歌", start: null, end: null }, "lyrics", 60)).toBeNull();
  expect(validRow({ id: "a", label: "歌", start: 4, end: 2 }, "lyrics", 60)).toBeTruthy();
  expect(validRow({ id: "a", label: "歌", start: NaN, end: 5 }, "lyrics", 60)).toBeTruthy();
});
test("editing uses copied tracks and does not overwrite automatic data", () => {
  const auto = { lyrics: [{ id: "a", label: "候補", start: 1, end: 2 }] };
  const edits = replaceRow({}, auto, "lyrics", { ...auto.lyrics[0], label: "修正" });
  expect(auto.lyrics[0].label).toBe("候補");
  expect(edits.lyrics?.[0].label).toBe("修正");
});
