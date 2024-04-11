import os
import subprocess
import shutil


def check_working_directory():
    if os.path.basename(os.getcwd()) != 'reflow-oven-gui':
        return False
    if not os.path.isfile('build.py'):
        return False
    if not os.path.isfile(os.path.join('src', 'main.py')):
        return False
    return True


def clear_app():
    build_dir = 'build'
    dist_dir = 'dist'
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)


def create_app():
    subprocess.run(
        ['pyinstaller', 'src/main.py',
         '-F',
         '-p', 'src/',
         '--add-data', 'src/web/templates:web/templates',
         '--add-data', 'src/web/static:web/static']
    )
    shutil.copytree(os.path.join('src', 'storage'), os.path.join('dist', 'storage'))


if __name__ == "__main__":
    if not check_working_directory():
        print('Please run "build.py" from "reflow-oven-gui" as working directory')
    else:
        clear_app()
        create_app()
