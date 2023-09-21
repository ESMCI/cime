import os
import glob
import re
import gzip
import logging
from CIME.utils import expect

logger = logging.getLogger(__name__)

def get_latest_cpl_logs(case):
    """
    find and return the latest cpl log file in the run directory
    """
    coupler_log_path = case.get_value("RUNDIR")
    cpllog_name = "drv" if case.get_value("COMP_INTERFACE") == "nuopc" else "cpl"
    cpllogs = glob.glob(
        os.path.join(coupler_log_path, "{}*.log.*".format(cpllog_name))
    )
    lastcpllogs = []
    if cpllogs:
        lastcpllogs.append(max(cpllogs, key=os.path.getctime))
        basename = os.path.basename(lastcpllogs[0])
        suffix = basename.split(".", 1)[1]
        for log in cpllogs:
            if log in lastcpllogs:
                continue

            if log.endswith(suffix):
                lastcpllogs.append(log)

    return lastcpllogs

def compare_memory(case):
    baseline_root = case.get_value("BASELINE_ROOT")

    baseline_name = case.get_value("BASECMP_CASE")

    baseline_dir = os.path.join(baseline_root, baseline_name)

    latest_cpl_logs = get_latest_cpl_logs(case)

    diff, baseline, current = [None]*3

    for cpllog in latest_cpl_logs:
        try:
            baseline = read_baseline_mem(baseline_dir)
        except FileNotFoundError as e:
            logger.debug("Could not read baseline memory usage: %s", e)

            continue

        if baseline is None:
            baseline = 0.0

        memlist = get_mem_usage(cpllog)

        if len(memlist) <= 3:
            logger.debug(f"Found {len(memlist)} memory usage samples, need atleast 4")

            continue

        current = memlist[-1][1]

        try:
            diff = (current - baseline) / baseline
        except ZeroDivisionError:
            diff = 0.0

    tolerance = case.get_value("TEST_MEMLEAK_TOLERANCE")

    if tolerance is None:
        tolerance = 0.1

    # Should we check if tolerance is above 0
    below_tolerance = None

    if diff is not None:
        below_tolerance = diff < tolerance

    return below_tolerance, diff, tolerance, baseline, current

def compare_throughput(case):
    baseline_root = case.get_value("BASELINE_ROOT")

    baseline_name = case.get_value("BASECMP_CASE")

    baseline_dir = os.path.join(baseline_root, baseline_name)

    latest_cpl_logs = get_latest_cpl_logs(case)

    diff, baseline, current = [None]*3

    # Do we need this loop, when are there multiple cpl logs?
    for cpllog in latest_cpl_logs:
        try:
            baseline = read_baseline_tput(baseline_dir)
        except (FileNotFoundError, IndexError, ValueError) as e:
            logger.debug("Could not read baseline throughput: %s", e)

            continue

        current = get_throughput(cpllog)

        try:
            # comparing ypd so bigger is better
            diff = (baseline - current) / baseline
        except (ValueError, TypeError):
            # Should we default the diff to 0.0 as with _compare_current_memory?
            logger.debug(
                "Could not determine change in throughput between baseline %s and current %s",
                baseline,
                current,
            )

            continue

    tolerance = case.get_value("TEST_TPUT_TOLERANCE")

    if tolerance is None:
        tolerance = 0.1

    expect(
        tolerance > 0.0,
        "Bad value for throughput tolerance in test",
    )

    below_tolerance = None

    if diff is not None:
        below_tolerance = diff < tolerance

    return below_tolerance, diff, tolerance, baseline, current

def write_baseline_tput(baseline_dir, cpllog):
    """
    Writes baseline throughput to file.

    A "-1" indicates that no throughput data was available from the coupler log.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.
    cpllog : str
        Path to the current coupler log.
    """
    tput_file = os.path.join(baseline_dir, "cpl-tput.log")

    tput = get_throughput(cpllog)

    with open(tput_file, "w") as fd:
        fd.write("# Throughput in simulated years per compute day\n")
        fd.write(
            "# A -1 indicates no throughput data was available from the test\n"
        )

        if tput is None:
            fd.write("-1")
        else:
            fd.write(str(tput))

def write_baseline_mem(baseline_dir, cpllog):
    """
    Writes baseline memory usage highwater to file.

    A "-1" indicates that no memory usage data was available from the coupler log.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.
    cpllog : str
        Path to the current coupler log.
    """
    mem_file = os.path.join(baseline_dir, "cpl-mem.log")

    mem = get_mem_usage(cpllog)

    with open(mem_file, "w") as fd:
        fd.write("# Memory usage highwater\n")
        fd.write(
            "# A -1 indicates no memory usage data was available from the test\n"
        )

        try:
            fd.write(str(mem[-1][1]))
        except IndexError:
            fd.write("-1")

def read_baseline_tput(baseline_dir):
    """
    Reads throughput baseline.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.

    Returns
    -------
    float
        Value of the throughput.

    Raises
    ------
    FileNotFoundError
        If baseline file does not exist.
    IndexError
        If no throughput value is found.
    ValueError
        If throughput value is not a float.
    """
    try:
        tput = read_baseline_value(os.path.join(baseline_dir, "cpl-tput.log"))
    except (IndexError, ValueError):
        tput = None

    if tput == -1:
        tput = None

    return tput

def read_baseline_mem(baseline_dir):
    """
    Reads memory usage highwater baseline.

    The default behvaior was to return 0 if no usage data was found.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.

    Returns
    -------
    float
        Value of the highwater memory usage.

    Raises
    ------
    FileNotFoundError
        If baseline file does not exist.
    """
    try:
        memory = read_baseline_value(
            os.path.join(baseline_dir, "cpl-mem.log")
        )
    except (IndexError, ValueError):
        memory = 0

    if memory == -1:
        memory = 0

    return memory

def read_baseline_value(baseline_file):
    """
    Read baseline value from file.

    Parameters
    ----------
    baseline_file : str
        Path to baseline file.

    Returns
    -------
    float
        Baseline value.

    Raises
    ------
    FileNotFoundError
        If ``baseline_file`` is not found.
    IndexError
        If not values are present in ``baseline_file``.
    ValueError
        If value in ``baseline_file`` is not a float.
    """
    with open(baseline_file) as fd:
        lines = [x for x in fd.readlines() if not x.startswith("#")]

    return float(lines[0])

def get_mem_usage(cpllog):
    """
    Examine memory usage as recorded in the cpl log file and look for unexpected
    increases.
    """
    memlist = []
    meminfo = re.compile(
        r".*model date =\s+(\w+).*memory =\s+(\d+\.?\d+).*highwater"
    )
    if cpllog is not None and os.path.isfile(cpllog):
        if ".gz" == cpllog[-3:]:
            fopen = gzip.open
        else:
            fopen = open
        with fopen(cpllog, "rb") as f:
            for line in f:
                m = meminfo.match(line.decode("utf-8"))
                if m:
                    memlist.append((float(m.group(1)), float(m.group(2))))
    # Remove the last mem record, it's sometimes artificially high
    if len(memlist) > 0:
        memlist.pop()
    return memlist

def get_throughput(cpllog):
    """
    Examine memory usage as recorded in the cpl log file and look for unexpected
    increases.
    """
    if cpllog is not None and os.path.isfile(cpllog):
        with gzip.open(cpllog, "rb") as f:
            cpltext = f.read().decode("utf-8")
            m = re.search(r"# simulated years / cmp-day =\s+(\d+\.\d+)\s", cpltext)
            if m:
                return float(m.group(1))
    return None

