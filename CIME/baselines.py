import os
import glob
import re
import gzip
import logging
from CIME.config import Config
from CIME.utils import expect

logger = logging.getLogger(__name__)


def get_latest_cpl_logs(case):
    """
    find and return the latest cpl log file in the run directory
    """
    coupler_log_path = case.get_value("RUNDIR")

    cpllog_name = "drv" if case.get_value("COMP_INTERFACE") == "nuopc" else "cpl"

    cpllogs = glob.glob(os.path.join(coupler_log_path, "{}*.log.*".format(cpllog_name)))

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


def compare_memory(case, baseline_dir=None):
    """
    Compare current memory usage to baseline.

    Parameters
    ----------
    case : CIME.case.case.Case
        Case object.
    baseline_dir : str or None
        Path to the baseline directory.

    Returns
    -------
    below_tolerance : bool
        Whether the current memory usage is below the baseline.
    comments : str
        Comments about baseline comparison.
    """
    if baseline_dir is None:
        baseline_dir = case.get_baseline_dir()

    config = load_coupler_customization(case)

    # TODO need better handling
    try:
        try:
            current = config.get_mem_usage(case)
        except AttributeError:
            current = default_get_mem_usage(case)[-1][1]
    except RuntimeError as e:
        return None, str(e)

    try:
        baseline = read_baseline_mem(baseline_dir)
    except FileNotFoundError as e:
        comment = f"Could not read baseline memory usage: {e!s}"

        logger.debug(comment)

        return None, comment

    if baseline is None:
        baseline = 0.0

    tolerance = case.get_value("TEST_MEMLEAK_TOLERANCE")

    if tolerance is None:
        tolerance = 0.1

    try:
        below_tolerance, comments = config.compare_memory_baseline(
            current, baseline, tolerance
        )
    except AttributeError:
        below_tolerance, comments = compare_memory_baseline(
            current, baseline, tolerance
        )

    return below_tolerance, comments


def compare_memory_baseline(current, baseline, tolerance):
    try:
        diff = (current - baseline) / baseline
    except ZeroDivisionError:
        diff = 0.0

    # Should we check if tolerance is above 0
    below_tolerance = None
    comment = ""

    if diff is not None:
        below_tolerance = diff < tolerance

        if below_tolerance:
            comment = "MEMCOMP: Memory usage highwater has changed by {:.2f}% relative to baseline".format(
                diff * 100
            )
        else:
            comment = "Error: Memory usage increase >{:d}% from baseline's {:f} to {:f}".format(
                int(tolerance * 100), baseline, current
            )

    return below_tolerance, comment


def compare_throughput(case, baseline_dir=None):
    if baseline_dir is None:
        baseline_dir = case.get_baseline_dir()

    config = load_coupler_customization(case)

    try:
        current = config.get_throughput(case)
    except AttributeError:
        current = default_get_throughput(case)

    try:
        baseline = read_baseline_tput(baseline_dir)
    except FileNotFoundError as e:
        comment = f"Could not read baseline throughput file: {e!s}"

        logger.debug(comment)

        return None, comment

    tolerance = case.get_value("TEST_TPUT_TOLERANCE")

    if tolerance is None:
        tolerance = 0.1

    expect(
        tolerance > 0.0,
        "Bad value for throughput tolerance in test",
    )

    try:
        below_tolerance, comment = config.compare_baseline_throughput(
            current, baseline, tolerance
        )
    except AttributeError:
        below_tolerance, comment = compare_baseline_throughput(
            current, baseline, tolerance
        )

    return below_tolerance, comment


def load_coupler_customization(case):
    comp_root_dir_cpl = case.get_value("COMP_ROOT_DIR_CPL")

    cpl_customize = os.path.join(comp_root_dir_cpl, "cime_config", "customize")

    return Config.load(cpl_customize)


def compare_baseline_throughput(current, baseline, tolerance):
    try:
        # comparing ypd so bigger is better
        diff = (baseline - current) / baseline
    except (ValueError, TypeError):
        # Should we default the diff to 0.0 as with _compare_current_memory?
        comment = f"Could not determine diff with baseline {baseline!r} and current {current!r}"

        logger.debug(comment)

        diff = None

    below_tolerance = None

    if diff is not None:
        below_tolerance = diff < tolerance

        if below_tolerance:
            comment = "TPUTCOMP: Computation time changed by {:.2f}% relative to baseline".format(
                diff * 100
            )
        else:
            comment = "Error: TPUTCOMP: Computation time increase > {:d}% from baseline".format(
                int(tolerance * 100)
            )

    return below_tolerance, comment


def write_baseline(case, basegen_dir, throughput=True, memory=True):
    config = load_coupler_customization(case)

    if throughput:
        try:
            try:
                tput = config.get_throughput(case)
            except AttributeError:
                tput = str(default_get_throughput(case))
        except RuntimeError:
            pass
        else:
            write_baseline_tput(basegen_dir, tput)

    if memory:
        try:
            try:
                mem = config.get_mem_usage(case)
            except AttributeError:
                mem = str(default_get_mem_usage(case)[-1][1])
        except RuntimeError:
            pass
        else:
            write_baseline_mem(basegen_dir, mem)


def default_get_throughput(case):
    """
    Parameters
    ----------
    cpllog : str
        Path to the coupler log.

    Returns
    -------
    str
        Last recorded highwater memory usage.
    """
    cpllog = get_latest_cpl_logs(case)

    try:
        tput = get_cpl_throughput(cpllog[0])
    except (FileNotFoundError, IndexError):
        tput = None

    return tput


def default_get_mem_usage(case, cpllog=None):
    """
    Parameters
    ----------
    cpllog : str
        Path to the coupler log.

    Returns
    -------
    str
        Last recorded highwater memory usage.

    Raises
    ------
    RuntimeError
        If not enough sample were found.
    """
    if cpllog is None:
        cpllog = get_latest_cpl_logs(case)
    else:
        cpllog = [
            cpllog,
        ]

    try:
        memlist = get_cpl_mem_usage(cpllog[0])
    except (FileNotFoundError, IndexError):
        memlist = [(None, None)]
    else:
        if len(memlist) <= 3:
            raise RuntimeError(
                f"Found {len(memlist)} memory usage samples, need atleast 4"
            )

    return memlist


def write_baseline_tput(baseline_dir, tput):
    """
    Writes throughput to baseline file.

    The format is arbitrary, it's the callers responsibilty
    to decode the data.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.
    tput : str
        Model throughput.
    """
    tput_file = os.path.join(baseline_dir, "cpl-tput.log")

    with open(tput_file, "w") as fd:
        fd.write(tput)


def write_baseline_mem(baseline_dir, mem):
    """
    Writes memory usage to baseline file.

    The format is arbitrary, it's the callers responsibilty
    to decode the data.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.
    mem : str
        Model memory usage.
    """
    mem_file = os.path.join(baseline_dir, "cpl-mem.log")

    with open(mem_file, "w") as fd:
        fd.write(mem)


def read_baseline_tput(baseline_dir):
    """
    Reads the raw lines of the throughput baseline file.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.

    Returns
    -------
    list
        Contents of the throughput baseline file.

    Raises
    ------
    FileNotFoundError
        If baseline file does not exist.
    """
    return read_baseline_value(os.path.join(baseline_dir, "cpl-tput.log"))


def read_baseline_mem(baseline_dir):
    """
    Read the raw lines of the memory baseline file.

    Parameters
    ----------
    baseline_dir : str
        Path to the baseline directory.

    Returns
    -------
    list
        Contents of the memory baseline file.

    Raises
    ------
    FileNotFoundError
        If baseline file does not exist.
    """
    return read_baseline_value(os.path.join(baseline_dir, "cpl-mem.log"))


def read_baseline_value(baseline_file):
    """
    Generic read function, ignores lines prepended by `#`.

    Parameters
    ----------
    baseline_file : str
        Path to baseline file.

    Returns
    -------
    list
        Lines contained in the baseline file without comments.

    Raises
    ------
    FileNotFoundError
        If ``baseline_file`` is not found.
    """
    with open(baseline_file) as fd:
        lines = [x for x in fd.readlines() if not x.startswith("#")]

    return lines


def get_cpl_mem_usage(cpllog):
    """
    Read memory usage from coupler log.

    Parameters
    ----------
    cpllog : str
        Path to the coupler log.

    Returns
    -------
    list
        Memory usage (data, highwater) as recorded by the coupler or empty list.
    """
    memlist = []

    meminfo = re.compile(r".*model date =\s+(\w+).*memory =\s+(\d+\.?\d+).*highwater")

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


def get_cpl_throughput(cpllog):
    """
    Reads throuhgput from coupler log.

    Parameters
    ----------
    cpllog : str
        Path to the coupler log.

    Returns
    -------
    int or None
        Throughput as recorded by the coupler or None
    """
    if cpllog is not None and os.path.isfile(cpllog):
        with gzip.open(cpllog, "rb") as f:
            cpltext = f.read().decode("utf-8")

            m = re.search(r"# simulated years / cmp-day =\s+(\d+\.\d+)\s", cpltext)

            if m:
                return float(m.group(1))
    return None
