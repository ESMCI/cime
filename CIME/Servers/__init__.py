# pylint: disable=import-error
from shutil import which

has_gftp = which("globus-url-copy")
has_svn = which("svn")
has_wget = which("wget")
has_ftp = True
try:
    from ftplib import FTP
except ImportError:
    has_ftp = False
if has_ftp:
    from CIME.Servers.ftp import FTP
if has_svn:
    from CIME.Servers.svn import SVN
if has_wget:
    from CIME.Servers.wget import WGET
if has_gftp:
    from CIME.Servers.gftp import GridFTP
