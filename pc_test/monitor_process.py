import time
import csv
import psutil
import sys

# optional NVIDIA GPU support
try:
    from pynvml import *  # type: ignore
    nvmlInit()
    GPU_AVAILABLE = True
    handle = nvmlDeviceGetHandleByIndex(0)
except Exception:
    GPU_AVAILABLE = False
    handle = None


def _safe_process(pid: int):
    try:
        return psutil.Process(pid)
    except psutil.NoSuchProcess:
        return None


def _get_proc_tree(root: psutil.Process):
    """Return a de-duplicated list of root + all recursive children that are alive."""
    procs = [root]
    try:
        procs.extend(root.children(recursive=True))
    except Exception:
        pass

    uniq = []
    seen = set()
    for p in procs:
        try:
            if p.pid in seen:
                continue
            seen.add(p.pid)
            if p.is_running():
                uniq.append(p)
        except Exception:
            continue
    return uniq


def _warmup_cpu(procs):
    """Warm up cpu_percent counters for all processes to avoid first-sample zeros."""
    for p in procs:
        try:
            p.cpu_percent(None)
        except Exception:
            pass


def _sum_cpu_mem_threads(procs):
    cpu_sum = 0.0
    rss_sum_mb = 0.0
    threads_sum = 0
    alive = 0

    for p in procs:
        try:
            cpu_sum += p.cpu_percent(None)
            rss_sum_mb += p.memory_info().rss / 1024 / 1024
            threads_sum += p.num_threads()
            alive += 1
        except Exception:
            continue

    return cpu_sum, rss_sum_mb, threads_sum, alive


def _get_gpu_overall():
    """Return (gpu_util_percent, gpu_mem_used_mb) or ("","") if unavailable."""
    if not GPU_AVAILABLE:
        return "", ""
    try:
        util = nvmlDeviceGetUtilizationRates(handle)
        meminfo = nvmlDeviceGetMemoryInfo(handle)
        return util.gpu, meminfo.used / 1024 / 1024
    except Exception:
        return "", ""


def _get_gpu_mem_for_pids(target_pids: set[int]):
    """
    Best-effort process GPU memory (MB) for a set of PIDs.
    Tries compute + graphics running processes. If nothing matched, returns "".
    """
    if not GPU_AVAILABLE:
        return ""

    used_bytes = 0
    found = False

    # compute processes
    try:
        for p in nvmlDeviceGetComputeRunningProcesses(handle):
            if p.pid in target_pids and p.usedGpuMemory not in (None, 0):
                used_bytes += int(p.usedGpuMemory)
                found = True
    except Exception:
        pass

    # graphics processes (may not exist in some pynvml versions/drivers)
    try:
        for p in nvmlDeviceGetGraphicsRunningProcesses(handle):
            if p.pid in target_pids and p.usedGpuMemory not in (None, 0):
                used_bytes += int(p.usedGpuMemory)
                found = True
    except Exception:
        pass

    if not found:
        return ""
    return used_bytes / 1024 / 1024


def monitor(pid: int, out_file: str = "resource_log.csv", interval: float = 1.0):
    root = _safe_process(pid)
    if root is None:
        print("Target process not found.")
        return

    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            # totals over process tree (default)
            "cpu_total_percent",
            "rss_total_mb",
            "threads_total",
            "num_procs",
            # GPU overall (most important for hardware validation)
            "gpu_util",
            "gpu_mem_used_mb",
            # best-effort process-tree GPU mem
            "proc_tree_gpu_mem_mb",
        ])

        # warmup
        procs = _get_proc_tree(root)
        _warmup_cpu(procs)

        start = time.time()

        while True:
            try:
                # refresh proc tree each tick (WebEngine children can appear later)
                procs = _get_proc_tree(root)

                cpu_total, rss_total_mb, threads_total, alive = _sum_cpu_mem_threads(procs)

                gpu_util, gpu_mem = _get_gpu_overall()
                proc_tree_gpu_mem = _get_gpu_mem_for_pids({p.pid for p in procs})

                writer.writerow([
                    time.time() - start,
                    cpu_total,
                    rss_total_mb,
                    threads_total,
                    alive,
                    gpu_util,
                    gpu_mem,
                    proc_tree_gpu_mem,
                ])

                f.flush()
                time.sleep(interval)

            except psutil.NoSuchProcess:
                print("Process ended.")
                break
            except KeyboardInterrupt:
                print("Stopped by user.")
                break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python monitor_process.py <PID> [out_file] [interval_sec]")
        sys.exit(1)

    pid = int(sys.argv[1])
    out_file = sys.argv[2] if len(sys.argv) >= 3 else "resource_log.csv"
    interval = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0

    monitor(pid, out_file=out_file, interval=interval)