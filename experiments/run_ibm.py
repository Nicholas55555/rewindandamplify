"""Run the experiment on real IBM Quantum hardware, with your own account.

Save your account once, in your own terminal; the key is typed at a hidden prompt and never appears here:

    python tools/save_ibm_account.py

Then:

    python experiments/run_ibm.py --plan            pick a device, compile everything, estimate QPU time. Uses no QPU time.
    python experiments/run_ibm.py --submit          submit the jobs (this uses QPU time from your allowance)
    python experiments/run_ibm.py --fetch           wait for the jobs and save the raw counts
    python experiments/analyse_hardware.py          turn the counts into tables and figures

Two jobs are submitted, the same circuits in both, so that the effect of error suppression can be measured:
    plain        no suppression at all
    suppressed   dynamical decoupling (XY4) and Pauli twirling of gates and measurements

Everything can be rehearsed without an account. This runs the same code path on a local device snapshot:

    python experiments/run_ibm.py --dry-run FakeFez
"""

import argparse
import json
import time

from common import RESULTS, save


from qrsm_grover.hardware import compile_best, readout_calibration, suite

# SamplerV2 is deprecated from qiskit-ibm-runtime 0.50, with at least three months' notice, in favour of a client-side
# sampler. It is still the documented way to set these options in 0.51, so this stays on it for now.

OUT = "hardware"
SHOTS = 4096
CAL_SHOTS = 4096
SECONDS_PER_SHOT_GUESS = 300e-6  # the device's repetition delay dominates; for the estimate only


def service():
    from qiskit_ibm_runtime import QiskitRuntimeService

    return QiskitRuntimeService()  # the account you saved; raises if there is none


def pick_backend(svc, name: str | None):
    if name:
        return svc.backend(name)
    return svc.least_busy(operational=True, simulator=False, min_num_qubits=20)


def build(backend, quick: bool, seeds: int) -> tuple:
    """Compile every experiment, and add one readout calibration pair covering every physical qubit they use."""
    experiments = suite(quick)
    compiled, info = [], []
    for i, exp in enumerate(experiments):
        t0 = time.time()
        isa, stats = compile_best(exp.circuit, backend, seeds=seeds)
        compiled.append(isa)
        info.append({"name": exp.name, "meta": exp.meta, "logical_qubits": exp.circuit.num_qubits, **stats})
        print(f"  {i + 1:2d}/{len(experiments)} {exp.name:34s} {stats['two_qubit_gates']:3d} two-qubit gates, depth "
              f"{stats['depth']:4d}, predicted survival {stats['estimated_success']:.2f}, qubits {stats['physical_qubits']}  "
              f"[{time.time() - t0:.0f}s]", flush=True)
    from qiskit import transpile

    used = sorted({q for item in info for q in item["physical_qubits"]})
    device_qubits = backend.num_qubits
    calibration = [transpile(qc, backend=backend, optimization_level=0, initial_layout=list(range(device_qubits)))
                   for qc in readout_calibration(used, device_qubits)]
    return compiled, info, calibration, used


def plan_summary(backend, info: list, calibration: list) -> dict:
    shots = len(info) * SHOTS + len(calibration) * CAL_SHOTS
    return {"backend": backend.name, "experiments": len(info), "calibration_circuits": len(calibration),
            "shots_per_job": shots, "estimated_qpu_seconds_per_job": shots * SECONDS_PER_SHOT_GUESS,
            "most_two_qubit_gates": max(x["two_qubit_gates"] for x in info), "time": time.strftime("%Y-%m-%d %H:%M:%S")}


def sampler_for(mode, suppressed: bool):
    from qiskit_ibm_runtime import SamplerV2

    sampler = SamplerV2(mode=mode)
    if suppressed:
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XY4"
        sampler.options.twirling.enable_gates = True
        sampler.options.twirling.enable_measure = True
        sampler.options.twirling.num_randomizations = 32
        sampler.options.twirling.shots_per_randomization = SHOTS // 32
    return sampler


def pubs_for(compiled: list, calibration: list) -> list:
    return [(qc, None, SHOTS) for qc in compiled] + [(qc, None, CAL_SHOTS) for qc in calibration]


def counts_from(pub_result) -> dict:
    """The counts of whichever classical register a result used."""
    data = pub_result.data
    name = "meas" if hasattr(data, "meas") else [k for k in data.keys()][0]
    return getattr(data, name).get_counts()


def save_raw(tag: str, info: list, used: list, n_exp: int, results, meta: dict) -> None:
    counts = [counts_from(r) for r in results]
    save(OUT, {"meta": meta, "experiments": [{**x, "counts": c} for x, c in zip(info, counts[:n_exp])],
               "calibration": {"qubits": used, "counts": counts[n_exp:]}}, f"raw_{tag}.json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--dry-run", metavar="FAKE_BACKEND", help="run everything locally on a device snapshot")
    ap.add_argument("--backend", help="a device name; default: the least busy one")
    ap.add_argument("--quick", action="store_true", help="only the first few circuits")
    ap.add_argument("--plain-only", action="store_true", help="submit only the job without error suppression")
    ap.add_argument("--seeds", type=int, default=8)
    args = ap.parse_args()
    (RESULTS / OUT).mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        from qiskit_ibm_runtime import fake_provider

        backend = getattr(fake_provider, args.dry_run)()
        compiled, info, calibration, used = build(backend, args.quick, args.seeds)
        print(json.dumps(plan_summary(backend, info, calibration), indent=1), flush=True)
        t0 = time.time()
        job = sampler_for(backend, False).run(pubs_for(compiled, calibration))
        result = job.result()
        save_raw(f"dryrun_{args.dry_run}", info, used, len(compiled), result,
                 {"backend": backend.name, "mode": "local dry run on a device snapshot, not real hardware", "job_id": None,
                  "suppression": "none", "shots": SHOTS, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        print(f"dry run finished in {time.time() - t0:.0f} s", flush=True)
        return

    svc = service()
    if args.plan or args.submit:
        names = [b.name for b in svc.backends(operational=True, simulator=False)]
        print(f"devices this account can use: {', '.join(names)}", flush=True)
        backend = pick_backend(svc, args.backend)
        print(f"compiling for {backend.name}", flush=True)
        compiled, info, calibration, used = build(backend, args.quick, args.seeds)
        summary = plan_summary(backend, info, calibration)
        print(json.dumps(summary, indent=1), flush=True)
        save(OUT, {**summary, "experiments": info, "calibrated_qubits": used}, "plan.json")
        if args.submit:
            jobs = {}
            for tag, suppressed in (("plain", False), ("suppressed", True)):
                if suppressed and args.plain_only:
                    continue
                job = sampler_for(backend, suppressed).run(pubs_for(compiled, calibration))
                jobs[tag] = job.job_id()
                print(f"submitted {tag}: job {job.job_id()} on {backend.name}", flush=True)
            save(OUT, {"backend": backend.name, "jobs": jobs, "submitted": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "experiments": info, "calibrated_qubits": used, "shots": SHOTS}, "jobs.json")
    if args.fetch:
        info_file = json.loads((RESULTS / OUT / "jobs.json").read_text(encoding="utf-8"))
        info, used = info_file["experiments"], info_file["calibrated_qubits"]
        for tag, job_id in info_file["jobs"].items():
            job = svc.job(job_id)
            print(f"{tag}: job {job_id} is {job.status()}", flush=True)
            result = job.result()  # waits for the job
            usage = None
            try:
                usage = job.usage()
            except Exception:  # not every plan reports it
                pass
            save_raw(tag, info, used, len(info), result,
                     {"backend": info_file["backend"], "mode": "real IBM Quantum hardware", "job_id": job_id,
                      "suppression": tag, "shots": info_file["shots"], "qpu_seconds": usage,
                      "submitted": info_file["submitted"], "fetched": time.strftime("%Y-%m-%d %H:%M:%S")})
            print(f"{tag}: saved. QPU time used: {usage} s", flush=True)


if __name__ == "__main__":
    main()
