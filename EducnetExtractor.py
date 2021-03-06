#!/bin/python3

import argparse
import os
import re
import shutil
import tempfile

from os import listdir, mkdir, system
from os.path import isfile, isdir, join, dirname, basename

from pyunpack import Archive


def recursiveFindCMakeLists(path):
    candidates = [join(path, f) for f in listdir(path) if f == "CMakeLists.txt"]
    if len(candidates) > 0:
        return candidates[0]

    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = recursiveFindCMakeLists(dir)
        if result is not None:
            return result

    return None


def findDirsWithCpp(path):
    candidates = [join(path, f) for f in listdir(path) if f.endswith(".cpp")]
    if len(candidates) > 0:
        return [(path, candidates)]

    result = []
    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = result + findDirsWithCpp(dir)

    return result


def findExecutables(path):
    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    executables = [join(path, f) for f in listdir(path) if
                   isfile(join(path, f)) and os.access(join(path, f), os.X_OK) and not f.endswith(
                       ".bin") and not f.endswith(".out")]

    for dir in dirs:
        executables = executables + findExecutables(dir)

    return executables

def process_dir(dir, target_directory, execute=False):
    cmakepath = recursiveFindCMakeLists(dir)
    outputdirname = join(target_directory, basename(dir).split("_")[0])
    if cmakepath is not None:
        cmakedirname = dirname(cmakepath)
        shutil.move(cmakedirname, outputdirname)
    else:
        print("Automatic CMake generation for " + outputdirname)
        cppdirs = findDirsWithCpp(dir)
        mkdir(outputdirname)
        for cppdir, cppfiles in cppdirs:
            shutil.move(cppdir, join(outputdirname, basename(cppdir)))
        cppdirs = findDirsWithCpp(outputdirname)
        # todo : generate the CMakeLists.txt
        cmakelistcontent = "cmake_minimum_required(VERSION 2.6)\r\nfile(TO_CMAKE_PATH \"$ENV{IMAGINEPP_ROOT}/CMake\" p)\r\nlist(APPEND CMAKE_MODULE_PATH \"${p}\") #For old Imagine++\r\nlist(APPEND CMAKE_SYSTEM_FRAMEWORK_PATH /Library/Frameworks) #Mac, why not auto?\r\nfind_package(Imagine REQUIRED)\r\n\r\nproject(EducnetExtractor)\n\n\n"
        for cppdir, cppfiles in cppdirs:
            cppfilesfrombase = ["\"" + join(basename(cppdir), basename(file)) + "\"" for file in cppfiles]
            projectname = re.sub(r'\W+', '', basename(cppdir))
            cmakelistcontent = cmakelistcontent + "add_executable(" + projectname + " " + " ".join(
                cppfilesfrombase) + ")\n"
            cmakelistcontent = cmakelistcontent + "ImagineUseModules(" + projectname + " Graphics)\n"

        with open(join(outputdirname, "CMakeLists.txt"), "w") as text_file:
            text_file.write(cmakelistcontent)

    system("cd '" + outputdirname + "' && mkdir build && cd build && cmake .. >/dev/null 2>/dev/null && make >/dev/null 2>/dev/null")

    executables = findExecutables(outputdirname)
    new_executables = []
    for executable in executables:
        shutil.move(executable, outputdirname + "/exe_" + basename(executable))
        new_executables.append(outputdirname + "/exe_" + basename(executable))

    executables = new_executables

    if execute:
        cls()

        while True:
            print(basename(dir).split("_")[0])
            print(" ")
            print(" ")

            for i in range(0, len(executables)):
                print(str(i) + " : " + basename(executables[i]))
            print("[vide] : Passer à l'eleve suivant")

            print(" ")
            print(" ")

            if cmakepath is None:
                print("Aucun CMake trouvé. Il a été généré automatiquement.")

            if len(executables) == 0:
                print("Aucun executable trouvé :(")

            print(" ")
            print(" ")

            i = input("=> ")
            if i == "":
                break
            try:
                i = int(i)
            except:
                continue
            if i < 0 or i >= len(executables):
                continue

            cls()
            print(":'" + executables[i] + "'")
            system("'" + executables[i] + "'")

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def main():
    parser = argparse.ArgumentParser("EductnetExtractor by Thomas Belos")
    parser.add_argument("-z", "--zip", nargs='+', help='<Required> One or more zip file', required=True)
    parser.add_argument("-d", "--dst", help='<Required> Destination directory', required=True)
    parser.add_argument("-e", "--execute", help='execute the file', type=bool)

    args = parser.parse_args()

    dst = args.dst
    with tempfile.TemporaryDirectory(suffix="_educnetextractor") as tmpdst:
        for file in args.zip:
            print("Extracting " + file)
            Archive(file).extractall(tmpdst)

        dirs = [join(tmpdst, f) for f in listdir(tmpdst) if isdir(join(tmpdst, f))]
        files = []
        for dir in dirs:
            files = files + [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]

        for file in files:
            print("Extracting " + file)
            out = join(dirname(file), "out")
            try:
                mkdir(out)
                Archive(file).extractall(out)
            except OSError:
                print("Impossible de créer " + out)
            except Exception as exc:
                print(exc)

        for dir in dirs:
            process_dir(dir, dst, execute=args.execute)


if __name__ == '__main__':
    main()
