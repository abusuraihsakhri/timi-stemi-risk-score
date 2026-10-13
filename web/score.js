/* Original presentation-time TIMI STEMI risk score. Morrow et al. Circulation 2000. */
export const mortalityByScore = [0.8, 1.6, 2.2, 4.4, 7.3, 12.4, 16.1, 23.4, 26.8, 35.9];

function numeric(name, value, lower, upper, integer = false) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < lower || value > upper ||
      (integer && !Number.isInteger(value))) {
    throw new Error(name + " must be " + (integer ? "an integer" : "a finite number") +
      " between " + lower + " and " + upper + ".");
  }
  return value;
}

export function calculateTimi(inputs) {
  if (!inputs || typeof inputs !== "object") throw new Error("Clinical inputs are required.");
  const age = numeric("Age", inputs.age, 0, 120, true);
  const sbp = numeric("Systolic blood pressure", inputs.systolic_bp, 1, 400);
  const hr = numeric("Heart rate", inputs.heart_rate, 1, 350);
  const killip = numeric("Killip class", inputs.killip_class, 1, 4, true);
  const weight = numeric("Weight", inputs.weight_kg, 1, 500);
  const hours = numeric("Time to treatment", inputs.time_to_treatment_hours, 0, 1000);
  if (typeof inputs.diabetes_hypertension_angina !== "boolean" ||
      typeof inputs.anterior_st_elevation_or_lbbb !== "boolean") {
    throw new Error("Both yes/no clinical findings must be specified.");
  }
  const points = {
    age: age >= 75 ? 3 : age >= 65 ? 2 : 0,
    diabetes_hypertension_angina: Number(inputs.diabetes_hypertension_angina),
    systolic_bp: sbp < 100 ? 3 : 0,
    heart_rate: hr > 100 ? 2 : 0,
    killip_class: killip >= 2 ? 2 : 0,
    weight_kg: weight < 67 ? 1 : 0,
    anterior_st_elevation_or_lbbb: Number(inputs.anterior_st_elevation_or_lbbb),
    time_to_treatment_hours: hours > 4 ? 1 : 0,
  };
  const score = Object.values(points).reduce((sum, value) => sum + value, 0);
  return { score, score_max: 14, mortality_30_day_percent: mortalityByScore[Math.min(score, 9)], points };
}
