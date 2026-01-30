# pylint: disable=import-error
import queue, os, time, threading, socket, signal, shutil, glob, tempfile
from pathlib import Path

# pylint: disable=import-error
import logging
import xml.etree.ElementTree as xmlet

import CIME.utils
from CIME.utils import expect, Timeout, run_cmd, run_cmd_no_fail, safe_copy, CIMEError
from CIME.XML.machines import Machines
from CIME.test_status import *
from CIME.provenance import save_test_success
from CIME.case.case import Case

SIGNAL_RECEIVED = False
E3SM_MAIN_CDASH = "E3SM"
CDASH_DEFAULT_BUILD_GROUP = "ACME_Latest"
SLEEP_INTERVAL_SEC = 0.1
ENV_VAR_KEEP_CDASH = "CIME_TEST_CDASH_WFT"

###############################################################################
def signal_handler(*_):
    ###############################################################################
    logging.warning("RECEIVED SIGNAL!")
    global SIGNAL_RECEIVED
    SIGNAL_RECEIVED = True


###############################################################################
def set_up_signal_handlers():
    ###############################################################################
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


###############################################################################
def get_test_time(test_path):
    ###############################################################################
    ts = TestStatus(test_dir=test_path)
    comment = ts.get_comment(RUN_PHASE)
    if "time=" not in comment:
        logging.warning("No run-phase time data found in {}".format(test_path))
        return 0
    else:
        time_data = [token for token in comment.split() if token.startswith("time=")][0]
        return int(time_data.split("=")[1])


###############################################################################
def get_test_phase(test_path, phase):
    ###############################################################################
    ts = TestStatus(test_dir=test_path)
    return ts.get_status(phase)


###############################################################################
def get_nml_diff(test_path):
    ###############################################################################
    test_log = os.path.join(test_path, "TestStatus.log")

    diffs = ""
    with open(test_log, "r") as fd:
        started = False
        for line in fd.readlines():
            if "NLCOMP" in line:
                started = True
            elif started:
                if "------------" in line:
                    break
                else:
                    diffs += line

    return diffs


###############################################################################
def get_test_output(test_path):
    ###############################################################################
    output_file = os.path.join(test_path, "TestStatus.log")
    if os.path.exists(output_file):
        return open(output_file, "r").read()
    else:
        logging.warning("File '{}' not found".format(output_file))
        return ""


###############################################################################
def create_cdash_xml_boiler(
    phase,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    current_time,
    hostname,
):
    ###############################################################################
    site_elem = xmlet.Element("Site")

    site_elem.attrib["BuildName"] = cdash_build_name
    site_elem.attrib["BuildStamp"] = "{}-{}".format(utc_time, cdash_build_group)
    site_elem.attrib["Name"] = hostname
    site_elem.attrib["OSName"] = "Linux"
    site_elem.attrib["Hostname"] = hostname
    site_elem.attrib["OSVersion"] = "Unknown"

    phase_elem = xmlet.SubElement(site_elem, phase)

    xmlet.SubElement(phase_elem, "StartDateTime").text = time.ctime(current_time)
    xmlet.SubElement(
        phase_elem, "Start{}Time".format("Test" if phase == "Testing" else phase)
    ).text = str(int(current_time))

    return site_elem, phase_elem


###############################################################################
def create_cdash_config_xml(
    results,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    current_time,
    hostname,
    data_rel_path,
):
    ###############################################################################
    site_elem, config_elem = create_cdash_xml_boiler(
        "Configure",
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
    )

    xmlet.SubElement(config_elem, "ConfigureCommand").text = "namelists"

    config_results = []
    for test_name in sorted(results):
        test_path = results[test_name][0]
        test_norm_path = (
            test_path if os.path.isdir(test_path) else os.path.dirname(test_path)
        )
        nml_phase_result = get_test_phase(test_norm_path, NAMELIST_PHASE)
        if nml_phase_result == TEST_FAIL_STATUS:
            nml_diff = get_nml_diff(test_norm_path)
            cdash_warning = "CMake Warning:\n\n{} NML DIFF:\n{}\n".format(
                test_name, nml_diff
            )
            config_results.append(cdash_warning)

    xmlet.SubElement(config_elem, "Log").text = "\n".join(config_results)

    xmlet.SubElement(config_elem, "ConfigureStatus").text = "0"
    xmlet.SubElement(config_elem, "ElapsedMinutes").text = "0"  # Skip for now

    etree = xmlet.ElementTree(site_elem)
    etree.write(data_rel_path / "Configure.xml")


###############################################################################
def create_cdash_build_xml(
    results,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    current_time,
    hostname,
    data_rel_path,
):
    ###############################################################################
    site_elem, build_elem = create_cdash_xml_boiler(
        "Build",
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
    )

    xmlet.SubElement(build_elem, "ConfigureCommand").text = "case.build"

    build_results = []
    for test_name in sorted(results):
        build_results.append(test_name)

    xmlet.SubElement(build_elem, "Log").text = "\n".join(build_results)

    for idx, test_name in enumerate(sorted(results)):
        test_path, test_status, _ = results[test_name]
        test_norm_path = (
            test_path if os.path.isdir(test_path) else os.path.dirname(test_path)
        )
        if test_status == TEST_FAIL_STATUS and get_test_time(test_norm_path) == 0:
            error_elem = xmlet.SubElement(build_elem, "Error")
            xmlet.SubElement(error_elem, "Text").text = test_name
            xmlet.SubElement(error_elem, "BuildLogLine").text = str(idx)
            xmlet.SubElement(error_elem, "PreContext").text = test_name
            xmlet.SubElement(error_elem, "PostContext").text = ""
            xmlet.SubElement(error_elem, "RepeatCount").text = "0"

    xmlet.SubElement(build_elem, "ElapsedMinutes").text = "0"  # Skip for now

    etree = xmlet.ElementTree(site_elem)
    etree.write(data_rel_path / "Build.xml")


###############################################################################
def create_cdash_test_xml(
    results,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    current_time,
    hostname,
    data_rel_path,
):
    ###############################################################################
    site_elem, testing_elem = create_cdash_xml_boiler(
        "Testing",
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
    )

    test_list_elem = xmlet.SubElement(testing_elem, "TestList")
    for test_name in sorted(results):
        xmlet.SubElement(test_list_elem, "Test").text = test_name

    for test_name in sorted(results):
        test_path, test_status, _ = results[test_name]
        test_passed = test_status in [TEST_PASS_STATUS, NAMELIST_FAIL_STATUS]
        test_norm_path = (
            test_path if os.path.isdir(test_path) else os.path.dirname(test_path)
        )

        full_test_elem = xmlet.SubElement(testing_elem, "Test")
        if test_passed:
            full_test_elem.attrib["Status"] = "passed"
        elif test_status == TEST_PEND_STATUS:
            full_test_elem.attrib["Status"] = "notrun"
        else:
            full_test_elem.attrib["Status"] = "failed"

        xmlet.SubElement(full_test_elem, "Name").text = test_name

        xmlet.SubElement(full_test_elem, "Path").text = test_norm_path

        xmlet.SubElement(full_test_elem, "FullName").text = test_name

        xmlet.SubElement(full_test_elem, "FullCommandLine")
        # text ?

        results_elem = xmlet.SubElement(full_test_elem, "Results")

        named_measurements = (
            ("text/string", "Exit Code", test_status),
            ("text/string", "Exit Value", "0" if test_passed else "1"),
            ("numeric_double", "Execution Time", str(get_test_time(test_norm_path))),
            (
                "text/string",
                "Completion Status",
                "Not Completed" if test_status == TEST_PEND_STATUS else "Completed",
            ),
            ("text/string", "Command line", "create_test"),
        )

        for type_attr, name_attr, value in named_measurements:
            named_measurement_elem = xmlet.SubElement(results_elem, "NamedMeasurement")
            named_measurement_elem.attrib["type"] = type_attr
            named_measurement_elem.attrib["name"] = name_attr

            xmlet.SubElement(named_measurement_elem, "Value").text = value

        measurement_elem = xmlet.SubElement(results_elem, "Measurement")

        value_elem = xmlet.SubElement(measurement_elem, "Value")
        value_elem.text = "".join(
            [item for item in get_test_output(test_norm_path) if ord(item) < 128]
        )

    xmlet.SubElement(testing_elem, "ElapsedMinutes").text = "0"  # Skip for now

    etree = xmlet.ElementTree(site_elem)
    etree.write(data_rel_path / "Test.xml")


###############################################################################
def create_cdash_xml_fakes(
    results,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    current_time,
    hostname,
    data_rel_path,
):
    ###############################################################################

    create_cdash_config_xml(
        results,
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
        data_rel_path,
    )

    create_cdash_build_xml(
        results,
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
        data_rel_path,
    )

    create_cdash_test_xml(
        results,
        cdash_build_name,
        cdash_build_group,
        utc_time,
        current_time,
        hostname,
        data_rel_path,
    )


###############################################################################
def create_cdash_upload_xml(
    results,
    cdash_build_name,
    cdash_build_group,
    utc_time,
    hostname,
    force_log_upload,
    tmp_path,
    data_rel_path,
):
    ###############################################################################

    log_dirname = f"{cdash_build_name}_logs"
    log_path = tmp_path / log_dirname

    need_to_upload = False

    for test_name, test_data in results.items():
        test_path, test_status, _ = test_data

        if test_status != TEST_PASS_STATUS or force_log_upload:
            test_case_dir = os.path.dirname(test_path)

            case_dirs = [test_case_dir]
            case_base = os.path.basename(test_case_dir)
            test_case2_dir = os.path.join(test_case_dir, "case2", case_base)
            if os.path.exists(test_case2_dir):
                case_dirs.append(test_case2_dir)

            for case_dir in case_dirs:
                for param in ["EXEROOT", "RUNDIR", "CASEDIR"]:
                    if param == "CASEDIR":
                        log_src_dir = case_dir
                    else:
                        # it's possible that tests that failed very badly/early, and fake cases for testing
                        # will not be able to support xmlquery
                        try:
                            log_src_dir = run_cmd_no_fail(
                                "./xmlquery {} --value".format(param),
                                from_dir=case_dir,
                            )
                        except CIMEError:
                            continue

                    log_dst_dir = log_path / "{}{}_{}_logs".format(
                        test_name,
                        "" if case_dir == test_case_dir else ".case2",
                        param,
                    )
                    log_dst_dir.mkdir(parents=True)
                    for log_file in glob.glob(os.path.join(log_src_dir, "*log*")):
                        if os.path.isdir(log_file):
                            shutil.copytree(
                                log_file, log_dst_dir / os.path.basename(log_file)
                            )
                        else:
                            safe_copy(log_file, str(log_dst_dir))
                    for log_file in glob.glob(
                        os.path.join(log_src_dir, "*.cprnc.out*")
                    ):
                        safe_copy(log_file, str(log_dst_dir))

            need_to_upload = True

    if need_to_upload:

        tarball = "{}.tar.gz".format(log_dirname)

        run_cmd_no_fail(
            "tar -cf - {} | gzip -c".format(log_dirname),
            arg_stdout=tarball,
            from_dir=str(tmp_path),
        )
        base64 = run_cmd_no_fail("base64 {}".format(tarball), from_dir=str(tmp_path))

        xml_text = r"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="Dart/Source/Server/XSL/Build.xsl <file:///Dart/Source/Server/XSL/Build.xsl> "?>
<Site BuildName="{}" BuildStamp="{}-{}" Name="{}" Generator="ctest3.0.0">
<Upload>
<File filename="{}">
<Content encoding="base64">
{}
</Content>
</File>
</Upload>
</Site>
""".format(
            cdash_build_name,
            utc_time,
            cdash_build_group,
            hostname,
            str((tmp_path / tarball).absolute()),
            base64,
        )

        with (data_rel_path / "Upload.xml").open(mode="w") as fd:
            fd.write(xml_text)


###############################################################################
def create_cdash_xml(
    results,
    cdash_build_name,
    cdash_project,
    cdash_build_group,
    force_log_upload=False,
    cdash_tmproot=None,
):
    ###############################################################################

    #
    # Create dart config file
    #

    current_time = time.time()

    utc_time_tuple = time.gmtime(current_time)
    cdash_timestamp = time.strftime("%H:%M:%S", utc_time_tuple)

    hostname = Machines().get_machine_name()
    if hostname is None:
        hostname = socket.gethostname().split(".")[0]
        logging.warning(
            "Could not convert hostname '{}' into an E3SM machine name".format(hostname)
        )

    # We assume all cases were created from the same code repo
    first_result_case = os.path.dirname(list(results.items())[0][1][0])
    try:
        srcroot = run_cmd_no_fail(
            "./xmlquery --value SRCROOT", from_dir=first_result_case
        )
    except CIMEError:
        # Use repo containing this script as last resort
        srcroot = os.path.join(CIME.utils.get_cime_root(), "..")

    git_commit = CIME.utils.get_current_commit(repo=srcroot)

    # Get total elapsed time
    if "JENKINS_START_TIME" in os.environ:
        time_info = int(current_time) - int(os.environ["JENKINS_START_TIME"])
    else:
        time_info = "unknown"

    if cdash_tmproot:
        tmproots = [cdash_tmproot]
    else:
        tmproots = [None, first_result_case, os.getcwd()]

    # Try multiple tmproots if necessary. The default /tmp will be tried first
    # unless cdash_tmproot was provided. The location of the default can be
    # modified via the TMPDIR environment variable.
    for tmproot in tmproots:
        try:
            with tempfile.TemporaryDirectory(dir=tmproot) as tmpdir:
                tmp_path = Path(tmpdir)
                utc_time = time.strftime("%Y%m%d-%H%M", utc_time_tuple)
                dart_path = tmp_path / "DartConfiguration.tcl"
                testing_path = tmp_path / "Testing"
                testtime_dir = testing_path / utc_time  # Most action happens here
                tag_file = testing_path / "TAG"
                notes_file = tmp_path / "notes.txt"

                testtime_dir.mkdir(parents=True)

                # Make tag file
                with tag_file.open(mode="w") as tag_fd:
                    tag_fd.write(f"{utc_time}\n{cdash_build_group}\n")

                # Make notes file
                with notes_file.open(mode="w") as notes_fd:
                    notes_fd.write(
                        f"Commit {git_commit}\nTotal testing time {time_info} seconds\n"
                    )

                create_cdash_xml_fakes(
                    results,
                    cdash_build_name,
                    cdash_build_group,
                    utc_time,
                    current_time,
                    hostname,
                    testtime_dir,
                )

                create_cdash_upload_xml(
                    results,
                    cdash_build_name,
                    cdash_build_group,
                    utc_time,
                    hostname,
                    force_log_upload,
                    tmp_path,
                    testtime_dir,
                )

                for drop_method in ["https", "http"]:
                    dart_config = """
SourceDirectory: {0}
BuildDirectory: {0}

# Site is something like machine.domain, i.e. pragmatic.crd
Site: {1}

# Build name is osname-revision-compiler, i.e. Linux-2.4.2-2smp-c++
BuildName: {2}

# Submission information
IsCDash: TRUE
CDashVersion:
QueryCDashVersion:
DropSite: my.cdash.org
DropLocation: /submit.php?project={3}
DropSiteUser:
DropSitePassword:
DropSiteMode:
DropMethod: {6}
TriggerSite:
ScpCommand: {4}

# Dashboard start time
NightlyStartTime: {5} UTC

UseLaunchers:
CurlOptions: CURLOPT_SSL_VERIFYPEER_OFF;CURLOPT_SSL_VERIFYHOST_OFF
""".format(
                        str(tmp_path.absolute()),
                        hostname,
                        cdash_build_name,
                        cdash_project,
                        shutil.which("scp"),
                        cdash_timestamp,
                        drop_method,
                    )
                    with dart_path.open(mode="w") as dart_fd:
                        dart_fd.write(dart_config)

                    stat, out, _ = run_cmd(
                        "ctest -VV -D NightlySubmit -A notes.txt",
                        combine_output=True,
                        from_dir=str(tmp_path),
                    )
                    if stat != 0:
                        logging.warning(
                            "ctest upload drop method {} FAILED:\n{}".format(
                                drop_method, out
                            )
                        )
                    else:
                        logging.info("Upload SUCCESS:\n{}".format(out))
                        if ENV_VAR_KEEP_CDASH in os.environ:
                            logging.info(
                                f"Test mode enabled, copying {str(tmp_path)} to {os.getcwd()}"
                            )
                            safe_copy(str(tmp_path / "Testing"), os.getcwd())

                        return

        except Exception as e:
            logging.warning(
                f"Using temp root '{tmproot}', cdash submission failed with error {e}"
            )

    expect(False, "All cdash upload attempts failed")


###############################################################################
def wait_for_test(
    test_path,
    results,
    wait,
    check_throughput,
    check_memory,
    ignore_namelists,
    ignore_diffs,
    ignore_memleak,
    no_run,
):
    ###############################################################################
    if os.path.isdir(test_path):
        test_status_filepath = os.path.join(test_path, TEST_STATUS_FILENAME)
    else:
        test_status_filepath = test_path

    logging.debug("Watching file: '{}'".format(test_status_filepath))
    test_log_path = os.path.join(
        os.path.dirname(test_status_filepath), ".internal_test_status.log"
    )

    # We don't want to make it a requirement that wait_for_tests has write access
    # to all case directories
    try:
        fd = open(test_log_path, "w")
        fd.close()
    except (IOError, OSError):
        test_log_path = "/dev/null"

    prior_ts = None
    with open(test_log_path, "w") as log_fd:
        while True:
            if os.path.exists(test_status_filepath):
                ts = TestStatus(test_dir=os.path.dirname(test_status_filepath))
                test_name = ts.get_name()
                test_status, test_phase = ts.get_overall_test_status(
                    wait_for_run=not no_run,  # Important
                    no_run=no_run,
                    check_throughput=check_throughput,
                    check_memory=check_memory,
                    ignore_namelists=ignore_namelists,
                    ignore_diffs=ignore_diffs,
                    ignore_memleak=ignore_memleak,
                )

                if prior_ts is not None and prior_ts != ts:
                    log_fd.write(ts.phase_statuses_dump())
                    log_fd.write("OVERALL: {}\n\n".format(test_status))

                prior_ts = ts

                if test_status == TEST_PEND_STATUS and (wait and not SIGNAL_RECEIVED):
                    time.sleep(SLEEP_INTERVAL_SEC)
                    logging.debug("Waiting for test to finish")
                else:
                    results.put((test_name, test_path, test_status, test_phase))
                    break

            else:
                if wait and not SIGNAL_RECEIVED:
                    logging.debug(
                        "File '{}' does not yet exist".format(test_status_filepath)
                    )
                    time.sleep(SLEEP_INTERVAL_SEC)
                else:
                    test_name = os.path.abspath(test_status_filepath).split("/")[-2]
                    results.put(
                        (
                            test_name,
                            test_path,
                            "File '{}' doesn't exist".format(test_status_filepath),
                            CREATE_NEWCASE_PHASE,
                        )
                    )
                    break


###############################################################################
def wait_for_tests_impl(
    test_paths,
    no_wait=False,
    check_throughput=False,
    check_memory=False,
    ignore_namelists=False,
    ignore_diffs=False,
    ignore_memleak=False,
    no_run=False,
):
    ###############################################################################
    results = queue.Queue()

    wft_threads = []
    for test_path in test_paths:
        t = threading.Thread(
            target=wait_for_test,
            args=(
                test_path,
                results,
                not no_wait,
                check_throughput,
                check_memory,
                ignore_namelists,
                ignore_diffs,
                ignore_memleak,
                no_run,
            ),
        )
        t.daemon = True
        t.start()
        wft_threads.append(t)

    for wft_thread in wft_threads:
        wft_thread.join()

    test_results = {}
    completed_test_paths = []
    while not results.empty():
        test_name, test_path, test_status, test_phase = results.get()
        if test_name in test_results:
            prior_path, prior_status, _ = test_results[test_name]
            if test_status == prior_status:
                logging.warning(
                    "Test name '{}' was found in both '{}' and '{}'".format(
                        test_name, test_path, prior_path
                    )
                )
            else:
                raise CIMEError(
                    "Test name '{}' was found in both '{}' and '{}' with different results".format(
                        test_name, test_path, prior_path
                    )
                )

        expect(
            test_name is not None,
            "Failed to get test name for test_path: {}".format(test_path),
        )
        test_results[test_name] = (test_path, test_status, test_phase)
        completed_test_paths.append(test_path)

    expect(
        set(test_paths) == set(completed_test_paths),
        "Missing results for test paths: {}".format(
            set(test_paths) - set(completed_test_paths)
        ),
    )
    return test_results


###############################################################################
def wait_for_tests(
    test_paths,
    no_wait=False,
    check_throughput=False,
    check_memory=False,
    ignore_namelists=False,
    ignore_diffs=False,
    ignore_memleak=False,
    cdash_build_name=None,
    cdash_project=E3SM_MAIN_CDASH,
    cdash_tmproot=None,
    cdash_build_group=CDASH_DEFAULT_BUILD_GROUP,
    timeout=None,
    force_log_upload=False,
    no_run=False,
    update_success=False,
    expect_test_complete=True,
):
    ###############################################################################
    # Set up signal handling, we want to print results before the program
    # is terminated
    set_up_signal_handlers()

    with Timeout(timeout, action=signal_handler):
        test_results = wait_for_tests_impl(
            test_paths,
            no_wait,
            check_throughput,
            check_memory,
            ignore_namelists,
            ignore_diffs,
            ignore_memleak,
            no_run,
        )

    all_pass = True
    env_loaded = False
    for test_name, test_data in sorted(test_results.items()):
        test_path, test_status, phase = test_data
        case_dir = os.path.dirname(test_path)

        if test_status not in [
            TEST_PASS_STATUS,
            TEST_PEND_STATUS,
            NAMELIST_FAIL_STATUS,
        ]:
            # Report failed phases
            logging.info("{} {} (phase {})".format(test_status, test_name, phase))
            all_pass = False
        else:
            # Be cautious about telling the user that the test passed since we might
            # not know that the test passed yet.
            if test_status == TEST_PEND_STATUS:
                if expect_test_complete:
                    logging.info(
                        "{} {} (phase {} unexpectedly left in PEND)".format(
                            TEST_PEND_STATUS, test_name, phase
                        )
                    )
                    all_pass = False
                else:
                    logging.info(
                        "{} {} (phase {} has not yet completed)".format(
                            TEST_PEND_STATUS, test_name, phase
                        )
                    )

            elif test_status == NAMELIST_FAIL_STATUS:
                logging.info(
                    "{} {} (but otherwise OK) {}".format(
                        NAMELIST_FAIL_STATUS, test_name, phase
                    )
                )
                all_pass = False
            else:
                expect(
                    test_status == TEST_PASS_STATUS,
                    "Expected pass if we made it here, instead: {}".format(test_status),
                )
                logging.info("{} {} {}".format(test_status, test_name, phase))

        logging.info("    Case dir: {}".format(case_dir))

        if update_success or (cdash_build_name and not env_loaded):
            try:
                # This can fail if the case crashed before setup completed
                with Case(case_dir, read_only=True) as case:
                    srcroot = case.get_value("SRCROOT")
                    baseline_root = case.get_value("BASELINE_ROOT")
                    # Submitting to cdash requires availability of cmake. We can't guarantee
                    # that without loading the env for a case
                    if cdash_build_name and not env_loaded:
                        case.load_env()
                        env_loaded = True

                    if update_success:
                        save_test_success(
                            baseline_root,
                            srcroot,
                            test_name,
                            test_status in [TEST_PASS_STATUS, NAMELIST_FAIL_STATUS],
                        )

            except CIMEError as e:
                logging.warning(
                    "Failed to update success / load_env for Case {}: {}".format(
                        case_dir, e
                    )
                )

    if cdash_build_name:
        create_cdash_xml(
            test_results,
            cdash_build_name,
            cdash_project,
            cdash_build_group,
            force_log_upload,
            cdash_tmproot,
        )

    return all_pass
