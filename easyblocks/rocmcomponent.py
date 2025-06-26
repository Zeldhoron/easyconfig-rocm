##
# Copyright 2009-2025 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for ROCm components, having a similar build structure,
implemented as an easyblock

@author: Jan Andre Reuter (jan@zyten.de)
"""
import contextlib
import os
import tempfile

from easybuild.framework.easyconfig import CUSTOM
from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.toolchains.compiler.clang import Clang
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.config import build_option
from easybuild.tools.filetools import mkdir, which
from easybuild.tools.modules import get_software_root
from easybuild.tools.environment import setvar


def list_to_cmake_arg(lst):
    """Convert iterable of strings to a value that can be passed as a CLI argument to CMake resulting in a list"""
    return "'%s'" % ';'.join(lst)


class EB_ROCmComponent(CMakeMake):
    """Support for building ROCm components"""

    @staticmethod
    def extra_options(extra_vars=None):
        """Extra easyconfig parameters for ROCmComponent"""
        extra_vars = CMakeMake.extra_options(extra_vars)
        extra_vars.update({
            'use_rocm_llvm_to_build': [True, "Use ROCm-LLVM to build package, uses toolchain compiler otherwise", CUSTOM],
            'hip_platform': ['amd', "Specify HIP platform. Allowed values: amd, nvidia", CUSTOM],
        })
        return extra_vars

    def configure_step(self, srcdir=None, builddir=None):
        """Prepare configuration to properly build ROCm component."""

        # If HIP platform is chosen to be nvidia, CUDA should be present in dependencies
        if self.cfg['hip_platform'] == 'nvidia':
            cuda_root = get_software_root('CUDA')
            if not cuda_root:
                raise EasyBuildError(f"CUDA is required to build {self.cfg.name} with NVIDIA GPU support!")
        elif self.cfg['hip_platform'] == 'amd':
            rocm_llvm_root = get_software_root('ROCm-LLVM')
            if not rocm_llvm_root:
                raise EasyBuildError(f"ROCm-LLVM is required to build {self.cfg.name} with AMD GPU support!")
        else:
            raise EasyBuildError(f"hip_platform parameter contains non-allowed value.")

        if self.cfg['use_rocm_llvm_to_build']:
            if build_option('rpath'):
                tmp_toolchain = Clang(name='Clang', version='1')
                tmp_toolchain.COMPILER_CC = 'amdclang'
                tmp_toolchain.COMPILER_CXX = 'amdclang++'
                tmp_toolchain.prepare_rpath_wrappers()

                cflags = os.getenv('CFLAGS', '')
                cxxflags = os.getenv('CXXFLAGS', '')
                setvar('CFLAGS', "%s %s" % (cflags, '-Wno-unused-command-line-argument'))
                setvar('CXXFLAGS', "%s %s" % (cxxflags, '-Wno-unused-command-line-argument'))

            amdclang_mock = which('amdclang')
            amdclangxx_mock = which('amdclang++')

            self.cfg['configopts'] += f'-DCMAKE_C_COMPILER={amdclang_mock} '
            self.cfg['configopts'] += f'-DCMAKE_CXX_COMPILER={amdclangxx_mock} '
            self.cfg['configopts'] += f'-DCMAKE_HIP_COMPILER={amdclangxx_mock} '

        self.cfg['configopts'] += f'-DHIP_PLATFORM={self.cfg["hip_platform"]} '
        amd_gfx_list =  ['gfx900', 'gfx906', 'gfx908']  
        if amd_gfx_list and self.cfg['hip_platform'] == 'amd':
            # For now, pass both AMDGPU_TARGETS and GPU_TARGETS, until AMD finally drops the former for all packages.
            self.cfg['configopts'] += f'-DAMDGPU_TARGETS={list_to_cmake_arg(amd_gfx_list)} '
            self.cfg['configopts'] += f'-DGPU_TARGETS={list_to_cmake_arg(amd_gfx_list)} '
        super().configure_step(srcdir, builddir)
