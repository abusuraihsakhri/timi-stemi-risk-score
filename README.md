# TIMI Risk Score for STEMI

A reproducible implementation of the **original TIMI STEMI presentation-time score**. It calculates 0–14 points from eight clinical predictors and displays the 30-day **all-cause mortality observed in the original InTIME II derivation cohort**.

> **Clinical limitation:** This is a historical population-level prognostic estimate, not a treatment threshold, diagnostic test, or individually calibrated mortality probability. Reperfusion-era and population differences affect calibration. Do not use it to delay emergency STEMI evaluation or reperfusion.

## Application

The standalone browser calculator is in [web/index.html](web/index.html). It uses ordinary JavaScript: no Python runtime, account, external API, or transmission of entered patient data is required. The GitHub Pages workflow publishes static files from the web directory; consult repository **Actions → Deploy clinical calculator to GitHub Pages** for deployment status.

## Variables (original TIMI STEMI score)

| Variable | Points |
| --- | ---: |
| Age 65–74 years | 2 |
| Age ≥75 years (instead of 65–74) | 3 |
| Any history of diabetes, hypertension, or angina | 1 |
| Systolic BP <100 mm Hg | 3 |
| Heart rate >100 beats/min | 2 |
| Killip class II–IV | 2 |
| Weight <67 kg | 1 |
| Anterior ST elevation or LBBB | 1 |
| Time to treatment >4 hours | 1 |

**30-day all-cause mortality (original cohort):**

| Points | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9–14 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mortality (%) | 0.8 | 1.6 | 2.2 | 4.4 | 7.3 | 12.4 | 16.1 | 23.4 | 26.8 | 35.9 |

These are the **STEMI** predictors, not the different TIMI score for unstable angina/NSTEMI. All eight fields are mandatory. Exactly 100 mm Hg, 100 bpm, 67 kg, and 4 hours do **not** meet their strict thresholds.

## Use with Python

Requires Python 3.10+. The scoring module itself uses only Python's standard library.

~~~bash
python timi_stemi.py single --age 75 --sbp 90 --heart-rate 110 --killip 2 --weight 60 --time-to-treatment 5 --dm-htn-angina --anterior-or-lbbb
python timi_stemi.py batch --input sample.csv --output results.csv
~~~

Single-case output contains the score, maximum score, 30-day mortality estimate, point breakdown and clinical context; the maximum-risk example above scores **14**.

CSV input requires these exact column names:

~~~text
age,diabetes_hypertension_angina,systolic_bp,heart_rate,killip_class,weight_kg,anterior_st_elevation_or_lbbb,time_to_treatment_hours
~~~

Boolean fields accept yes/no, true/false or 1/0 (case-insensitive). Additional identifiers remain in output. Invalid rows produce errors instead of silently defaulting predictors. Use de-identified data only.

## API and optional legacy tools

~~~bash
python -m pip install -r requirements.txt
python cli.py serve --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000/ for the browser calculator or POST eight variables as a JSON object to /api/timi-stemi. Interactive API documentation is at /docs; current OpenAPI is at /openapi.json.

Older, **separate** experimental operations modules remain in the agents package, enrichment.py, simulator.py and cli.py for compatibility. Their generic audit thresholds, simulated language-model responses and enrichment outputs are **not** clinically validated TIMI STEMI calculations. Do not use /api/audit or those modules to assess patient prognosis.

For legacy audit functionality, set a strong unique AUDIT_SECRET_KEY environment variable (at least 16 characters) before running audit commands or the Docker service. The HMAC trail is process-local, not a persistent clinical audit system. Do not expose legacy endpoints publicly without authentication and privacy/security review.

## Development and tests

~~~bash
python -m pip install -r requirements.txt
python -m pytest -q
node --test web/score.test.js
node --check web/score.js
~~~

Node.js is required only for JavaScript unit tests, not for using the calculator. Python tests cover clinical thresholds, mortality lookup, invalid inputs, CSV processing, API scoring and legacy audit components. CI checks Python 3.10–3.13 and Node.js 22. For a local Docker API:

~~~bash
export AUDIT_SECRET_KEY='generate-a-unique-random-secret-here'
docker compose up --build
~~~

The sample Compose service publishes port 8000; restrict it to trusted networks. Never commit actual patient data or runtime secrets. The static calculator does not store clinical entries in browser storage. It needs a JavaScript-module-capable browser (recent Chrome, Firefox, Edge, or Safari) and works on a static host, including GitHub Pages.

## Reference

Morrow DA, Antman EM, Charlesworth A, et al. TIMI risk score for ST-elevation myocardial infarction: a convenient, bedside, clinical score for risk assessment at presentation. *Circulation.* 2000;102:2031–2037. [doi:10.1161/01.CIR.102.17.2031](https://doi.org/10.1161/01.CIR.102.17.2031). See also the [TIMI Study Group calculator](https://timi.org/timi-risk-score-calculator-for-stemi/).

## License

[MIT](LICENSE).
