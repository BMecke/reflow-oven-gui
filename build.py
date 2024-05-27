import os
import subprocess
import shutil


def check_working_directory():
    """
    Returns, whether the current working directory is equal to the repository root.

    Returns
    -------
    bool
        True if working directory is "reflow-oven-gui", False otherwise.
    """
    if os.path.basename(os.getcwd()) != 'reflow-oven-gui':
        return False
    if not os.path.isfile('build.py'):
        return False
    if not os.path.isfile(os.path.join('reflow_oven', 'main.py')):
        return False
    return True


def clear_app():
    """
    Deletes any currently present "pyinstaller" artifact-directories.
    This includes "build" as well as "dist".
    """
    build_dir = 'build'
    dist_dir = 'dist'
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)


def create_app():
    """
    Invokes "pyinstaller" to create a standalone executable version of this Python project.
    Target directory for the result is "dist".
    """
    subprocess.run(
        ['pyinstaller', 'reflow_oven/main.py',
         '-F',
         '-p', 'reflow_oven/',
         '--add-data', 'reflow_oven/web/templates:web/templates',
         '--add-data', 'reflow_oven/web/static:web/static']
    )
    shutil.copytree(os.path.join('reflow_oven', 'storage'), os.path.join('dist', 'storage'))


if __name__ == "__main__":
    if not check_working_directory():
        print('Please run "build.py" from "reflow-oven-gui" as working directory')
    else:
        clear_app()
        create_app()
