"""
Common functions used by cime python scripts
Warning: you cannot use CIME Classes in this module as it causes circular dependencies
"""
import shlex
import configparser
import io, logging, gzip, sys, os, time, re, shutil, glob, string, random, importlib, fnmatch
import importlib.util
import errno, signal, warnings, filecmp
import stat as statlib
from argparse import Action
from contextlib import contextmanager

# pylint: disable=deprecated-module
from distutils import file_util

# Return this error code if the scripts worked but tests failed
TESTS_FAILED_ERR_CODE = 100
logger = logging.getLogger(__name__)

# Fix to pass user defined `srcroot` to `CIME.XML.generic_xml.GenericXML`
# where it's used to resolve $SRCROOT in XML config files.
GLOBAL = {}


def deprecate_action(message):
    class ActionStoreDeprecated(Action):
        def __call__(self, parser, namespace, values, option_string=None):
            raise DeprecationWarning(f"{option_string} is deprecated{message}")

    return ActionStoreDeprecated


def import_from_file(name, file_path):
    loader = importlib.machinery.SourceFileLoader(name, file_path)

    spec = importlib.util.spec_from_loader(loader.name, loader)

    module = importlib.util.module_from_spec(spec)

    sys.modules[name] = module

    spec.loader.exec_module(module)

    return module


@contextmanager
def redirect_stdout(new_target):
    old_target, sys.stdout = sys.stdout, new_target  # replace sys.stdout
    try:
        yield new_target  # run some code with the replaced stdout
    finally:
        sys.stdout = old_target  # restore to the previous value


@contextmanager
def redirect_stderr(new_target):
    old_target, sys.stderr = sys.stderr, new_target  # replace sys.stdout
    try:
        yield new_target  # run some code with the replaced stdout
    finally:
        sys.stderr = old_target  # restore to the previous value


@contextmanager
def redirect_stdout_stderr(new_target):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = new_target, new_target
    try:
        yield new_target
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


@contextmanager
def redirect_logger(new_target, logger_name):
    ch = logging.StreamHandler(stream=new_target)
    ch.setLevel(logging.DEBUG)
    log = logging.getLogger(logger_name)
    root_log = logging.getLogger()
    orig_handlers = log.handlers
    orig_root_loggers = root_log.handlers

    try:
        root_log.handlers = []
        log.handlers = [ch]
        yield log
    finally:
        root_log.handlers = orig_root_loggers
        log.handlers = orig_handlers


class IndentFormatter(logging.Formatter):
    def __init__(self, indent, fmt=None, datefmt=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        self._indent = indent

    def format(self, record):
        record.msg = "{}{}".format(self._indent, record.msg)
        out = logging.Formatter.format(self, record)
        return out


def set_logger_indent(indent):
    root_log = logging.getLogger()
    root_log.handlers = []
    formatter = IndentFormatter(indent)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_log.addHandler(handler)


class EnvironmentContext(object):
    """
    Context manager for environment variables
    Usage:
        os.environ['MYVAR'] = 'oldvalue'
        with EnvironmentContex(MYVAR='myvalue', MYVAR2='myvalue2'):
            print os.getenv('MYVAR')    # Should print myvalue.
            print os.getenv('MYVAR2')    # Should print myvalue2.
        print os.getenv('MYVAR')        # Should print oldvalue.
        print os.getenv('MYVAR2')        # Should print None.

    CREDIT: https://github.com/sakurai-youhei/envcontext
    """

    def __init__(self, **kwargs):
        self.envs = kwargs
        self.old_envs = {}

    def __enter__(self):
        self.old_envs = {}
        for k, v in self.envs.items():
            self.old_envs[k] = os.environ.get(k)
            os.environ[k] = v

    def __exit__(self, *args):
        for k, v in self.old_envs.items():
            if v:
                os.environ[k] = v
            else:
                del os.environ[k]


# This should be the go-to exception for CIME use. It's a subclass
# of SystemExit in order suppress tracebacks, which users generally
# hate seeing. It's a subclass of Exception because we want it to be
# "catchable". If you are debugging CIME and want to see the stacktrace,
# run your CIME command with the --debug flag.
class CIMEError(SystemExit, Exception):
    pass


def expect(condition, error_msg, exc_type=CIMEError, error_prefix="ERROR:"):
    """
    Similar to assert except doesn't generate an ugly stacktrace. Useful for
    checking user error, not programming error.

    >>> expect(True, "error1")
    >>> expect(False, "error2") # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: error2
    """
    # Without this line we get a futurewarning on the use of condition below
    warnings.filterwarnings("ignore")
    if not condition:
        if logger.isEnabledFor(logging.DEBUG):
            import pdb

            pdb.set_trace()  # pylint: disable=forgotten-debug-statement

        msg = error_prefix + " " + error_msg
        raise exc_type(msg)


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def check_name(fullname, additional_chars=None, fullpath=False):
    """
    check for unallowed characters in name, this routine only
    checks the final name and does not check if path exists or is
    writable

    >>> check_name("test.id", additional_chars=".")
    False
    >>> check_name("case.name", fullpath=False)
    True
    >>> check_name("/some/file/path/case.name", fullpath=True)
    True
    >>> check_name("mycase+mods")
    False
    >>> check_name("mycase?mods")
    False
    >>> check_name("mycase*mods")
    False
    >>> check_name("/some/full/path/name/")
    False
    """

    chars = r"+*?<>/{}[\]~`@:"
    if additional_chars is not None:
        chars += additional_chars
    if fullname.endswith("/"):
        return False
    if fullpath:
        _, name = os.path.split(fullname)
    else:
        name = fullname
    match = re.search(r"[" + re.escape(chars) + "]", name)
    if match is not None:
        logger.warning(
            "Illegal character {} found in name {}".format(match.group(0), name)
        )
        return False
    return True


# Should only be called from get_cime_config()
def _read_cime_config_file():
    """
    READ the config file in ~/.cime, this file may contain
    [main]
    CIME_MODEL=e3sm,cesm,ufs
    PROJECT=someprojectnumber
    """
    allowed_sections = ("main", "create_test")

    allowed_in_main = (
        "cime_model",
        "project",
        "charge_account",
        "srcroot",
        "mail_type",
        "mail_user",
        "machine",
        "mpilib",
        "compiler",
        "input_dir",
        "cime_driver",
    )
    allowed_in_create_test = (
        "mail_type",
        "mail_user",
        "save_timing",
        "single_submit",
        "test_root",
        "output_root",
        "baseline_root",
        "clean",
        "machine",
        "mpilib",
        "compiler",
        "parallel_jobs",
        "proc_pool",
        "walltime",
        "job_queue",
        "allow_baseline_overwrite",
        "wait",
        "force_procs",
        "force_threads",
        "input_dir",
        "pesfile",
        "retry",
        "walltime",
    )

    cime_config_file = os.path.abspath(
        os.path.join(os.path.expanduser("~"), ".cime", "config")
    )
    cime_config = configparser.ConfigParser()
    if os.path.isfile(cime_config_file):
        cime_config.read(cime_config_file)
        for section in cime_config.sections():
            expect(
                section in allowed_sections,
                "Unknown section {} in .cime/config\nallowed sections are {}".format(
                    section, allowed_sections
                ),
            )
        if cime_config.has_section("main"):
            for item, _ in cime_config.items("main"):
                expect(
                    item in allowed_in_main,
                    'Unknown option in config section "main": "{}"\nallowed options are {}'.format(
                        item, allowed_in_main
                    ),
                )
        if cime_config.has_section("create_test"):
            for item, _ in cime_config.items("create_test"):
                expect(
                    item in allowed_in_create_test,
                    'Unknown option in config section "test": "{}"\nallowed options are {}'.format(
                        item, allowed_in_create_test
                    ),
                )
    else:
        logger.debug("File {} not found".format(cime_config_file))
        cime_config.add_section("main")

    return cime_config


_CIMECONFIG = None


def get_cime_config():
    global _CIMECONFIG
    if not _CIMECONFIG:
        _CIMECONFIG = _read_cime_config_file()

    return _CIMECONFIG


def reset_cime_config():
    """
    Useful to keep unit tests from interfering with each other
    """
    global _CIMECONFIG
    _CIMECONFIG = None


def copy_local_macros_to_dir(destination, extra_machdir=None):
    """
    Copy any local macros files to the path given by 'destination'.

    Local macros files are potentially found in:
    (1) extra_machdir/cmake_macros/*.cmake
    (2) $HOME/.cime/*.cmake
    """
    local_macros = []
    if extra_machdir:
        if os.path.isdir(os.path.join(extra_machdir, "cmake_macros")):
            local_macros.extend(
                glob.glob(os.path.join(extra_machdir, "cmake_macros/*.cmake"))
            )

    dotcime = None
    home = os.environ.get("HOME")
    if home:
        dotcime = os.path.join(home, ".cime")
    if dotcime and os.path.isdir(dotcime):
        local_macros.extend(glob.glob(dotcime + "/*.cmake"))

    for macro in local_macros:
        safe_copy(macro, destination)


def get_python_libs_location_within_cime():
    """
    From within CIME, return subdirectory of python libraries
    """
    return os.path.join("scripts", "lib")


def get_cime_root(case=None):
    """
    Return the absolute path to the root of CIME that contains this script
    """
    real_file_dir = os.path.dirname(os.path.realpath(__file__))
    cimeroot = os.path.abspath(os.path.join(real_file_dir, ".."))

    if case is not None:
        case_cimeroot = os.path.abspath(case.get_value("CIMEROOT"))
        cimeroot = os.path.abspath(cimeroot)
        expect(
            cimeroot == case_cimeroot,
            "Inconsistent CIMEROOT variable: case -> '{}', file location -> '{}'".format(
                case_cimeroot, cimeroot
            ),
        )

    logger.debug("CIMEROOT is " + cimeroot)
    return cimeroot


def get_config_path():
    cimeroot = get_cime_root()

    return os.path.join(cimeroot, "CIME", "data", "config")


def get_schema_path():
    config_path = get_config_path()

    return os.path.join(config_path, "xml_schemas")


def get_template_path():
    cimeroot = get_cime_root()

    return os.path.join(cimeroot, "CIME", "data", "templates")


def get_tools_path():
    cimeroot = get_cime_root()

    return os.path.join(cimeroot, "CIME", "Tools")


def get_src_root():
    """
    Return the absolute path to the root of SRCROOT.

    """
    cime_config = get_cime_config()

    if "SRCROOT" in os.environ:
        srcroot = os.environ["SRCROOT"]

        logger.debug("SRCROOT from environment: {}".format(srcroot))
    elif cime_config.has_option("main", "SRCROOT"):
        srcroot = cime_config.get("main", "SRCROOT")

        logger.debug("SRCROOT from user config: {}".format(srcroot))
    elif "SRCROOT" in GLOBAL:
        srcroot = GLOBAL["SRCROOT"]

        logger.debug("SRCROOT from internal GLOBAL: {}".format(srcroot))
    else:
        # If the share directory exists in the CIME root then it's
        # assumed it's also the source root. This should only
        # occur when the local "Externals.cfg" is used to install
        # requirements for running/testing without a specific model.
        if os.path.isdir(os.path.join(get_cime_root(), "share")):
            srcroot = os.path.abspath(os.path.join(get_cime_root()))
        else:
            srcroot = os.path.abspath(os.path.join(get_cime_root(), ".."))

        logger.debug("SRCROOT from implicit detection: {}".format(srcroot))

    return srcroot


def get_cime_default_driver():
    driver = os.environ.get("CIME_DRIVER")
    if driver:
        logger.debug("Setting CIME_DRIVER={} from environment".format(driver))
    else:
        cime_config = get_cime_config()
        if cime_config.has_option("main", "CIME_DRIVER"):
            driver = cime_config.get("main", "CIME_DRIVER")
            if driver:
                logger.debug(
                    "Setting CIME_driver={} from ~/.cime/config".format(driver)
                )

    from CIME.config import Config

    config = Config.instance()

    if not driver:
        driver = config.driver_default

    expect(
        driver in config.driver_choices,
        "Attempt to set invalid driver {}".format(driver),
    )
    return driver


def get_all_cime_models():
    config_path = get_config_path()
    models = []

    for entry in os.listdir(config_path):
        if os.path.isdir(os.path.join(config_path, entry)):
            models.append(entry)

    models.remove("xml_schemas")

    return models


def set_model(model):
    """
    Set the model to be used in this session
    """
    cime_config = get_cime_config()
    cime_models = get_all_cime_models()
    if not cime_config.has_section("main"):
        cime_config.add_section("main")
    expect(
        model in cime_models,
        "model {} not recognized. The acceptable values of CIME_MODEL currently are {}".format(
            model, cime_models
        ),
    )
    cime_config.set("main", "CIME_MODEL", model)


def get_model():
    """
    Get the currently configured model value
    The CIME_MODEL env variable may or may not be set

    >>> os.environ["CIME_MODEL"] = "garbage"
    >>> get_model() # doctest:+ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: model garbage not recognized
    >>> del os.environ["CIME_MODEL"]
    >>> set_model('rocky') # doctest:+ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: model rocky not recognized
    >>> set_model('e3sm')
    >>> get_model()
    'e3sm'
    >>> reset_cime_config()
    """
    model = os.environ.get("CIME_MODEL")
    cime_models = get_all_cime_models()
    if model in cime_models:
        logger.debug("Setting CIME_MODEL={} from environment".format(model))
    else:
        expect(
            model is None,
            "model {} not recognized. The acceptable values of CIME_MODEL currently are {}".format(
                model, cime_models
            ),
        )
        cime_config = get_cime_config()
        if cime_config.has_option("main", "CIME_MODEL"):
            model = cime_config.get("main", "CIME_MODEL")
            if model is not None:
                logger.debug("Setting CIME_MODEL={} from ~/.cime/config".format(model))

    # One last try
    if model is None:
        srcroot = get_src_root()

        if os.path.isfile(os.path.join(srcroot, "Externals.cfg")):
            model = "cesm"
            with open(os.path.join(srcroot, "Externals.cfg")) as fd:
                for line in fd:
                    if re.search("ufs", line):
                        model = "ufs"
        else:
            model = "e3sm"
        # This message interfers with the correct operation of xmlquery
        # logger.debug("Guessing CIME_MODEL={}, set environment variable if this is incorrect".format(model))

    if model is not None:
        set_model(model)
        return model

    modelroot = os.path.join(get_cime_root(), "CIME", "config")
    models = os.listdir(modelroot)
    msg = ".cime/config or environment variable CIME_MODEL must be set to one of: "
    msg += ", ".join(
        [
            model
            for model in models
            if os.path.isdir(os.path.join(modelroot, model)) and model != "xml_schemas"
        ]
    )
    expect(False, msg)


def _get_path(filearg, from_dir):
    if not filearg.startswith("/") and from_dir is not None:
        filearg = os.path.join(from_dir, filearg)

    return filearg


def _convert_to_fd(filearg, from_dir, mode="a"):
    filearg = _get_path(filearg, from_dir)

    return open(filearg, mode)


_hack = object()


def _line_defines_python_function(line, funcname):
    """Returns True if the given line defines the function 'funcname' as a top-level definition

    ("top-level definition" means: not something like a class method; i.e., the def should
    be at the start of the line, not indented)

    """
    if re.search(r"^def\s+{}\s*\(".format(funcname), line) or re.search(
        r"^from\s.+\simport.*\s{}(?:,|\s|$)".format(funcname), line
    ):
        return True
    return False


def file_contains_python_function(filepath, funcname):
    """Checks whether the given file contains a top-level definition of the function 'funcname'

    Returns a boolean value (True if the file contains this function definition, False otherwise)
    """
    has_function = False
    with open(filepath, "r") as fd:
        for line in fd.readlines():
            if _line_defines_python_function(line, funcname):
                has_function = True
                break

    return has_function


def fixup_sys_path(*additional_paths):
    cimeroot = get_cime_root()

    if cimeroot not in sys.path or sys.path.index(cimeroot) > 0:
        sys.path.insert(0, cimeroot)

    tools_path = get_tools_path()

    if tools_path not in sys.path or sys.path.index(tools_path) > 1:
        sys.path.insert(1, tools_path)

    for i, x in enumerate(additional_paths):
        if x not in sys.path or sys.path.index(x) > 2 + i:
            sys.path.insert(2 + i, x)


def import_and_run_sub_or_cmd(
    cmd,
    cmdargs,
    subname,
    subargs,
    config_dir,
    compname,
    logfile=None,
    case=None,
    from_dir=None,
    timeout=None,
):
    sys_path_old = sys.path
    # ensure we provide `get_src_root()` and `get_tools_path()` to sys.path
    # allowing imported modules to correctly import `CIME` module or any
    # tool under `CIME/Tools`.
    fixup_sys_path(config_dir)
    try:
        mod = importlib.import_module(f"{compname}_cime_py")
        getattr(mod, subname)(*subargs)
    except (ModuleNotFoundError, AttributeError) as e:
        # * ModuleNotFoundError if importlib can not find module,
        # * AttributeError if importlib finds the module but
        #   {subname} is not defined in the module
        expect(
            os.path.isfile(cmd),
            f"Could not find {subname} file for component {compname}",
        )

        # TODO shouldn't need to use logger.isEnabledFor for debug logging
        if isinstance(e, ModuleNotFoundError) and logger.isEnabledFor(logging.DEBUG):
            logger.info(
                "WARNING: Could not import module '{}_cime_py'".format(compname)
            )

        try:
            run_sub_or_cmd(
                cmd, cmdargs, subname, subargs, logfile, case, from_dir, timeout
            )
        except Exception as e1:
            raise e1 from None
    except Exception:
        if logfile:
            with open(logfile, "a") as log_fd:
                log_fd.write(str(sys.exc_info()[1]))
            expect(False, "{} FAILED, cat {}".format(cmd, logfile))
        else:
            raise
    sys.path = sys_path_old


def run_sub_or_cmd(
    cmd, cmdargs, subname, subargs, logfile=None, case=None, from_dir=None, timeout=None
):
    """
    This code will try to import and run each cmd as a subroutine
    if that fails it will run it as a program in a seperate shell

    Raises exception on failure.
    """
    if file_contains_python_function(cmd, subname):
        do_run_cmd = False
    else:
        do_run_cmd = True

    if not do_run_cmd:
        # ensure we provide `get_src_root()` and `get_tools_path()` to sys.path
        # allowing imported modules to correctly import `CIME` module or any
        # tool under `CIME/Tools`.
        fixup_sys_path()

        try:
            mod = import_from_file(subname, cmd)
            logger.info("   Calling {}".format(cmd))
            # Careful: logfile code is not thread safe!
            if logfile:
                with open(logfile, "w") as log_fd:
                    with redirect_logger(log_fd, subname):
                        with redirect_stdout_stderr(log_fd):
                            getattr(mod, subname)(*subargs)
            else:
                getattr(mod, subname)(*subargs)

        except (SyntaxError, AttributeError) as _:
            pass  # Need to try to run as shell command

        except Exception:
            if logfile:
                with open(logfile, "a") as log_fd:
                    log_fd.write(str(sys.exc_info()[1]))

                expect(False, "{} FAILED, cat {}".format(cmd, logfile))
            else:
                raise

        else:
            return  # Running as python function worked, we're done

    logger.info("   Running {} ".format(cmd))
    if case is not None:
        case.flush()

    fullcmd = cmd
    if isinstance(cmdargs, list):
        for arg in cmdargs:
            fullcmd += " " + str(arg)
    else:
        fullcmd += " " + cmdargs

    if logfile:
        fullcmd += " >& {} ".format(logfile)

    stat, output, _ = run_cmd(
        "{}".format(fullcmd), combine_output=True, from_dir=from_dir, timeout=timeout
    )
    if output:  # Will be empty if logfile
        logger.info(output)

    if stat != 0:
        if logfile:
            expect(False, "{} FAILED, cat {}".format(fullcmd, logfile))
        else:
            expect(False, "{} FAILED, see above".format(fullcmd))

    # refresh case xml object from file
    if case is not None:
        case.read_xml()


def run_cmd(
    cmd,
    input_str=None,
    from_dir=None,
    verbose=None,
    arg_stdout=_hack,
    arg_stderr=_hack,
    env=None,
    combine_output=False,
    timeout=None,
    executable=None,
    shell=True,
):
    """
    Wrapper around subprocess to make it much more convenient to run shell commands

    >>> run_cmd('ls file_i_hope_doesnt_exist')[0] != 0
    True
    """
    import subprocess  # Not safe to do globally, module not available in older pythons

    # Real defaults for these value should be subprocess.PIPE
    if arg_stdout is _hack:
        arg_stdout = subprocess.PIPE
    elif isinstance(arg_stdout, str):
        arg_stdout = _convert_to_fd(arg_stdout, from_dir)

    if arg_stderr is _hack:
        arg_stderr = subprocess.STDOUT if combine_output else subprocess.PIPE
    elif isinstance(arg_stderr, str):
        arg_stderr = _convert_to_fd(arg_stdout, from_dir)

    if verbose != False and (verbose or logger.isEnabledFor(logging.DEBUG)):
        logger.info(
            "RUN: {}\nFROM: {}".format(
                cmd, os.getcwd() if from_dir is None else from_dir
            )
        )

    if input_str is not None:
        stdin = subprocess.PIPE
    else:
        stdin = None

    if not shell:
        cmd = shlex.split(cmd)

    # ensure we have an environment to use if not being over written by parent
    if env is None:
        # persist current environment
        env = os.environ.copy()

    # Always provide these variables for anything called externally.
    # `CIMEROOT` is provided for external scripts, makefiles, etc that
    # may reference it. `PYTHONPATH` is provided to ensure external
    # python can correctly import the CIME module and anything under
    # `CIME/tools`.
    #
    # `get_tools_path()` is provided for backwards compatibility.
    # External python prior to the CIME module move would use `CIMEROOT`
    # or build a relative path and append `sys.path` to import
    # `standard_script_setup`. Providing `PYTHONPATH` fixes protential
    # broken paths in external python.
    env.update(
        {
            "CIMEROOT": f"{get_cime_root()}",
            "PYTHONPATH": f"{get_cime_root()}:{get_tools_path()}",
        }
    )

    if timeout:
        with Timeout(timeout):
            proc = subprocess.Popen(
                cmd,
                shell=shell,
                stdout=arg_stdout,
                stderr=arg_stderr,
                stdin=stdin,
                cwd=from_dir,
                executable=executable,
                env=env,
            )

            output, errput = proc.communicate(input_str)
    else:
        proc = subprocess.Popen(
            cmd,
            shell=shell,
            stdout=arg_stdout,
            stderr=arg_stderr,
            stdin=stdin,
            cwd=from_dir,
            executable=executable,
            env=env,
        )

        output, errput = proc.communicate(input_str)

    # In Python3, subprocess.communicate returns bytes. We want to work with strings
    # as much as possible, so we convert bytes to string (which is unicode in py3) via
    # decode. For python2, we do NOT want to do this since decode will yield unicode
    # strings which are not necessarily compatible with the system's default base str type.
    if output is not None:
        try:
            output = output.decode("utf-8", errors="ignore")
        except AttributeError:
            pass
    if errput is not None:
        try:
            errput = errput.decode("utf-8", errors="ignore")
        except AttributeError:
            pass

    # Always strip outputs
    if output:
        output = output.strip()
    if errput:
        errput = errput.strip()

    stat = proc.wait()
    if isinstance(arg_stdout, io.IOBase):
        arg_stdout.close()  # pylint: disable=no-member
    if isinstance(arg_stderr, io.IOBase) and arg_stderr is not arg_stdout:
        arg_stderr.close()  # pylint: disable=no-member

    if verbose != False and (verbose or logger.isEnabledFor(logging.DEBUG)):
        if stat != 0:
            logger.info("  stat: {:d}\n".format(stat))
        if output:
            logger.info("  output: {}\n".format(output))
        if errput:
            logger.info("  errput: {}\n".format(errput))

    return stat, output, errput


def run_cmd_no_fail(
    cmd,
    input_str=None,
    from_dir=None,
    verbose=None,
    arg_stdout=_hack,
    arg_stderr=_hack,
    env=None,
    combine_output=False,
    timeout=None,
    executable=None,
):
    """
    Wrapper around subprocess to make it much more convenient to run shell commands.
    Expects command to work. Just returns output string.

    >>> run_cmd_no_fail('echo foo') == 'foo'
    True
    >>> run_cmd_no_fail('echo THE ERROR >&2; false') # doctest:+ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: Command: 'echo THE ERROR >&2; false' failed with error ...

    >>> run_cmd_no_fail('grep foo', input_str=b'foo') == 'foo'
    True
    >>> run_cmd_no_fail('echo THE ERROR >&2', combine_output=True) == 'THE ERROR'
    True
    """
    stat, output, errput = run_cmd(
        cmd,
        input_str,
        from_dir,
        verbose,
        arg_stdout,
        arg_stderr,
        env,
        combine_output,
        executable=executable,
        timeout=timeout,
    )
    if stat != 0:
        # If command produced no errput, put output in the exception since we
        # have nothing else to go on.
        errput = output if not errput else errput
        if errput is None:
            if combine_output:
                if isinstance(arg_stdout, str):
                    errput = "See {}".format(_get_path(arg_stdout, from_dir))
                else:
                    errput = ""
            elif isinstance(arg_stderr, str):
                errput = "See {}".format(_get_path(arg_stderr, from_dir))
            else:
                errput = ""

        expect(
            False,
            "Command: '{}' failed with error '{}' from dir '{}'".format(
                cmd, errput, os.getcwd() if from_dir is None else from_dir
            ),
        )

    return output


def normalize_case_id(case_id):
    """
    Given a case_id, return it in form TESTCASE.GRID.COMPSET.PLATFORM

    >>> normalize_case_id('ERT.ne16_g37.B1850C5.sandiatoss3_intel')
    'ERT.ne16_g37.B1850C5.sandiatoss3_intel'
    >>> normalize_case_id('ERT.ne16_g37.B1850C5.sandiatoss3_intel.test-mod')
    'ERT.ne16_g37.B1850C5.sandiatoss3_intel.test-mod'
    >>> normalize_case_id('ERT.ne16_g37.B1850C5.sandiatoss3_intel.G.20151121')
    'ERT.ne16_g37.B1850C5.sandiatoss3_intel'
    >>> normalize_case_id('ERT.ne16_g37.B1850C5.sandiatoss3_intel.test-mod.G.20151121')
    'ERT.ne16_g37.B1850C5.sandiatoss3_intel.test-mod'
    """
    sep_count = case_id.count(".")
    expect(
        sep_count >= 3 and sep_count <= 6,
        "Case '{}' needs to be in form: TESTCASE.GRID.COMPSET.PLATFORM[.TESTMOD]  or  TESTCASE.GRID.COMPSET.PLATFORM[.TESTMOD].GC.TESTID".format(
            case_id
        ),
    )
    if sep_count in [5, 6]:
        return ".".join(case_id.split(".")[:-2])
    else:
        return case_id


def parse_test_name(test_name):
    """
    Given a CIME test name TESTCASE[_CASEOPTS].GRID.COMPSET[.MACHINE_COMPILER[.TESTMODS]],
    return each component of the testname with machine and compiler split.
    Do not error if a partial testname is provided (TESTCASE or TESTCASE.GRID) instead
    parse and return the partial results.

    TESTMODS use hyphens in a special way:
    - A single hyphen stands for a path separator (for example, 'test-mods' resolves to
      the path 'test/mods')
    - A double hyphen separates multiple test mods (for example, 'test-mods--other-dir-path'
      indicates two test mods: 'test/mods' and 'other/dir/path')

    If there are one or more TESTMODS, then the testmods component of the result will be a
    list, where each element of the list is one testmod, and hyphens have been replaced by
    slashes. (If there are no TESTMODS in this test, then the TESTMODS component of the
    result is None, as for other optional components.)

    >>> parse_test_name('ERS')
    ['ERS', None, None, None, None, None, None]
    >>> parse_test_name('ERS.fe12_123')
    ['ERS', None, 'fe12_123', None, None, None, None]
    >>> parse_test_name('ERS.fe12_123.JGF')
    ['ERS', None, 'fe12_123', 'JGF', None, None, None]
    >>> parse_test_name('ERS_D.fe12_123.JGF')
    ['ERS', ['D'], 'fe12_123', 'JGF', None, None, None]
    >>> parse_test_name('ERS_D_P1.fe12_123.JGF')
    ['ERS', ['D', 'P1'], 'fe12_123', 'JGF', None, None, None]
    >>> parse_test_name('ERS_D_G2.fe12_123.JGF')
    ['ERS', ['D', 'G2'], 'fe12_123', 'JGF', None, None, None]
    >>> parse_test_name('SMS_D_Ln9_Mmpi-serial.f19_g16_rx1.A')
    ['SMS', ['D', 'Ln9', 'Mmpi-serial'], 'f19_g16_rx1', 'A', None, None, None]
    >>> parse_test_name('ERS.fe12_123.JGF.machine_compiler')
    ['ERS', None, 'fe12_123', 'JGF', 'machine', 'compiler', None]
    >>> parse_test_name('ERS.fe12_123.JGF.machine_compiler.test-mods')
    ['ERS', None, 'fe12_123', 'JGF', 'machine', 'compiler', ['test/mods']]
    >>> parse_test_name('ERS.fe12_123.JGF.*_compiler.test-mods')
    ['ERS', None, 'fe12_123', 'JGF', None, 'compiler', ['test/mods']]
    >>> parse_test_name('ERS.fe12_123.JGF.machine_*.test-mods')
    ['ERS', None, 'fe12_123', 'JGF', 'machine', None, ['test/mods']]
    >>> parse_test_name('ERS.fe12_123.JGF.*_*.test-mods')
    ['ERS', None, 'fe12_123', 'JGF', None, None, ['test/mods']]
    >>> parse_test_name('ERS.fe12_123.JGF.machine_compiler.test-mods--other-dir-path--and-one-more')
    ['ERS', None, 'fe12_123', 'JGF', 'machine', 'compiler', ['test/mods', 'other/dir/path', 'and/one/more']]
    >>> parse_test_name('SMS.f19_g16.2000_DATM%QI.A_XLND_SICE_SOCN_XROF_XGLC_SWAV.mach-ine_compiler.test-mods') # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: Expected 4th item of 'SMS.f19_g16.2000_DATM%QI.A_XLND_SICE_SOCN_XROF_XGLC_SWAV.mach-ine_compiler.test-mods' ('A_XLND_SICE_SOCN_XROF_XGLC_SWAV') to be in form machine_compiler
    >>> parse_test_name('SMS.f19_g16.2000_DATM%QI/A_XLND_SICE_SOCN_XROF_XGLC_SWAV.mach-ine_compiler.test-mods') # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    CIMEError: ERROR: Invalid compset name 2000_DATM%QI/A_XLND_SICE_SOCN_XROF_XGLC_SWAV
    """
    rv = [None] * 7
    num_dots = test_name.count(".")

    rv[0 : num_dots + 1] = test_name.split(".")
    testcase_field_underscores = rv[0].count("_")
    rv.insert(1, None)  # Make room for caseopts
    rv.pop()
    if testcase_field_underscores > 0:
        full_str = rv[0]
        rv[0] = full_str.split("_")[0]
        rv[1] = full_str.split("_")[1:]

    if num_dots >= 3:
        expect(check_name(rv[3]), "Invalid compset name {}".format(rv[3]))

        expect(
            rv[4].count("_") == 1,
            "Expected 4th item of '{}' ('{}') to be in form machine_compiler".format(
                test_name, rv[4]
            ),
        )
        rv[4:5] = rv[4].split("_")
        if rv[4] == "*":
            rv[4] = None
        if rv[5] == "*":
            rv[5] = None
        rv.pop()

    if rv[-1] is not None:
        # The last element of the return value - testmods - will be a list of testmods,
        # built by separating the TESTMODS component on strings of double hyphens
        testmods = rv[-1].split("--")
        rv[-1] = [one_testmod.replace("-", "/") for one_testmod in testmods]

    expect(
        num_dots <= 4,
        "'{}' does not look like a CIME test name, expect TESTCASE.GRID.COMPSET[.MACHINE_COMPILER[.TESTMODS]]".format(
            test_name
        ),
    )

    return rv


def get_full_test_name(
    partial_test,
    caseopts=None,
    grid=None,
    compset=None,
    machine=None,
    compiler=None,
    testmods_list=None,
    testmods_string=None,
):
    """
    Given a partial CIME test name, return in form TESTCASE.GRID.COMPSET.MACHINE_COMPILER[.TESTMODS]
    Use the additional args to fill out the name if needed

    Testmods can be provided through one of two arguments, but *not* both:
    - testmods_list: a list of one or more testmods (as would be returned by
      parse_test_name, for example)
    - testmods_string: a single string containing one or more testmods; if there is more
      than one, then they should be separated by a string of two hyphens ('--')

    For both testmods_list and testmods_string, any slashes as path separators ('/') are
    replaced by hyphens ('-').

    >>> get_full_test_name("ERS", grid="ne16_fe16", compset="JGF", machine="melvin", compiler="gnu")
    'ERS.ne16_fe16.JGF.melvin_gnu'
    >>> get_full_test_name("ERS", caseopts=["D", "P16"], grid="ne16_fe16", compset="JGF", machine="melvin", compiler="gnu")
    'ERS_D_P16.ne16_fe16.JGF.melvin_gnu'
    >>> get_full_test_name("ERS.ne16_fe16", compset="JGF", machine="melvin", compiler="gnu")
    'ERS.ne16_fe16.JGF.melvin_gnu'
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu")
    'ERS.ne16_fe16.JGF.melvin_gnu'
    >>> get_full_test_name("ERS.ne16_fe16.JGF.melvin_gnu.mods", machine="melvin", compiler="gnu")
    'ERS.ne16_fe16.JGF.melvin_gnu.mods'

    testmods_list can be a single element:
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_list=["mods/test"])
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test'

    testmods_list can also have multiple elements, separated either by slashes or hyphens:
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_list=["mods/test", "mods2/test2/subdir2", "mods3/test3/subdir3"])
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3'
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_list=["mods-test", "mods2-test2-subdir2", "mods3-test3-subdir3"])
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3'

    The above testmods_list tests should also work with equivalent testmods_string arguments:
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_string="mods/test")
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test'
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_string="mods/test--mods2/test2/subdir2--mods3/test3/subdir3")
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3'
    >>> get_full_test_name("ERS.ne16_fe16.JGF", machine="melvin", compiler="gnu", testmods_string="mods-test--mods2-test2-subdir2--mods3-test3-subdir3")
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3'

    The following tests the consistency check between the test name and various optional arguments:
    >>> get_full_test_name("ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3", machine="melvin", compiler="gnu", testmods_list=["mods/test", "mods2/test2/subdir2", "mods3/test3/subdir3"])
    'ERS.ne16_fe16.JGF.melvin_gnu.mods-test--mods2-test2-subdir2--mods3-test3-subdir3'
    """
    (
        partial_testcase,
        partial_caseopts,
        partial_grid,
        partial_compset,
        partial_machine,
        partial_compiler,
        partial_testmods,
    ) = parse_test_name(partial_test)

    required_fields = [
        (partial_grid, grid, "grid"),
        (partial_compset, compset, "compset"),
        (partial_machine, machine, "machine"),
        (partial_compiler, compiler, "compiler"),
    ]

    result = partial_test
    for partial_val, arg_val, name in required_fields:
        if partial_val is None:
            # Add to result based on args
            expect(
                arg_val is not None,
                "Could not fill-out test name, partial string '{}' had no {} information and you did not provide any".format(
                    partial_test, name
                ),
            )
            if name == "machine" and "*_" in result:
                result = result.replace("*_", arg_val + "_")
            elif name == "compiler" and "_*" in result:
                result = result.replace("_*", "_" + arg_val)
            else:
                result = "{}{}{}".format(
                    result, "_" if name == "compiler" else ".", arg_val
                )
        elif arg_val is not None and partial_val != partial_compiler:
            expect(
                arg_val == partial_val,
                "Mismatch in field {}, partial string '{}' indicated it should be '{}' but you provided '{}'".format(
                    name, partial_test, partial_val, arg_val
                ),
            )

    if testmods_string is not None:
        expect(
            testmods_list is None,
            "Cannot provide both testmods_list and testmods_string",
        )
        # Convert testmods_string to testmods_list; after this point, the code will work
        # the same regardless of whether testmods_string or testmods_list was provided.
        testmods_list = testmods_string.split("--")
    if partial_testmods is None:
        if testmods_list is None:
            # No testmods for this test and that's OK
            pass
        else:
            testmods_hyphenated = [
                one_testmod.replace("/", "-") for one_testmod in testmods_list
            ]
            result += ".{}".format("--".join(testmods_hyphenated))
    elif testmods_list is not None:
        expect(
            testmods_list == partial_testmods,
            "Mismatch in field testmods, partial string '{}' indicated it should be '{}' but you provided '{}'".format(
                partial_test, partial_testmods, testmods_list
            ),
        )

    if partial_caseopts is None:
        if caseopts is None:
            # No casemods for this test and that's OK
            pass
        else:
            result = result.replace(
                partial_testcase,
                "{}_{}".format(partial_testcase, "_".join(caseopts)),
                1,
            )
    elif caseopts is not None:
        expect(
            caseopts == partial_caseopts,
            "Mismatch in field caseopts, partial string '{}' indicated it should be '{}' but you provided '{}'".format(
                partial_test, partial_caseopts, caseopts
            ),
        )

    return result


def get_current_branch(repo=None):
    """
    Return the name of the current branch for a repository

    >>> if "GIT_BRANCH" in os.environ:
    ...     get_current_branch() is not None
    ... else:
    ...     os.environ["GIT_BRANCH"] = "foo"
    ...     get_current_branch() == "foo"
    True
    """
    if "GIT_BRANCH" in os.environ:
        # This approach works better for Jenkins jobs because the Jenkins
        # git plugin does not use local tracking branches, it just checks out
        # to a commit
        branch = os.environ["GIT_BRANCH"]
        if branch.startswith("origin/"):
            branch = branch.replace("origin/", "", 1)
        return branch
    else:
        stat, output, _ = run_cmd("git symbolic-ref HEAD", from_dir=repo)
        if stat != 0:
            return None
        else:
            return output.replace("refs/heads/", "")


def get_current_commit(short=False, repo=None, tag=False):
    """
    Return the sha1 of the current HEAD commit

    >>> get_current_commit() is not None
    True
    """
    if tag:
        rc, output, _ = run_cmd(
            "git describe --tags $(git log -n1 --pretty='%h')", from_dir=repo
        )
    else:
        rc, output, _ = run_cmd(
            "git rev-parse {} HEAD".format("--short" if short else ""), from_dir=repo
        )

    return output if rc == 0 else "unknown"


def get_model_config_location_within_cime(model=None):
    model = get_model() if model is None else model
    return os.path.join("config", model)


def get_scripts_root():
    """
    Get absolute path to scripts

    >>> os.path.isdir(get_scripts_root())
    True
    """
    return os.path.join(get_cime_root(), "scripts")


def get_model_config_root(model=None):
    """
    Get absolute path to model config area"

    >>> os.environ["CIME_MODEL"] = "e3sm" # Set the test up don't depend on external resources
    >>> os.path.isdir(get_model_config_root())
    True
    """
    model = get_model() if model is None else model
    return os.path.join(
        get_cime_root(), "CIME", "data", get_model_config_location_within_cime(model)
    )


def stop_buffering_output():
    """
    All stdout, stderr will not be buffered after this is called.
    """
    os.environ["PYTHONUNBUFFERED"] = "1"


def start_buffering_output():
    """
    All stdout, stderr will be buffered after this is called. This is python's
    default behavior.
    """
    sys.stdout.flush()
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w")


def match_any(item, re_counts):
    """
    Return true if item matches any regex in re_counts' keys. Increments
    count if a match was found.
    """
    for regex_str in re_counts:
        regex = re.compile(regex_str)
        if regex.match(item):
            re_counts[regex_str] += 1
            return True

    return False


def get_current_submodule_status(recursive=False, repo=None):
    """
    Return the sha1s of the current currently checked out commit for each submodule,
    along with the submodule path and the output of git describe for the SHA-1.

    >>> get_current_submodule_status() is not None
    True
    """
    rc, output, _ = run_cmd(
        "git submodule status {}".format("--recursive" if recursive else ""),
        from_dir=repo,
    )

    return output if rc == 0 else "unknown"


def copy_globs(globs_to_copy, output_directory, lid=None):
    """
    Takes a list of globs and copies all files to `output_directory`.

    Hiddens files become unhidden i.e. removing starting dot.

    Output filename is derviced from the basename of the input path and can
    be appended with the `lid`.

    """
    for glob_to_copy in globs_to_copy:
        for item in glob.glob(glob_to_copy):
            item_basename = os.path.basename(item).lstrip(".")

            if lid is None:
                filename = item_basename
            else:
                filename = f"{item_basename}.{lid}"

            safe_copy(
                item, os.path.join(output_directory, filename), preserve_meta=False
            )


def safe_copy(src_path, tgt_path, preserve_meta=True):
    """
    A flexbile and safe copy routine. Will try to copy file and metadata, but this
    can fail if the current user doesn't own the tgt file. A fallback data-only copy is
    attempted in this case. Works even if overwriting a read-only file.

    tgt_path can be a directory, src_path must be a file

    most of the complexity here is handling the case where the tgt_path file already
    exists. This problem does not exist for the tree operations so we don't need to wrap those.

    preserve_meta toggles if file meta-data, like permissions, should be preserved. If you are
    copying baseline files, you should be within a SharedArea context manager and preserve_meta
    should be false so that the umask set up by SharedArea can take affect regardless of the
    permissions of the src files.
    """

    tgt_path = (
        os.path.join(tgt_path, os.path.basename(src_path))
        if os.path.isdir(tgt_path)
        else tgt_path
    )

    # Handle pre-existing file
    if os.path.isfile(tgt_path):
        st = os.stat(tgt_path)
        owner_uid = st.st_uid

        # Handle read-only files if possible
        if not os.access(tgt_path, os.W_OK):
            if owner_uid == os.getuid():
                # I am the owner, make writeable
                os.chmod(tgt_path, st.st_mode | statlib.S_IWRITE)
            else:
                # I won't be able to copy this file
                raise OSError(
                    "Cannot copy over file {}, it is readonly and you are not the owner".format(
                        tgt_path
                    )
                )

        if owner_uid == os.getuid():
            # I am the owner, copy file contents, permissions, and metadata
            file_util.copy_file(
                src_path,
                tgt_path,
                preserve_mode=preserve_meta,
                preserve_times=preserve_meta,
                verbose=0,
            )
        else:
            # I am not the owner, just copy file contents
            shutil.copyfile(src_path, tgt_path)

    else:
        # We are making a new file, copy file contents, permissions, and metadata.
        # This can fail if the underlying directory is not writable by current user.
        file_util.copy_file(
            src_path,
            tgt_path,
            preserve_mode=preserve_meta,
            preserve_times=preserve_meta,
            verbose=0,
        )

    # If src file was executable, then the tgt file should be too
    st = os.stat(tgt_path)
    if os.access(src_path, os.X_OK) and st.st_uid == os.getuid():
        os.chmod(
            tgt_path, st.st_mode | statlib.S_IXUSR | statlib.S_IXGRP | statlib.S_IXOTH
        )


def safe_recursive_copy(src_dir, tgt_dir, file_map):
    """
    Copies a set of files from one dir to another. Works even if overwriting a
    read-only file. Files can be relative paths and the relative path will be
    matched on the tgt side.
    """
    for src_file, tgt_file in file_map:
        full_tgt = os.path.join(tgt_dir, tgt_file)
        full_src = (
            src_file if os.path.isabs(src_file) else os.path.join(src_dir, src_file)
        )
        expect(
            os.path.isfile(full_src),
            "Source dir '{}' missing file '{}'".format(src_dir, src_file),
        )
        safe_copy(full_src, full_tgt)


def symlink_force(target, link_name):
    """
    Makes a symlink from link_name to target. Unlike the standard
    os.symlink, this will work even if link_name already exists (in
    which case link_name will be overwritten).
    """
    try:
        os.symlink(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e


def find_proc_id(proc_name=None, children_only=False, of_parent=None):
    """
    Children implies recursive.
    """
    expect(
        proc_name is not None or children_only,
        "Must provide proc_name if not searching for children",
    )
    expect(
        not (of_parent is not None and not children_only),
        "of_parent only used with children_only",
    )

    parent = of_parent if of_parent is not None else os.getpid()

    pgrep_cmd = "pgrep {} {}".format(
        proc_name if proc_name is not None else "",
        "-P {:d}".format(parent if children_only else ""),
    )
    stat, output, errput = run_cmd(pgrep_cmd)
    expect(stat in [0, 1], "pgrep failed with error: '{}'".format(errput))

    rv = set([int(item.strip()) for item in output.splitlines()])
    if children_only:
        pgrep_cmd = "pgrep -P {}".format(parent)
        stat, output, errput = run_cmd(pgrep_cmd)
        expect(stat in [0, 1], "pgrep failed with error: '{}'".format(errput))

        for child in output.splitlines():
            rv = rv.union(
                set(find_proc_id(proc_name, children_only, int(child.strip())))
            )

    return list(rv)


def get_timestamp(timestamp_format="%Y%m%d_%H%M%S", utc_time=False):
    """
    Get a string representing the current UTC time in format: YYYYMMDD_HHMMSS

    The format can be changed if needed.
    """
    if utc_time:
        time_tuple = time.gmtime()
    else:
        time_tuple = time.localtime()
    return time.strftime(timestamp_format, time_tuple)


def get_project(machobj=None):
    """
    Hierarchy for choosing PROJECT:
    0. Command line flag to create_newcase or create_test
    1. Environment variable PROJECT
    2  Environment variable ACCOUNT  (this is for backward compatibility)
    3. File $HOME/.cime/config       (this is new)
    4  File $HOME/.cesm_proj         (this is for backward compatibility)
    5  config_machines.xml (if machobj provided)
    """
    project = os.environ.get("PROJECT")
    if project is not None:
        logger.info("Using project from env PROJECT: " + project)
        return project
    project = os.environ.get("ACCOUNT")
    if project is not None:
        logger.info("Using project from env ACCOUNT: " + project)
        return project

    cime_config = get_cime_config()
    if cime_config.has_option("main", "PROJECT"):
        project = cime_config.get("main", "PROJECT")
        if project is not None:
            logger.info("Using project from .cime/config: " + project)
            return project

    projectfile = os.path.abspath(os.path.join(os.path.expanduser("~"), ".cesm_proj"))
    if os.path.isfile(projectfile):
        with open(projectfile, "r") as myfile:
            for line in myfile:
                project = line.rstrip()
                if not project.startswith("#"):
                    break
        if project is not None:
            logger.info("Using project from .cesm_proj: " + project)
            cime_config.set("main", "PROJECT", project)
            return project

    if machobj is not None:
        project = machobj.get_value("PROJECT")
        if project is not None:
            logger.info("Using project from config_machines.xml: " + project)
            return project

    logger.info("No project info available")
    return None


def get_charge_account(machobj=None, project=None):
    """
    Hierarchy for choosing CHARGE_ACCOUNT:
    1. Environment variable CHARGE_ACCOUNT
    2. File $HOME/.cime/config
    3. config_machines.xml (if machobj provided)
    4. default to same value as PROJECT

    >>> import CIME
    >>> import CIME.XML.machines
    >>> machobj = CIME.XML.machines.Machines(machine="theta")
    >>> project = get_project(machobj)
    >>> charge_account = get_charge_account(machobj, project)
    >>> project == charge_account
    True
    >>> os.environ["CHARGE_ACCOUNT"] = "ChargeAccount"
    >>> get_charge_account(machobj, project)
    'ChargeAccount'
    >>> del os.environ["CHARGE_ACCOUNT"]
    """
    charge_account = os.environ.get("CHARGE_ACCOUNT")
    if charge_account is not None:
        logger.info("Using charge_account from env CHARGE_ACCOUNT: " + charge_account)
        return charge_account

    cime_config = get_cime_config()
    if cime_config.has_option("main", "CHARGE_ACCOUNT"):
        charge_account = cime_config.get("main", "CHARGE_ACCOUNT")
        if charge_account is not None:
            logger.info("Using charge_account from .cime/config: " + charge_account)
            return charge_account

    if machobj is not None:
        charge_account = machobj.get_value("CHARGE_ACCOUNT")
        if charge_account is not None:
            logger.info(
                "Using charge_account from config_machines.xml: " + charge_account
            )
            return charge_account

    logger.info("No charge_account info available, using value from PROJECT")
    return project


def find_files(rootdir, pattern):
    """
    recursively find all files matching a pattern
    """
    result = []
    for root, _, files in os.walk(rootdir):
        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                result.append(os.path.join(root, filename))

    return result


def setup_standard_logging_options(parser):
    group = parser.add_argument_group("Logging options")

    helpfile = os.path.join(os.getcwd(), os.path.basename("{}.log".format(sys.argv[0])))

    group.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print debug information (very verbose) to file {}".format(helpfile),
    )

    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Add additional context (time and file) to log messages",
    )

    group.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Print only warnings and error messages",
    )


class _LessThanFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(_LessThanFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    def filter(self, record):
        # non-zero return means we log this message
        return 1 if record.levelno < self.max_level else 0


def configure_logging(verbose, debug, silent):
    root_logger = logging.getLogger()

    verbose_formatter = logging.Formatter(
        fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%m-%d %H:%M"
    )

    # Change info to go to stdout. This handle applies to INFO exclusively
    stdout_stream_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_stream_handler.setLevel(logging.INFO)
    stdout_stream_handler.addFilter(_LessThanFilter(logging.WARNING))

    # Change warnings and above to go to stderr
    stderr_stream_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_stream_handler.setLevel(logging.WARNING)

    # --verbose adds to the message format but does not impact the log level
    if verbose:
        stdout_stream_handler.setFormatter(verbose_formatter)
        stderr_stream_handler.setFormatter(verbose_formatter)

    root_logger.addHandler(stdout_stream_handler)
    root_logger.addHandler(stderr_stream_handler)

    if debug:
        # Set up log file to catch ALL logging records
        log_file = "{}.log".format(os.path.basename(sys.argv[0]))

        debug_log_handler = logging.FileHandler(log_file, mode="w")
        debug_log_handler.setFormatter(verbose_formatter)
        debug_log_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(debug_log_handler)

        root_logger.setLevel(logging.DEBUG)
    elif silent:
        root_logger.setLevel(logging.WARN)
    else:
        root_logger.setLevel(logging.INFO)


def parse_args_and_handle_standard_logging_options(args, parser=None):
    """
    Guide to logging in CIME.

    logger.debug -> Verbose/detailed output, use for debugging, off by default. Goes to a .log file
    logger.info -> Goes to stdout (and log if --debug). Use for normal program output
    logger.warning -> Goes to stderr (and log if --debug). Use for minor problems
    logger.error -> Goes to stderr (and log if --debug)
    """
    # scripts_regression_tests is the only thing that should pass a None argument in parser
    if parser is not None:
        if "--help" not in args[1:]:
            _check_for_invalid_args(args[1:])
        args = parser.parse_args(args[1:])

    configure_logging(args.verbose, args.debug, args.silent)

    return args


def get_logging_options():
    """
    Use to pass same logging options as was used for current
    executable to subprocesses.
    """
    root_logger = logging.getLogger()

    if root_logger.level == logging.DEBUG:
        return "--debug"
    elif root_logger.level == logging.WARN:
        return "--silent"
    else:
        return ""


def convert_to_type(value, type_str, vid=""):
    """
    Convert value from string to another type.
    vid is only for generating better error messages.
    """
    if value is not None:

        if type_str == "char":
            pass

        elif type_str == "integer":
            try:
                value = int(eval(value))
            except Exception:
                expect(
                    False,
                    "Entry {} was listed as type int but value '{}' is not valid int".format(
                        vid, value
                    ),
                )

        elif type_str == "logical":
            expect(
                value.upper() in ["TRUE", "FALSE"],
                "Entry {} was listed as type logical but had val '{}' instead of TRUE or FALSE".format(
                    vid, value
                ),
            )
            value = value.upper() == "TRUE"

        elif type_str == "real":
            try:
                value = float(value)
            except Exception:
                expect(
                    False,
                    "Entry {} was listed as type real but value '{}' is not valid real".format(
                        vid, value
                    ),
                )

        else:
            expect(False, "Unknown type '{}'".format(type_str))

    return value


def convert_to_unknown_type(value):
    """
    Convert value to it's real type by probing conversions.
    """
    if value is not None:

        # Attempt to convert to logical
        if value.upper() in ["TRUE", "FALSE"]:
            return value.upper() == "TRUE"

        # Attempt to convert to integer
        try:
            value = int(eval(value))
        except Exception:
            pass
        else:
            return value

        # Attempt to convert to float
        try:
            value = float(value)
        except Exception:
            pass
        else:
            return value

        # Just treat as string

    return value


def convert_to_string(value, type_str=None, vid=""):
    """
    Convert value back to string.
    vid is only for generating better error messages.
    >>> convert_to_string(6, type_str="integer") == '6'
    True
    >>> convert_to_string('6', type_str="integer") == '6'
    True
    >>> convert_to_string('6.0', type_str="real") == '6.0'
    True
    >>> convert_to_string(6.01, type_str="real") == '6.01'
    True
    """
    if value is not None and not isinstance(value, str):
        if type_str == "char":
            expect(
                isinstance(value, str),
                "Wrong type for entry id '{}'".format(vid),
            )
        elif type_str == "integer":
            expect(
                isinstance(value, int),
                "Wrong type for entry id '{}'".format(vid),
            )
            value = str(value)
        elif type_str == "logical":
            expect(type(value) is bool, "Wrong type for entry id '{}'".format(vid))
            value = "TRUE" if value else "FALSE"
        elif type_str == "real":
            expect(type(value) is float, "Wrong type for entry id '{}'".format(vid))
            value = str(value)
        else:
            expect(False, "Unknown type '{}'".format(type_str))
    if value is None:
        value = ""
        logger.debug("Attempt to convert None value for vid {} {}".format(vid, value))

    return value


def convert_to_seconds(time_str):
    """
    Convert time value in [[HH:]MM:]SS to seconds

    We assume that XX:YY is likely to be HH:MM, not MM:SS

    >>> convert_to_seconds("42")
    42
    >>> convert_to_seconds("01:01:01")
    3661
    >>> convert_to_seconds("01:01")
    3660
    """
    components = time_str.split(":")
    expect(len(components) < 4, "Unusual time string: '{}'".format(time_str))

    components.reverse()
    result = 0
    starting_exp = 1 if len(components) == 2 else 0
    for idx, component in enumerate(components):
        result += int(component) * pow(60, idx + starting_exp)

    return result


def convert_to_babylonian_time(seconds):
    """
    Convert time value to seconds to HH:MM:SS

    >>> convert_to_babylonian_time(3661)
    '01:01:01'
    >>> convert_to_babylonian_time(360000)
    '100:00:00'
    """
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60

    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def get_time_in_seconds(timeval, unit):
    """
    Convert a time from 'unit' to seconds
    """
    if "nyear" in unit:
        dmult = 365 * 24 * 3600
    elif "nmonth" in unit:
        dmult = 30 * 24 * 3600
    elif "nday" in unit:
        dmult = 24 * 3600
    elif "nhour" in unit:
        dmult = 3600
    elif "nminute" in unit:
        dmult = 60
    else:
        dmult = 1

    return dmult * timeval


def compute_total_time(job_cost_map, proc_pool):
    """
    Given a map: jobname -> (procs, est-time), return a total time
    estimate for a given processor pool size

    >>> job_cost_map = {"A" : (4, 3000), "B" : (2, 1000), "C" : (8, 2000), "D" : (1, 800)}
    >>> compute_total_time(job_cost_map, 8)
    5160
    >>> compute_total_time(job_cost_map, 12)
    3180
    >>> compute_total_time(job_cost_map, 16)
    3060
    """
    current_time = 0
    waiting_jobs = dict(job_cost_map)
    running_jobs = {}  # name -> (procs, est-time, start-time)
    while len(waiting_jobs) > 0 or len(running_jobs) > 0:
        launched_jobs = []
        for jobname, data in waiting_jobs.items():
            procs_for_job, time_for_job = data
            if procs_for_job <= proc_pool:
                proc_pool -= procs_for_job
                launched_jobs.append(jobname)
                running_jobs[jobname] = (procs_for_job, time_for_job, current_time)

        for launched_job in launched_jobs:
            del waiting_jobs[launched_job]

        completed_jobs = []
        for jobname, data in running_jobs.items():
            procs_for_job, time_for_job, time_started = data
            if (current_time - time_started) >= time_for_job:
                proc_pool += procs_for_job
                completed_jobs.append(jobname)

        for completed_job in completed_jobs:
            del running_jobs[completed_job]

        current_time += 60  # minute time step

    return current_time


def format_time(time_format, input_format, input_time):
    """
    Converts the string input_time from input_format to time_format
    Valid format specifiers are "%H", "%M", and "%S"
    % signs must be followed by an H, M, or S and then a separator
    Separators can be any string without digits or a % sign
    Each specifier can occur more than once in the input_format,
    but only the first occurence will be used.
    An example of a valid format: "%H:%M:%S"
    Unlike strptime, this does support %H >= 24

    >>> format_time("%H:%M:%S", "%H", "43")
    '43:00:00'
    >>> format_time("%H  %M", "%M,%S", "59,59")
    '0  59'
    >>> format_time("%H, %S", "%H:%M:%S", "2:43:9")
    '2, 09'
    """
    input_fields = input_format.split("%")
    expect(
        input_fields[0] == input_time[: len(input_fields[0])],
        "Failed to parse the input time '{}'; does not match the header string '{}'".format(
            input_time, input_format
        ),
    )
    input_time = input_time[len(input_fields[0]) :]
    timespec = {"H": None, "M": None, "S": None}
    maxvals = {"M": 60, "S": 60}
    DIGIT_CHECK = re.compile("[^0-9]*")
    # Loop invariants given input follows the specs:
    # field starts with H, M, or S
    # input_time starts with a number corresponding with the start of field
    for field in input_fields[1:]:
        # Find all of the digits at the start of the string
        spec = field[0]
        value_re = re.match(r"\d*", input_time)
        expect(
            value_re is not None,
            "Failed to parse the input time for the '{}' specifier, expected an integer".format(
                spec
            ),
        )
        value = value_re.group(0)
        expect(spec in timespec, "Unknown time specifier '" + spec + "'")
        # Don't do anything if the time field is already specified
        if timespec[spec] is None:
            # Verify we aren't exceeding the maximum value
            if spec in maxvals:
                expect(
                    int(value) < maxvals[spec],
                    "Failed to parse the '{}' specifier: A value less than {:d} is expected".format(
                        spec, maxvals[spec]
                    ),
                )
            timespec[spec] = value
        input_time = input_time[len(value) :]
        # Check for the separator string
        expect(
            len(re.match(DIGIT_CHECK, field).group(0)) == len(field),
            "Numbers are not permissible in separator strings",
        )
        expect(
            input_time[: len(field) - 1] == field[1:],
            "The separator string ({}) doesn't match '{}'".format(
                field[1:], input_time
            ),
        )
        input_time = input_time[len(field) - 1 :]
    output_fields = time_format.split("%")
    output_time = output_fields[0]
    # Used when a value isn't given
    min_len_spec = {"H": 1, "M": 2, "S": 2}
    # Loop invariants given input follows the specs:
    # field starts with H, M, or S
    # output_time
    for field in output_fields[1:]:
        expect(
            field == output_fields[-1] or len(field) > 1,
            "Separator strings are required to properly parse times",
        )
        spec = field[0]
        expect(spec in timespec, "Unknown time specifier '" + spec + "'")
        if timespec[spec] is not None:
            output_time += "0" * (min_len_spec[spec] - len(timespec[spec]))
            output_time += timespec[spec]
        else:
            output_time += "0" * min_len_spec[spec]
        output_time += field[1:]
    return output_time


def append_status(msg, sfile, caseroot="."):
    """
    Append msg to sfile in caseroot
    """
    ctime = time.strftime("%Y-%m-%d %H:%M:%S: ")

    # Reduce empty lines in CaseStatus. It's a very concise file
    # and does not need extra newlines for readability
    line_ending = "\n"

    with open(os.path.join(caseroot, sfile), "a") as fd:
        fd.write(ctime + msg + line_ending)
        fd.write(" ---------------------------------------------------" + line_ending)


def append_testlog(msg, caseroot="."):
    """
    Add to TestStatus.log file
    """
    append_status(msg, "TestStatus.log", caseroot)


def append_case_status(phase, status, msg=None, caseroot="."):
    """
    Update CaseStatus file
    """
    append_status(
        "{} {}{}".format(phase, status, " {}".format(msg if msg else "")),
        "CaseStatus",
        caseroot,
    )


def does_file_have_string(filepath, text):
    """
    Does the text string appear in the filepath file
    """
    return os.path.isfile(filepath) and text in open(filepath).read()


def is_last_process_complete(filepath, expect_text, fail_text):
    """
    Search the filepath in reverse order looking for expect_text
    before finding fail_text. This utility is used by archive_metadata.

    """
    complete = False
    fh = open(filepath, "r")
    fb = fh.readlines()

    rfb = "".join(reversed(fb))

    findex = re.search(fail_text, rfb)
    if findex is None:
        findex = 0
    else:
        findex = findex.start()

    eindex = re.search(expect_text, rfb)
    if eindex is None:
        eindex = 0
    else:
        eindex = eindex.start()

    if findex > eindex:
        complete = True

    return complete


def transform_vars(text, case=None, subgroup=None, overrides=None, default=None):
    """
    Do the variable substitution for any variables that need transforms
    recursively.

    >>> transform_vars("{{ cesm_stdout }}", default="cesm.stdout")
    'cesm.stdout'
    >>> member_store = lambda : None
    >>> member_store.foo = "hi"
    >>> transform_vars("I say {{ foo }}", overrides={"foo":"hi"})
    'I say hi'
    """
    directive_re = re.compile(r"{{ (\w+) }}", flags=re.M)
    # loop through directive text, replacing each string enclosed with
    # template characters with the necessary values.
    while directive_re.search(text):
        m = directive_re.search(text)
        variable = m.groups()[0]
        whole_match = m.group()
        if (
            overrides is not None
            and variable.lower() in overrides
            and overrides[variable.lower()] is not None
        ):
            repl = overrides[variable.lower()]
            logger.debug(
                "from overrides: in {}, replacing {} with {}".format(
                    text, whole_match, str(repl)
                )
            )
            text = text.replace(whole_match, str(repl))

        elif (
            case is not None
            and hasattr(case, variable.lower())
            and getattr(case, variable.lower()) is not None
        ):
            repl = getattr(case, variable.lower())
            logger.debug(
                "from case members: in {}, replacing {} with {}".format(
                    text, whole_match, str(repl)
                )
            )
            text = text.replace(whole_match, str(repl))

        elif (
            case is not None
            and case.get_value(variable.upper(), subgroup=subgroup) is not None
        ):
            repl = case.get_value(variable.upper(), subgroup=subgroup)
            logger.debug(
                "from case: in {}, replacing {} with {}".format(
                    text, whole_match, str(repl)
                )
            )
            text = text.replace(whole_match, str(repl))

        elif default is not None:
            logger.debug(
                "from default: in {}, replacing {} with {}".format(
                    text, whole_match, str(default)
                )
            )
            text = text.replace(whole_match, default)

        else:
            # If no queue exists, then the directive '-q' by itself will cause an error
            if "-q {{ queue }}" in text:
                text = ""
            else:
                logger.warning("Could not replace variable '{}'".format(variable))
                text = text.replace(whole_match, "")

    return text


def wait_for_unlocked(filepath):
    locked = True
    file_object = None
    while locked:
        try:
            buffer_size = 8
            # Opening file in append mode and read the first 8 characters.
            file_object = open(filepath, "a", buffer_size)
            if file_object:
                locked = False
        except IOError:
            locked = True
            time.sleep(1)
        finally:
            if file_object:
                file_object.close()


def gunzip_existing_file(filepath):
    with gzip.open(filepath, "rb") as fd:
        return fd.read()


def gzip_existing_file(filepath):
    """
    Gzips an existing file, removes the unzipped version, returns path to zip file.
    Note the that the timestamp of the original file will be maintained in
    the zipped file.

    >>> import tempfile
    >>> fd, filename = tempfile.mkstemp(text=True)
    >>> _ = os.write(fd, b"Hello World")
    >>> os.close(fd)
    >>> gzfile = gzip_existing_file(filename)
    >>> gunzip_existing_file(gzfile) == b'Hello World'
    True
    >>> os.remove(gzfile)
    """
    expect(os.path.exists(filepath), "{} does not exists".format(filepath))

    st = os.stat(filepath)
    orig_atime, orig_mtime = st[statlib.ST_ATIME], st[statlib.ST_MTIME]

    gzpath = "{}.gz".format(filepath)
    with open(filepath, "rb") as f_in:
        with gzip.open(gzpath, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(filepath)

    os.utime(gzpath, (orig_atime, orig_mtime))

    return gzpath


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


def find_system_test(testname, case):
    """
    Find and import the test matching testname
    Look through the paths set in config_files.xml variable SYSTEM_TESTS_DIR
    for components used in this case to find a test matching testname.  Add the
    path to that directory to sys.path if its not there and return the test object
    Fail if the test is not found in any of the paths.
    """
    from importlib import import_module

    system_test_path = None
    if testname.startswith("TEST"):
        system_test_path = "CIME.SystemTests.system_tests_common.{}".format(testname)
    else:
        components = ["any"]
        components.extend(case.get_compset_components())
        fdir = []
        for component in components:
            tdir = case.get_value(
                "SYSTEM_TESTS_DIR", attribute={"component": component}
            )
            if tdir is not None:
                tdir = os.path.abspath(tdir)
                system_test_file = os.path.join(tdir, "{}.py".format(testname.lower()))
                if os.path.isfile(system_test_file):
                    fdir.append(tdir)
                    logger.debug("found " + system_test_file)
                    if component == "any":
                        system_test_path = "CIME.SystemTests.{}.{}".format(
                            testname.lower(), testname
                        )
                    else:
                        system_test_dir = os.path.dirname(system_test_file)
                        if system_test_dir not in sys.path:
                            sys.path.append(system_test_dir)
                        system_test_path = "{}.{}".format(testname.lower(), testname)
        expect(len(fdir) > 0, "Test {} not found, aborting".format(testname))
        expect(
            len(fdir) == 1,
            "Test {} found in multiple locations {}, aborting".format(testname, fdir),
        )
    expect(system_test_path is not None, "No test {} found".format(testname))

    path, m = system_test_path.rsplit(".", 1)
    mod = import_module(path)
    return getattr(mod, m)


def _get_most_recent_lid_impl(files):
    """
    >>> files = ['/foo/bar/e3sm.log.20160905_111212', '/foo/bar/e3sm.log.20160906_111212.gz']
    >>> _get_most_recent_lid_impl(files)
    ['20160905_111212', '20160906_111212']
    >>> files = ['/foo/bar/e3sm.log.20160905_111212', '/foo/bar/e3sm.log.20160905_111212.gz']
    >>> _get_most_recent_lid_impl(files)
    ['20160905_111212']
    """
    results = []
    for item in files:
        basename = os.path.basename(item)
        components = basename.split(".")
        if len(components) > 2:
            results.append(components[2])
        else:
            logger.warning(
                "Apparent model log file '{}' did not conform to expected name format".format(
                    item
                )
            )

    return sorted(list(set(results)))


def ls_sorted_by_mtime(path):
    """return list of path sorted by timestamp oldest first"""
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))


def get_lids(case):
    model = case.get_value("MODEL")
    rundir = case.get_value("RUNDIR")
    return _get_most_recent_lid_impl(glob.glob("{}/{}.log*".format(rundir, model)))


def new_lid(case=None):
    lid = time.strftime("%y%m%d-%H%M%S")
    jobid = batch_jobid(case=case)
    if jobid is not None:
        lid = jobid + "." + lid
    os.environ["LID"] = lid
    return lid


def batch_jobid(case=None):
    jobid = os.environ.get("PBS_JOBID")
    if jobid is None:
        jobid = os.environ.get("SLURM_JOB_ID")
    if jobid is None:
        jobid = os.environ.get("LSB_JOBID")
    if jobid is None:
        jobid = os.environ.get("COBALT_JOBID")
    if case:
        jobid = case.get_job_id(jobid)
    return jobid


def analyze_build_log(comp, log, compiler):
    """
    Capture and report warning count,
    capture and report errors and undefined references.
    """
    warncnt = 0
    if "intel" in compiler:
        warn_re = re.compile(r" warning #")
        error_re = re.compile(r" error #")
        undefined_re = re.compile(r" undefined reference to ")
    elif "gnu" in compiler or "nag" in compiler:
        warn_re = re.compile(r"^Warning: ")
        error_re = re.compile(r"^Error: ")
        undefined_re = re.compile(r" undefined reference to ")
    else:
        # don't know enough about this compiler
        return

    with open(log, "r") as fd:
        for line in fd:
            if re.search(warn_re, line):
                warncnt += 1
            if re.search(error_re, line):
                logger.warning(line)
            if re.search(undefined_re, line):
                logger.warning(line)

    if warncnt > 0:
        logger.info(
            "Component {} build complete with {} warnings".format(comp, warncnt)
        )


def is_python_executable(filepath):
    first_line = None
    if os.path.isfile(filepath):
        with open(filepath, "rt") as f:
            try:
                first_line = f.readline()
            except Exception:
                pass

        return (
            first_line is not None
            and first_line.startswith("#!")
            and "python" in first_line
        )
    return False


def get_umask():
    current_umask = os.umask(0)
    os.umask(current_umask)

    return current_umask


def stringify_bool(val):
    val = False if val is None else val
    expect(type(val) is bool, "Wrong type for val '{}'".format(repr(val)))
    return "TRUE" if val else "FALSE"


def indent_string(the_string, indent_level):
    """Indents the given string by a given number of spaces

    Args:
       the_string: str
       indent_level: int

    Returns a new string that is the same as the_string, except that
    each line is indented by 'indent_level' spaces.

    In python3, this can be done with textwrap.indent.
    """

    lines = the_string.splitlines(True)
    padding = " " * indent_level
    lines_indented = [padding + line for line in lines]
    return "".join(lines_indented)


def verbatim_success_msg(return_val):
    return return_val


CASE_SUCCESS = "success"
CASE_FAILURE = "error"


def run_and_log_case_status(
    func,
    phase,
    caseroot=".",
    custom_starting_msg_functor=None,
    custom_success_msg_functor=None,
    is_batch=False,
):
    starting_msg = None

    if custom_starting_msg_functor is not None:
        starting_msg = custom_starting_msg_functor()

    # Delay appending "starting" on "case.subsmit" phase when batch system is
    # present since we don't have the jobid yet
    if phase != "case.submit" or not is_batch:
        append_case_status(phase, "starting", msg=starting_msg, caseroot=caseroot)
    rv = None
    try:
        rv = func()
    except BaseException:
        custom_success_msg = (
            custom_success_msg_functor(rv)
            if custom_success_msg_functor and rv is not None
            else None
        )
        if phase == "case.submit" and is_batch:
            append_case_status(
                phase, "starting", msg=custom_success_msg, caseroot=caseroot
            )
        e = sys.exc_info()[1]
        append_case_status(
            phase, CASE_FAILURE, msg=("\n{}".format(e)), caseroot=caseroot
        )
        raise
    else:
        custom_success_msg = (
            custom_success_msg_functor(rv) if custom_success_msg_functor else None
        )
        if phase == "case.submit" and is_batch:
            append_case_status(
                phase, "starting", msg=custom_success_msg, caseroot=caseroot
            )
        append_case_status(
            phase, CASE_SUCCESS, msg=custom_success_msg, caseroot=caseroot
        )

    return rv


def _check_for_invalid_args(args):
    # Prevent circular import
    from CIME.config import Config

    # TODO Is this really model specific
    if Config.instance().check_invalid_args:
        for arg in args:
            # if arg contains a space then it was originally quoted and we can ignore it here.
            if " " in arg or arg.startswith("--"):
                continue
            if arg.startswith("-") and len(arg) > 2:
                sys.stderr.write(
                    'WARNING: The {} argument is deprecated. Multi-character arguments should begin with "--" and single character with "-"\n  Use --help for a complete list of available options\n'.format(
                        arg
                    )
                )


def add_mail_type_args(parser):
    parser.add_argument("--mail-user", help="Email to be used for batch notification.")

    parser.add_argument(
        "-M",
        "--mail-type",
        action="append",
        help="When to send user email. Options are: never, all, begin, end, fail.\n"
        "You can specify multiple types with either comma-separated args or multiple -M flags.",
    )


def resolve_mail_type_args(args):
    if args.mail_type is not None:
        resolved_mail_types = []
        for mail_type in args.mail_type:
            resolved_mail_types.extend(mail_type.split(","))

        for mail_type in resolved_mail_types:
            expect(
                mail_type in ("never", "all", "begin", "end", "fail"),
                "Unsupported mail-type '{}'".format(mail_type),
            )

        args.mail_type = resolved_mail_types


def copyifnewer(src, dest):
    """if dest does not exist or is older than src copy src to dest"""
    if not os.path.isfile(dest) or not filecmp.cmp(src, dest):
        safe_copy(src, dest)


class SharedArea(object):
    """
    Enable 0002 umask within this manager
    """

    def __init__(self, new_perms=0o002):
        self._orig_umask = None
        self._new_perms = new_perms

    def __enter__(self):
        self._orig_umask = os.umask(self._new_perms)

    def __exit__(self, *_):
        os.umask(self._orig_umask)


class Timeout(object):
    """
    A context manager that implements a timeout. By default, it
    will raise exception, but a custon function call can be provided.
    Provided None as seconds makes this class a no-op
    """

    def __init__(self, seconds, action=None):
        self._seconds = seconds
        self._action = action if action is not None else self._handle_timeout

    def _handle_timeout(self, *_):
        raise RuntimeError("Timeout expired")

    def __enter__(self):
        if self._seconds is not None:
            signal.signal(signal.SIGALRM, self._action)
            signal.alarm(self._seconds)

    def __exit__(self, *_):
        if self._seconds is not None:
            signal.alarm(0)


def filter_unicode(unistr):
    """
    Sometimes unicode chars can cause problems
    """
    return "".join([i if ord(i) < 128 else " " for i in unistr])


def run_bld_cmd_ensure_logging(cmd, arg_logger, from_dir=None, timeout=None):
    arg_logger.info(cmd)
    stat, output, errput = run_cmd(cmd, from_dir=from_dir, timeout=timeout)
    arg_logger.info(output)
    arg_logger.info(errput)
    expect(stat == 0, filter_unicode(errput))


def get_batch_script_for_job(job):
    return job if "st_archive" in job else "." + job


def string_in_list(_string, _list):
    """Case insensitive search for string in list
    returns the matching list value
    >>> string_in_list("Brack",["bar", "bracK", "foo"])
    'bracK'
    >>> string_in_list("foo", ["FFO", "FOO", "foo2", "foo3"])
    'FOO'
    >>> string_in_list("foo", ["FFO", "foo2", "foo3"])
    """
    for x in _list:
        if _string.lower() == x.lower():
            return x
    return None


def model_log(model, arg_logger, msg, debug_others=True):
    if get_model() == model:
        arg_logger.info(msg)
    elif debug_others:
        arg_logger.debug(msg)


def get_htmlroot(machobj=None):
    """Get location for test HTML output

    Hierarchy for choosing CIME_HTML_ROOT:
    0. Environment variable CIME_HTML_ROOT
    1. File $HOME/.cime/config
    2. config_machines.xml (if machobj provided)
    """
    htmlroot = os.environ.get("CIME_HTML_ROOT")
    if htmlroot is not None:
        logger.info("Using htmlroot from env CIME_HTML_ROOT: {}".format(htmlroot))
        return htmlroot

    cime_config = get_cime_config()
    if cime_config.has_option("main", "CIME_HTML_ROOT"):
        htmlroot = cime_config.get("main", "CIME_HTML_ROOT")
        if htmlroot is not None:
            logger.info("Using htmlroot from .cime/config: {}".format(htmlroot))
            return htmlroot

    if machobj is not None:
        htmlroot = machobj.get_value("CIME_HTML_ROOT")
        if htmlroot is not None:
            logger.info("Using htmlroot from config_machines.xml: {}".format(htmlroot))
            return htmlroot

    logger.info("No htmlroot info available")
    return None


def get_urlroot(machobj=None):
    """Get URL to htmlroot

    Hierarchy for choosing CIME_URL_ROOT:
    0. Environment variable CIME_URL_ROOT
    1. File $HOME/.cime/config
    2. config_machines.xml (if machobj provided)
    """
    urlroot = os.environ.get("CIME_URL_ROOT")
    if urlroot is not None:
        logger.info("Using urlroot from env CIME_URL_ROOT: {}".format(urlroot))
        return urlroot

    cime_config = get_cime_config()
    if cime_config.has_option("main", "CIME_URL_ROOT"):
        urlroot = cime_config.get("main", "CIME_URL_ROOT")
        if urlroot is not None:
            logger.info("Using urlroot from .cime/config: {}".format(urlroot))
            return urlroot

    if machobj is not None:
        urlroot = machobj.get_value("CIME_URL_ROOT")
        if urlroot is not None:
            logger.info("Using urlroot from config_machines.xml: {}".format(urlroot))
            return urlroot

    logger.info("No urlroot info available")
    return None


def clear_folder(_dir):
    if os.path.exists(_dir):
        for the_file in os.listdir(_dir):
            file_path = os.path.join(_dir, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                else:
                    clear_folder(file_path)
                    os.rmdir(file_path)
            except Exception as e:
                print(e)


def add_flag_to_cmd(flag, val):
    """
    Given a flag and value for a shell command, return a string

    >>> add_flag_to_cmd("-f", "hi")
    '-f hi'
    >>> add_flag_to_cmd("--foo", 42)
    '--foo 42'
    >>> add_flag_to_cmd("--foo=", 42)
    '--foo=42'
    >>> add_flag_to_cmd("--foo:", 42)
    '--foo:42'
    >>> add_flag_to_cmd("--foo:", " hi ")
    '--foo:hi'
    """
    no_space_chars = "=:"
    no_space = False
    for item in no_space_chars:
        if flag.endswith(item):
            no_space = True

    separator = "" if no_space else " "
    return "{}{}{}".format(flag, separator, str(val).strip())


def is_comp_standalone(case):
    """
    Test if the case is a single component standalone
    such as FKESSLER
    """
    stubcnt = 0
    classes = case.get_values("COMP_CLASSES")
    for comp in classes:
        if case.get_value("COMP_{}".format(comp)) == "s{}".format(comp.lower()):
            stubcnt = stubcnt + 1
        else:
            model = comp.lower()
    numclasses = len(classes)
    if stubcnt >= numclasses - 2:
        return True, model
    return False, get_model()
