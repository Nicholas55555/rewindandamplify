"""Turn raw device counts into results: hit rates, conditional distributions, the after-click fingerprint, the noise.

It reads every results/hardware/raw_*.json, from real jobs and from local dry runs alike, and scores each circuit
against its noiseless answer, computed fresh from the same logical circuit.

    python experiments/analyse_hardware.py
"""

import glob
import json
from pathlib import Path

from common import RESULTS, save

import numpy as np
from qiskit.quantum_info import Statevector, hellinger_fidelity

from qrsm_grover.classical import conditional_distribution, total_variation
from qrsm_grover.hardware import NONE, ONE, readout_correct, suite
from qrsm_grover.predicates import any_click, click_at
from qrsm_grover.queries import exact_after_click
from qrsm_grover.search import demo_catalog

OUT = "hardware"


def to_distribution(counts: dict, n_bits: int) -> np.ndarray:
    d = np.zeros(2 ** n_bits)
    for bits, c in counts.items():
        d[int(bits.replace(" ", ""), 2)] += c
    return d / d.sum()


def device_flip_rates(calibration: dict) -> dict:
    """Each physical qubit's readout error rates, from the all-zeros and all-ones circuits."""
    zeros, ones = calibration["counts"]
    rates = {}
    for i, qubit in enumerate(calibration["qubits"]):
        flips = []
        for counts, wrong in ((zeros, 1), (ones, 0)):
            total = sum(counts.values())
            flips.append(sum(c for bits, c in counts.items() if (int(bits.replace(" ", ""), 2) >> i) & 1 == wrong) / total)
        rates[qubit] = tuple(flips)
    return rates


def model_of(meta: dict):
    return ONE if meta.get("k", 1) == 1 else NONE


def question_mask(meta: dict) -> np.ndarray:
    T = meta["T"]
    return (any_click() if meta["question"] == "any click" else click_at(T)).mask(T)


def score_history(meta: dict, measured: np.ndarray, ideal: np.ndarray) -> dict:
    model = model_of(meta)
    T, n = meta["T"], model.n_memory
    mask = question_mask(meta)
    values = np.arange(measured.size)
    histories = (values >> n) & (2 ** T - 1)
    hist = np.bincount(histories, weights=measured, minlength=2 ** T)
    hist_ideal = np.bincount(histories, weights=ideal, minlength=2 ** T)
    exact = conditional_distribution(model.history_probabilities(T), mask)
    hit = float(hist[mask].sum())
    return {"hit": hit, "ideal_hit": float(hist_ideal[mask].sum()), "tvd": total_variation(np.where(mask, hist, 0) / max(hit, 1e-12), exact),
            "ideal_tvd": total_variation(conditional_distribution(hist_ideal, mask), exact)}


def score_loop(meta: dict, measured: np.ndarray) -> dict:
    model = model_of(meta)
    n, t0, tau, width = model.n_memory, meta["t0"], meta["tau"], meta["width"]
    values = np.arange(measured.size)
    kept = ((values >> (n + t0 - 1)) & 1) == 1
    base = width - tau
    weight = float(measured[kept].sum())
    conditional = np.array([measured[kept & (((values >> (base + j)) & 1) == 1)].sum() / max(weight, 1e-12) for j in range(tau)])
    exact = exact_after_click(model, t0, tau)
    return {"kept": weight, "conditional": conditional, "exact": exact["conditional"],
            "error": float(np.abs(conditional - exact["conditional"]).max())}


def score_catalog(meta: dict, measured: np.ndarray, ideal: np.ndarray) -> dict:
    from qrsm_grover.search import classical_scores, tokenise, tokens_of

    catalog = demo_catalog(meta["N"])
    vocabulary = set().union(*(tokens_of(name) for name in catalog))
    scores = classical_scores(catalog, tokenise(meta["query"], vocabulary))
    target = int(np.argmax(scores))
    return {"target": catalog[target], "hit": float(measured[target]), "ideal_hit": float(ideal[target]),
            "distribution": measured, "ideal_distribution": ideal}


def analyse(path: Path, ideals: dict) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    device_rates = device_flip_rates(raw["calibration"])
    rows = []
    for item in raw["experiments"]:
        name, meta = item["name"], item["meta"]
        n_bits = item["logical_qubits"]
        measured = to_distribution(item["counts"], n_bits)
        ideal = ideals[name]
        rates = [device_rates[q] for q in item["physical_qubits"]]
        corrected = readout_correct(measured, rates)
        row = {"name": name, "meta": meta, "two_qubit_gates": item["two_qubit_gates"], "depth": item["depth"],
               "estimated_success": item["estimated_success"], "physical_qubits": item["physical_qubits"],
               "fidelity_raw": float(hellinger_fidelity(dict(enumerate(measured)), dict(enumerate(ideal)))),
               "fidelity_corrected": float(hellinger_fidelity(dict(enumerate(corrected)), dict(enumerate(ideal))))}
        if meta["kind"] == "history":
            row["raw"] = score_history(meta, measured, ideal)
            row["corrected"] = score_history(meta, corrected, ideal)
        elif meta["kind"] == "loop":
            row["raw"] = score_loop(meta, measured)
            row["corrected"] = score_loop(meta, corrected)
        elif meta["kind"] == "catalog":
            row["raw"] = score_catalog(meta, measured, ideal)
            row["corrected"] = score_catalog(meta, corrected, ideal)
        elif meta["kind"] == "echo":
            row["raw"] = {"return": float(measured[0])}
            row["corrected"] = {"return": float(corrected[0])}
        rows.append(row)
    return {"meta": raw["meta"], "rows": rows}


def table(result: dict) -> str:
    lines = [f"### {result['meta'].get('backend')}: {result['meta'].get('mode')} ({result['meta'].get('suppression')})", "",
             "| circuit | 2q gates | hit, ideal | hit, measured | hit, readout-corrected | conditional TVD | fidelity |",
             "|---|---|---|---|---|---|---|"]
    for row in result["rows"]:
        kind = row["meta"]["kind"]
        if kind == "history":
            lines.append(f"| {row['name']} | {row['two_qubit_gates']} | {row['raw']['ideal_hit']:.3f} | {row['raw']['hit']:.3f} | "
                         f"{row['corrected']['hit']:.3f} | {row['corrected']['tvd']:.3f} | {row['fidelity_corrected']:.3f} |")
        elif kind == "catalog":
            lines.append(f"| {row['name']} | {row['two_qubit_gates']} | {row['raw']['ideal_hit']:.3f} | {row['raw']['hit']:.3f} | "
                         f"{row['corrected']['hit']:.3f} | | {row['fidelity_corrected']:.3f} |")
        elif kind == "loop":
            lines.append(f"| {row['name']} | {row['two_qubit_gates']} | exact {np.round(row['raw']['exact'], 3).tolist()} | "
                         f"{np.round(row['raw']['conditional'], 3).tolist()} | {np.round(row['corrected']['conditional'], 3).tolist()} | "
                         f"kept {row['raw']['kept']:.3f} | {row['fidelity_corrected']:.3f} |")
        elif kind == "echo":
            lines.append(f"| {row['name']} | {row['two_qubit_gates']} | 1.000 | {row['raw']['return']:.3f} | "
                         f"{row['corrected']['return']:.3f} | | |")
    return "\n".join(lines)


def main() -> None:
    files = sorted(glob.glob(str(RESULTS / OUT / "raw_*.json")))
    if not files:
        print("no raw results yet: run experiments/run_ibm.py first")
        return
    ideals = {}
    for exp in suite(False):
        logical = exp.circuit.remove_final_measurements(inplace=False)
        ideals[exp.name] = np.abs(Statevector(logical).data) ** 2
    report = []
    for f in files:
        path = Path(f)
        print(f"analysing {path.name}", flush=True)
        result = analyse(path, ideals)
        tag = path.stem.replace("raw_", "")
        save(OUT, result, f"summary_{tag}.json")
        report.append(table(result))
    (RESULTS / OUT / "summary.md").write_text("\n\n".join(report) + "\n", encoding="utf-8")
    print("\n\n".join(report))


if __name__ == "__main__":
    main()
