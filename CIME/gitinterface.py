import sys, shutil, re
from CIME.utils import run_cmd_no_fail
from pathlib import Path


class GitInterface:
    def __init__(self, repo_path, logger, branch=None):
        major = 0
        minor = 0
        self.logger = logger
        self._defined = False
        if shutil.which("git"):
            version = run_cmd_no_fail("git --version")
            result = re.findall(r"([0-9]+)\.([0-9]+)\.?[0-9]*", version)
            major = int(result[0][0])
            minor = int(result[0][1])
        if major < 2 or (major == 2 and minor < 28):
            logger.warning(
                "Git not found or git version too old for cesm git interface {} {}".format(
                    major, minor
                )
            )
            return

        logger.debug("Initialize GitInterface for {}".format(repo_path))
        self._defined = True
        if isinstance(repo_path, str):
            self.repo_path = Path(repo_path).resolve()
        elif isinstance(repo_path, Path):
            self.repo_path = repo_path.resolve()
        else:
            raise TypeError("repo_path must be a str or Path object")
        try:
            import git

            self._use_module = True
            try:
                self.repo = git.Repo(str(self.repo_path))  # Initialize GitPython repo
            except git.exc.InvalidGitRepositoryError:
                self.git = git
                self._init_git_repo(branch=branch)
            msg = "Using GitPython interface to git"
        except ImportError:
            self._use_module = False
            if not (self.repo_path / ".git").exists():
                self._init_git_repo(branch=branch)
            msg = "Using shell interface to git"
        logger.debug(msg)

    def _git_command(self, operation, *args):
        if not self._defined:
            return
        self.logger.debug(operation)
        if self._use_module and operation != "submodule":
            try:
                return getattr(self.repo.git, operation)(*args)
            except Exception as e:
                sys.exit(e)
        else:
            return ["git", "-C", str(self.repo_path), operation] + list(args)

    def _init_git_repo(self, branch=None):
        if not self._defined:
            return
        if self._use_module:
            self.repo = self.git.Repo.init(str(self.repo_path))
            if branch:
                self.git_operation("checkout", "-b", branch)
        else:
            command = ["git", "-C", str(self.repo_path), "init"]
            if branch:
                command.extend(["-b", branch])
            run_cmd_no_fail(" ".join(command))

    # pylint: disable=unused-argument
    def git_operation(self, operation, *args, **kwargs):
        if not self._defined:
            return
        command = self._git_command(operation, *args)
        if isinstance(command, list):
            try:
                return run_cmd_no_fail(" ".join(command))
            except Exception as e:
                sys.exit(e)
        else:
            return command

    def config_get_value(self, section, name):
        if not self._defined:
            return
        if self._use_module:
            config = self.repo.config_reader()
            try:
                val = config.get_value(section, name)
            except:
                val = None
            return val
        else:
            cmd = (
                "git",
                "-C",
                str(self.repo_path),
                "config",
                "--get",
                f"{section}.{name}",
            )
            output = run_cmd_no_fail(cmd)
            return output.strip()

    def config_set_value(self, section, name, value):
        if not self._defined:
            return
        if self._use_module:
            with self.repo.config_writer() as writer:
                writer.set_value(section, name, value)
            writer.release()  # Ensure changes are saved
        else:
            cmd = (
                "git",
                "-C",
                str(self.repo_path),
                "config",
                f"{section}.{name}",
                value,
            )
            self.logger.debug(cmd)
            run_cmd_no_fail(cmd)
