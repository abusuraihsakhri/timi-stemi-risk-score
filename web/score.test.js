import test from "node:test";
import assert from "node:assert/strict";
import { calculateTimi, mortalityByScore } from "./score.js";

const baseline = {
  age: 64, diabetes_hypertension_angina: false, systolic_bp: 100,
  heart_rate: 100, killip_class: 1, weight_kg: 67,
  anterior_st_elevation_or_lbbb: false, time_to_treatment_hours: 4,
};
test("exact boundaries are not counted", () => {
  const result = calculateTimi(baseline);
  assert.equal(result.score, 0);
  assert.equal(result.mortality_30_day_percent, 0.8);
});
test("all eight predictors contribute correctly", () => {
  const result = calculateTimi({
    ...baseline, age: 75, diabetes_hypertension_angina: true,
    systolic_bp: 99, heart_rate: 101, killip_class: 4,
    weight_kg: 66.9, anterior_st_elevation_or_lbbb: true,
    time_to_treatment_hours: 4.01,
  });
  assert.equal(result.score, 14);
  assert.equal(result.mortality_30_day_percent, 35.9);
});
test("age bands 65–74 and 75+ are exclusive", () => {
  assert.equal(calculateTimi({ ...baseline, age: 65 }).score, 2);
  assert.equal(calculateTimi({ ...baseline, age: 74 }).score, 2);
  assert.equal(calculateTimi({ ...baseline, age: 75 }).score, 3);
});
test("original mortality lookup covers scores 0–14", () => {
  assert.equal(mortalityByScore.length, 10);
  assert.equal(calculateTimi({ ...baseline, systolic_bp: 99 }).mortality_30_day_percent, 4.4);
  assert.equal(calculateTimi({ ...baseline, systolic_bp: 99, killip_class: 2 }).mortality_30_day_percent, 12.4);
});
test("missing and malformed inputs are rejected", () => {
  for (const changes of [{ age: NaN }, { age: 64.5 }, { weight_kg: 0 },
    { killip_class: 5 }, { heart_rate: Infinity }, { diabetes_hypertension_angina: undefined }]) {
    assert.throws(() => calculateTimi({ ...baseline, ...changes }));
  }
});
