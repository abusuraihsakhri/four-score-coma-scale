# FOUR Score — Coma Assessment

A clinical scoring aid for the **Full Outline of UnResponsiveness (FOUR)** scale. An examiner selects one finding in each of four domains: **eye, motor, brainstem reflexes, and respiration**. Each contributes 0–4 points, giving an integer total of **0–16**. Lower totals indicate more impaired findings. The software does not assign prognostic cutoffs or recommend treatment.

## Browser calculator

Open `web/index.html` in a modern browser, select all four findings, then view, print, or export the score to CSV. No server, install, Python, or external JavaScript dependencies are needed. An automated GitHub Pages deployment workflow publishes the `web/` directory when Pages is enabled.

## Python calculator

The clinical scoring code uses the Python standard library (Python 3.10+).

```bash
python four_score.py single --eye 4 --motor 3 --brainstem 2 --respiration 1
# score: 10 / 16

python four_score.py batch -i sample.csv -o results.csv
```

CSV requires `eye,motor,brainstem,respiration` columns with whole-number points from 0 to 4. Other input columns are preserved. The output adds `four_score_total`. Invalid rows are rejected before the result file is replaced.

### Optional REST API and legacy demonstration

```bash
python -m pip install -r requirements-dev.txt
python cli.py serve --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/api/four-score \
  -H 'Content-Type: application/json' \
  -d '{"eye":4,"motor":3,"brainstem":2,"respiration":1}'
```

The `POST /api/four-score` endpoint enforces integer values 0–4. The separate `cli.py audit`, `cli.py chat`, `/api/audit`, and `/api/chat` commands are **legacy generic demonstrations**, **not FOUR score calculations or validated clinical decision support**. The chat path is a deterministic stub, not a language-model integration. The in-memory HMAC audit chain is process-local, is not a persistent ledger, and does not independently prove that the original event data are accurate.

## Privacy and safety

The static browser calculator neither sends nor stores examination data. Avoid entering identifiable clinical data in CSV files, CLI arguments, or the API; those workflows process local or server-side inputs and the legacy demo retains some metadata in memory. The demonstration's regex identifier checks are incomplete and **do not establish HIPAA compliance or de-identification**. Set `AUDIT_SECRET_KEY` in the server environment if a stable process-specific audit key is required; if absent, an ephemeral random key is generated. This is not intended as the sole basis for clinical decisions.

## Development and testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q four_score.py cli.py agents tests
docker build -t four-score-coma-scale .
```

The browser application uses HTML, CSS, and native JavaScript; the optional API uses FastAPI/Pydantic. CI tests the supported Python versions and checks browser JavaScript syntax. GitHub Pages hosts only the static calculator: it cannot run `cli.py` or the FastAPI service.

## Reference

Wijdicks EFM, Bamlet WR, Maramattom BV, Manno EM, McClelland RL. Validation of a new coma scale: The FOUR score. *Ann Neurol.* 2005;58:585–593. [doi:10.1002/ana.20611](https://doi.org/10.1002/ana.20611).

## License

[MIT](LICENSE).
