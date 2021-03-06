## func
##
## Copyright 2007, Red Hat, Inc
## See AUTHORS
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##
##


import distutils.sysconfig
import os
import sys
import inspect
from gettext import gettext
_ = gettext

from func import logger
logger = logger.Logger().logger

from inspect import isclass
from func.minion.modules import func_module
from func.utils import is_public_valid_method

def module_walker(topdir):
    module_files = []
    for root, dirs, files in os.walk(topdir):
        # we should get here for each subdir
        for filename in files:
            # ASSUMPTION: all module files will end with .py, .pyc, .pyo
            if filename[-3:] == ".py" or filename[-4:] == ".pyc" or filename[-4:] == ".pyo":
                # the normpath is important, since we eventually replace /'s with .'s
                # in the module name, and foo..bar doesnt work -akl
                module_files.append(os.path.normpath("%s/%s" % (root, filename)))

    return module_files

def load_methods(path, main_class, parent_class=None):
    methods = {}
    modules = load_modules(path, main_class, parent_class=parent_class)
    for x in modules.keys():
        for method in dir(modules[x]):
            if is_public_valid_method(modules[x], method):
                methods["%s.%s" % (x,method)]=getattr(modules[x], method)
    return methods

def load_modules(path='func/minion/modules/', main_class=func_module.FuncModule, blacklist=None, parent_class=None):
    python_path = distutils.sysconfig.get_python_lib()
    module_file_path = "%s/%s" % (python_path, path)
    (mod_path, mod_dir) = os.path.split(os.path.normpath(module_file_path))
    mod_dir = "func."+module_file_path[len(python_path+'/func/'):].replace("/",".")

    sys.path.insert(0, mod_path)
    mods = {}
    bad_mods = {}

    filenames = module_walker(module_file_path)

    # FIXME: this is probably more complicated than it needs to be -akl
    for fn in filenames:
        # aka, everything after the module_file_path
        module_name_part = fn[len(module_file_path):]
        dirname, basename = os.path.split(module_name_part)

        if basename[:8] == "__init__":
            modname = dirname
            dirname = ""
        elif basename[-3:] == ".py":
            modname = basename[:-3]
        elif basename[-4:] in [".pyc", ".pyo"]:
            modname = basename[:-4]

        pathname = modname
        if dirname != "":
            pathname = "%s/%s" % (dirname, modname)

        mod_imp_name = pathname.replace("/", ".")

        if mods.has_key(mod_imp_name):
            # If we've already imported mod_imp_name, don't import it again
            continue

        # ignore modules that we've already determined aren't valid modules
        if bad_mods.has_key(mod_imp_name):
            continue

        try:
            # Auto-detect and load all FuncModules
            blip =  __import__("%s%s" % ( mod_dir,mod_imp_name), globals(), locals(), [mod_imp_name])
            for obj in dir(blip):
                attr = getattr(blip, obj)
                if isclass(attr) and issubclass(attr, main_class):
                    logger.debug("Loading %s module" % attr)
                    if parent_class:
                        mods[mod_imp_name] = attr(parent_class)
                    else:
                        mods[mod_imp_name] = attr()

        except ImportError, e:
            # A module that raises an ImportError is (for now) simply not loaded.
            errmsg = _("Could not load %s module: %s")
            logger.warning(errmsg % (mod_imp_name, e))
            bad_mods[mod_imp_name] = True
            continue
        except:
            errmsg = _("Could not load %s module")
            logger.warning(errmsg % (mod_imp_name))
            bad_mods[mod_imp_name] = True
            continue

    return mods

if __name__ == "__main__":

    module_file_path = "/usr/lib/python2.5/site-packages/func/minion/modules/"
    bar = module_walker(module_file_path)
    print bar
    for f in bar:
        print f
        print os.path.basename(f)
        print os.path.split(f)
        g = f[len(module_file_path):]
        print g
        print os.path.split(g)

    print load_modules()
