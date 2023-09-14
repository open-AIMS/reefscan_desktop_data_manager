import logging
import shutil as os_shutil
from smbclient import shutil

logger = logging.getLogger("")
def copytree(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False,
             dirs_exist_ok=False, **kwargs):
    """
    Recursively copy an entire directory tree rooted at src to a directory named dst and return the destination
    directory. dirs_exist_ok dictates whether to raise an exception in case dst or any missing parent directory
    exists.

    Permissions and times of directories are copied with copystat(), individual files are copied using copy2().

    If symlinks is 'True', symbolic links in the source tree are represented as symbolic links in the new tree and the
    metadata of the original links will be copied as far as the platform allow; if 'False' or omitted, the contents and
    metadata of the linked files are copied to the new tree.

    When symlinks is 'False', if the file pointed by the symlink doesn't exist, an exception will be added in the list
    of errors raises in an 'Error' exception at the end of the copy process. You can set the optional
    ignore_dangling_symlinks flag to 'True' if you want to silence this exception.

    if ignore is given, it must be a callable that will receive as its arguments the directory being visited by
    copytree(), and a list of its contents, as returned by smbclient.listdir(). Since copytee() is called recursively,
    the ignore callable will be called once for each directory that is copied. The callable must return a sequence of
    directory and file names relative to the current directory (i.e. a subset of the items in its second argument);
    these names will then be ignored in the copy process.

    If exception(s) occur, an shutil.Error is raised with a list of reasons.

    If copy_function is given, it must be a callable that will be used to copy each file. It will be called with the
    source path and the destination path as arguments. By default copy() is used, but any function that supports the
    same signature (like copy()) can be used.

    In this current form, copytree() only supports remote to remote copies over SMB.

    :param src: The source directory to copy.
    :param dst: The destination directory to copy to.
    :param symlinks: Whether to attempt to copy a symlink from the source tree to the dest tree, if False the symlink
        target's contents are copied instead as a normal file/dir.
    :param ignore: A callable in the form 'callable(src, names) -> ignored_named' that returns a list of file names to
        ignore based on the list passed in.
    :param copy_function: The copy function to use for copying files.
    :param ignore_dangling_symlinks: Ignore any broken symlinks, otherwise an Error is raised.
    :param dirs_exist_ok: Whether to fail if the dst directory exists or not.
    :param kwargs: Common arguments used to build the SMB Session for any UNC paths.
    :return: The dst path.
    """
    dir_entries = list(shutil.scandir(src, **kwargs))

    ignored = []
    if ignore is not None:
        ignored = ignore(src, [e.name for e in dir_entries])

    errors = []
    for dir_entry in dir_entries:
        if dir_entry.name in ignored:
            continue

        src_path = shutil._join_local_or_remote_path(src, dir_entry.name)
        dst_path = shutil._join_local_or_remote_path(dst, dir_entry.name)

        try:
            if dir_entry.is_symlink():
                link_target = shutil.readlink(src_path, **kwargs)
                if symlinks:
                    shutil.symlink(link_target, dst_path, **kwargs)
                    shutil.copystat(src_path, dst_path, follow_symlinks=False)
                    continue
                else:
                    # Manually override the dir_entry with a new one that is the link target and copy that below.
                    try:
                        dir_entry = shutil.SMBDirEntry.from_path(link_target, **kwargs)
                    except OSError as err:
                        if err.errno == shutil.errno.ENOENT and ignore_dangling_symlinks:
                            continue
                        raise

            if dir_entry.is_dir():
                copytree(src_path, dst_path, symlinks, ignore, copy_function, ignore_dangling_symlinks, dirs_exist_ok,
                         **kwargs)
            else:
                copy_function(src_path, dst_path, **kwargs)
        except shutil.Error as err:
            # From a recursive call of copytree().
            errors.extend(err.args[0])
        except OSError as err:
            # Main smbclient operations should raise an OSError exception (or one that inherits OSError).
            errors.append((src_path, dst_path, str(err)))
        except ValueError as err:
            # If the path is not supported or we are trying to symlink outside of the share boundary.
            errors.append((src_path, dst_path, str(err)))

    if errors:
        raise os_shutil.Error(errors)
    return dst
