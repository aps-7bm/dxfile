#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Subclasses the h5py module for interacting with Data Exchange files.
"""


from __future__ import print_function
import logging
import h5py
import os
import sys


__author__ = 'David Vine'
__copyright__ = 'Copyright (c) 2015, UChicago Argonne, LLC.'
__docformat__ = 'restructuredtext en'
__platform__ = 'Unix'
__version__ = '1.6'
__all__ = ['File',
           'Entry']

py3 = sys.version_info[0] == 3
logger = logging.getLogger(__name__)


class File(h5py.File):

    """
    Interact with Data Exchange files.

    Methods
    -------
    create_top_level_group(self, group_name):
        Helper function for creating a top level group which will 
        update the ``implements`` group automagically.

    add_entry(self, dexen_ob, overwrite=False):
        This method is used to parse DataExchangeEntry objects and 
        add them to the DataExchangeFile.

    """

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)

        if kwargs['mode'] in ['w', 'a']:  # New File
            if not 'exchange' in self.keys():
                self.create_top_level_group('exchange')
        else:
            # Verify this file conforms to Data Exchange guidelines
            try:
                assert 'implements' in self.keys()
                assert 'exchange' in self.keys()
            except AssertionError:
                print(
                    'WARNING: File does not have either/both "implements" or "exchange" group')

    def __repr__(self):
        if not self.id:
            r = u'<Closed DataExchange file>'
        else:
            # Filename has to be forced to Unicode if it comes back bytes
            # Mode is always a "native" string
            filename = self.filename
            if isinstance(filename, bytes):  # Can't decode fname
                filename = filename.decode('utf8', 'replace')
            r = u'<DataExchange file "%s" (mode %s)>' % (os.path.basename(filename),
                                                         self.mode)
        if py3:
            return r
        return r.encode('utf8')

    def create_top_level_group(self, group_name):
        """
        Create a group in the file root and updates the ``implements`` 
        group accordingly. This method should ALWAYS be used to create 
        groups in the file root.
        """
        self.create_group(group_name)
        try:
            implements = self['/implements'].value
            if group_name not in implements.split(':'):
                del self['implements']
                self.create_dataset(
                    'implements', data=':'.join([implements, group_name]))
        except KeyError:
            self.create_dataset('implements', data=group_name)

    def add_entry(self, dexen_ob, overwrite=False):
        """
        This method is used to parse DataExchangeEntry objects and add 
        them to the DataExchangeFile.
        """
        if type(dexen_ob) != list:
            dexen_ob = [dexen_ob]

        for dexen in dexen_ob:

            # Does HDF5 path exist?
            path = dexen.root.split('/')
            try:
                path.remove('')
            except ValueError:
                pass
            if not path[0] in self.keys():
                self.create_top_level_group(path[0])

            root = dexen.root
            self.require_group('/'.join([root, getattr(dexen, 'entry_name')]))

            dsets = [ds for ds in dir(dexen) if not ds.startswith('__')]
            [dsets.remove(item)
             for item in ['entry_name', 'root', 'docstring']]

            for ds_name in dsets:
                if getattr(dexen, ds_name)['value'] is not None:
                    if 'dataset_opts' in getattr(dexen, ds_name).keys():
                        opts = getattr(dexen, ds_name)['dataset_opts']
                    else:
                        opts = {}
                    try:
                        ds = self['/'.join([root, getattr(dexen, 'entry_name')])].create_dataset(
                            ds_name, data=getattr(dexen, ds_name)['value'], **opts)
                        for key in getattr(dexen, ds_name).keys():
                            if key in ['value', 'docstring', 'dataset_opts']:
                                pass
                            else:
                                ds.attrs[key] = getattr(dexen, ds_name)[key]
                    except RuntimeError:
                        # Likely cause of runtime error is dataset already
                        # existing in file
                        dataset_exists = ds_name in self[
                            '/'.join([root, getattr(dexen, 'entry_name')])].keys()
                        if dataset_exists:
                            if not overwrite:
                                print(
                                    'WARNING: Dataset {:s} already exists. This entry has been skipped.'.format(ds_name))
                            else:
                                # The overwite flag is set so delete the
                                # existing dataset and write the new one in its
                                # place
                                del self[
                                    '/'.join([root, getattr(dexen, 'entry_name'), ds_name])]
                                ds = self['/'.join([root, getattr(dexen, 'entry_name')])].create_dataset(
                                    ds_name, data=getattr(dexen, ds_name)['value'], **opts)
                                for key in getattr(dexen, ds_name).keys():
                                    if key in ['value', 'docstring', 'dataset_opts']:
                                        pass
                                    else:
                                        ds.attrs[key] = getattr(
                                            dexen, ds_name)[key]

                        else:
                            raise


class Entry(object):

    """
    Interact with Data Exchange files.

    Methods
    -------
    _entry_definitions(self)
        Contains the archetypes for Data Exchange file entries.

    _generate_classes(self)
        This method is used to turn the Entry._entry_definitions into generate_classes
        which can be instantitated for hold data.
    """

    def __init__(self, **kwargs):
        self._entry_definitions()
        self._generate_classes()

    def _entry_definitions(self):
        """
        This method contains the archetypes for Data Exchange file entries.

        The syntax for an entry is:
            *'root': The HDF5 path where this entry will be created (e.g. '/measurement_3/sample' or '/exchange/').
            *'entry_name': The name of entry (e.g. 'monochromator' or 'sample_7'). It is a HDF5 Group.
            *'docstring': Describes this type of entry. E.g for sample: "The sample measured."
                                *This is used only for autogegnerating documentation for DataExchangeEntry.
                                *It does not get written to the DataExchangeFile.
            *'ENTRY':   An entry is a dataset with attributes under the 'name' group.
                        Each 'ENTRY' must have:
                            * value: The dataset
                        Each 'ENTRY' should have:
                            * units: Units for value - an attribute of the dataset
                            * docstring: Used for autogenerating documentation
                        Each 'ENTRY' can have (i.e optional):
                            *'dataset_opts': Options passed to the create_dataset function. E.g.:
                            *'dataset_opts': {'compression':'gzip', 'compression_opts':4}
                        Where a value is ``None`` this entry will not be added to the DataExchangeFile.
                        'ENTRY' can have any other parameter and these will be treated as HDF5 dataset attributes
        """
        self._exchange = {
            'root': 'exchange',
            'entry_name': '',
            'docstring': 'Used for grouping the results of the measurement',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the data contained inside'
            }
        }

        self._data = {
            'root': '/exchange',
            'entry_name': '',
            'docstring': 'The result of the measurement.',
            'data': {
                'value': None,
                'units': 'counts',
                'docstring': 'The result of the measurement.'
            },
        }

        self._sample = {
            'root': '/measurement',
            'entry_name': 'sample',
            'docstring': 'The sample measured.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Descriptive name of the sample.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the sample.'
            },
            'preparation_date': {
                'value': None,
                'units': 'text',
                'docstring': 'Date and time the sample was prepared.'
            },
            'chemical_formula': {
                'value': None,
                'units': 'text',
                'docstring': 'Sample chemical formula using the CIF format.'
            },
            'mass': {
                'value': None,
                'units': 'kg',
                'docstring': 'Mass of the sample.'
            },
            'concentration': {
                'value': None,
                'units': 'kgm^-3',
                'docstring': 'Mass/volume.'
            },
            'environment': {
                'value': None,
                'units': 'text',
                'docstring': 'Sample environment.'
            },
            'temperature': {
                'value': None,
                'units': 'kelvin',
                'docstring': 'Sample temperature.'
            },
            'temperature_set': {
                'value': None,
                'units': 'kelvin',
                'docstring': 'Sample temperature set point.'
            },
            'pressure': {
                'value': None,
                'units': 'kPa',
                'docstring': 'Sample pressure.'
            },
            'fatigue_cycle': {
                'value': None,
                'units': None,
                'docstring': 'Sample fatigue cycles.'
            },
            'thickness': {
                'value': None,
                'units': 'm',
                'docstring': 'Sample thickness.'
            },
            'tray': {
                'value': None,
                'units': 'text',
                'docstring': 'Sample position in the sample changer/robot.'
            },
            'comment': {
                'value': None,
                'units': 'text',
                'docstring': 'comment'
            }
        }

        self._experiment = {
            'root': '/measurement/sample',
            'entry_name': 'experiment',
            'docstring': 'This provides references to facility ids for the proposal, scheduled activity, and safety form.',
            'proposal': {
                'value': None,
                'units': 'text',
                'docstring': 'Proposal reference number. For the APS this is the General User Proposal number.'
            },
            'activity': {
                'value': None,
                'units': 'text',
                'docstring': 'Proposal scheduler id. For the APS this is the beamline scheduler activity id.'
            },
            'safety': {
                'value': None,
                'units': 'text',
                'docstring': 'Safety reference document. For the APS this is the Experiment Safety Approval Form number.'
            },
            'title': {
                'value': None,
                'units': 'text',
                'docstring': 'Experiment title. For the APS this is the proposal title assigned by the user.'
            },
        }

        self._experimenter = {
            'root': '/measurement/sample',
            'entry_name': 'experimenter',
            'docstring': 'Description of a single experimenter.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'User name.'
            },
            'role': {
                'value': None,
                'units': 'text',
                'docstring': 'User role.'
            },
            'affiliation': {
                'value': None,
                'units': 'text',
                'docstring': 'User affiliation.'
            },
            'address': {
                'value': None,
                'units': 'text',
                'docstring': 'User address.'
            },
            'phone': {
                'value': None,
                'units': 'text',
                'docstring': 'User phone number.'
            },
            'email': {
                'value': None,
                'units': 'text',
                'docstring': 'User email address.'
            },
            'facility_user_id': {
                'value': None,
                'units': 'text',
                'docstring': 'User badge number.'
            },
        }

        self._instrument = {
            'root': '/measurement',
            'entry_name': 'instrument',
            'docstring': 'All relevant beamline components status at the beginning of a measurement',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the instrument.'
            },
            'comment': {
                'value': None,
                'units': 'text',
                'docstring': 'comment'
            },
        }

        self._source = {
            'root': '/measurement/instrument',
            'entry_name': 'source',
            'docstring': 'The light source being used',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the facility.'
            },
            'datetime': {
                'value': None,
                'units': 'text',
                'docstring': 'Date and time source was measured.'
            },
            'beamline': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the beamline.'
            },
            'current': {
                'value': None,
                'units': 'A',
                'docstring': 'Electron beam current (A).'
            },
            'energy': {
                'value': None,
                'units': 'J',
                'docstring': 'Characteristic photon energy of the source (J). For an APS bending magnet this is 30 keV or 4.807e-15 J.'
            },
            'pulse_energy': {
                'value': None,
                'units': 'J',
                'docstring': 'Sum of the energy of all the photons in the pulse (J).'
            },
            'pulse_width': {
                'value': None,
                'units': 's',
                'docstring': 'Duration of the pulse (s).'
            },
            'mode': {
                'value': None,
                'units': 'text',
                'docstring': 'top-up'
            },
            'beam_intensity_incident': {
                'value': None,
                'units': 'phs^-1',
                'docstring': 'Incident beam intensity in (photons per s).'
            },
            'beam_intensity_transmitted': {
                'value': None,
                'units': 'phs^-1',
                'docstring': 'Transmitted beam intensity (photons per s).'
            },
        }

        self._attenuator = {
            'root': '/measurement/instrument',
            'entry_name': 'attenuator',
            'docstring': 'X-ray beam attenuator.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the attenuator.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description or composition of attenuator.'
            },
            'thickness': {
                'value': None,
                'units': 'm',
                'docstring': 'Thickness of attenuator along beam direction.'
            },
            'transmission': {
                'value': None,
                'units': 'None',
                'docstring': 'The nominal amount of the beam that gets through (transmitted intensity)/(incident intensity)'
            }
        }

        self._monochromator = {
            'root': '/measurement/instrument',
            'entry_name': 'monochromator',
            'docstring': 'X-ray beam monochromator.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the monochromator.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the monochromator'
            },
            'energy': {
                'value': None,
                'units': 'J',
                'docstring': 'Peak of the spectrum that the monochromator selects. When units is not defined this field is in J'
            },
            'energy_error': {
                'value': None,
                'units': 'J',
                'docstring': 'Standard deviation of the spectrum that the monochromator selects. When units is not defined this field is in J.'
            },
            'mono_stripe': {
                'value': None,
                'units': 'text',
                'docstring': 'Type of multilayer coating or crystal.'
            }
        }

        self._mirror = {
            'root': '/measurement/instrument',
            'entry_name': 'mirror',
            'docstring': 'X-ray beam mirror.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the mirror.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the mirror'
            },
            'angle': {
                'value': None,
                'units': 'rad',
                'docstring': 'Mirror incident angle'
            }
        }

        self._detector = {
            'root': '/measurement/instrument',
            'entry_name': 'detector',
            'docstring': 'X-ray detector.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the detector.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the detector'
            },
            'manufacturer': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector manufacturer.'
            },
            'model': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector model'
            },
            'serial_number': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector serial number.'
            },
            'firmware_version': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector firmware version.'
            },
            'software_version': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector software version.'
            },
            'bit_depth': {
                'value': None,
                'units': 'dimensionless',
                'docstring': 'The detector ADC bit depth.'
            },
            'pixel_size_x': {
                'value': None,
                'units': 'm',
                'docstring': 'Physical detector pixel size (m).'
            },
            'pixel_size_y': {
                'value': None,
                'units': 'm',
                'docstring': 'Physical detector pixel size (m).'
            },
            'actual_pixel_size_x': {
                'value': None,
                'units': 'm',
                'docstring': 'Pixel size on the sample plane (m).'
            },
            'actual_pixel_size_y': {
                'value': None,
                'units': 'm',
                'docstring': 'Pixel size on the sample plane (m).'
            },
            'dimension_x': {
                'value': None,
                'units': 'pixels',
                'docstring': 'The detector horiz. dimension.'
            },
            'dimension_y': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector vertical dimension.'
            },
            'binning_x': {
                'value': None,
                'units': 'pixels',
                'docstring': 'If the data are collected binning the detector x binning and y binning store the binning factor.'
            },
            'binning_y': {
                'value': None,
                'units': 'dimensionless',
                'docstring': 'If the data are collected binning the detector x binning and y binning store the binning factor.'
            },
            'operating_temperature': {
                'value': None,
                'units': 'dimensionless',
                'docstring': 'The detector operating temperature (K).'
            },
            'exposure_time': {
                'value': None,
                'units': 's',
                'docstring': 'The set detector exposure time (s).'
            },
            'delay_time': {
                'value': None,
                'units': 's',
                'docstring': 'Detector delay time (s). This is used in combination with a mechanical shutter.'
            },
            'stabilization_time': {
                'value': None,
                'units': 's',
                'docstring': 'Detector delay time (s). This is used during stop and go data collection to allow the sample to stabilize.'
            },
            'frame_rate': {
                'value': None,
                'units': 'fps',
                'docstring': 'The detector frame rate (fps).'
            },
            'shutter_mode': {
                'value': None,
                'units': 'text',
                'docstring': 'The detector shutter mode: global, rolling etc.'
            },
            'output_data': {
                'value': None,
                'units': 'text',
                'docstring': 'String HDF5 path to the exchange group where the detector output data is located.'
            },
            'counts_per_joule': {
                'value': None,
                'units': 'counts',
                'docstring': 'Number of counts recorded per each joule of energy received by the detector'
            },
            'basis_vectors': {
                'value': None,
                'units': 'fps',
                'docstring': 'A matrix with the basis vectors of the detector data.'
            },
            'corner_position': {
                'value': None,
                'units': 'fps',
                'docstring': 'The x, y and z coordinates of the corner of the first data element.'
            },
        }

        self._roi = {
            'root': '/measurement/instrument/detector',
            'entry_name': 'roi',
            'docstring': 'region of interest (ROI) of the image actually collected, if smaller than the full CCD.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'ROI name'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'ROI description'
            },
            'min_x': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Top left x pixel position'
            },
            'min_y': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Top left y pixel position'
            },
            'size_x': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Horizontal image size'
            },
            'size_y': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Vertical image size'
            }
        }

        self._objective = {
            'root': '/measurement/instrument/detection_system',
            'entry_name': 'objective',
            'docstring': 'microscope objective lenses used.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Lens name'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Lens description'
            },
            'manufacturer': {
                'value': None,
                'units': 'text',
                'docstring': 'Lens manufacturer'
            },
            'model': {
                'value': None,
                'units': 'text',
                'docstring': 'Lens model.'
            },
            'magnification': {
                'value': None,
                'units': 'dimensionless',
                'docstring': 'Lens specified magnification'
            },
            'numerical_aperture': {
                'value': None,
                'units': 'dimensionless',
                'docstring': 'The numerical aperture (N.A.) is a measure of the light-gathering characteristics of the lens.'
            }
        }

        self._scintillator = {
            'root': '/measurement/instrument/detection_system',
            'entry_name': 'scintillator',
            'docstring': 'scintillator used.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Scintillator name'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Scintillator description'
            },
            'manufacturer': {
                'value': None,
                'units': 'text',
                'docstring': 'Scintillator Manufacturer.'
            },
            'serial_number': {
                'value': None,
                'units': 'text',
                'docstring': 'Scintillator serial number.'
            },
            'scintillating_thickness': {
                'value': None,
                'units': 'm',
                'docstring': 'Scintillator thickness.'
            },
            'substrate_thickness': {
                'value': None,
                'units': 'm',
                'docstring': 'Scintillator substrate thickness.'
            }
        }


        self._sample_stack = {
            'root': '/measurement/instrument',
            'entry_name': 'sample',
            'docstring': 'Sample stack name',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Descriptive name of the sample stack.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the sample stack.'
            },
        }

        self._sample_stack_setup = {
            'root': '/measurement/instrument/sample',
            'entry_name': 'setup',
            'docstring': 'Tomography specific tag to store motor positions that are static during data collection.',
            'sample_x': {
                'value': None,
                'units': 'mm',
                'docstring': 'Initial position of the X stage under the rotary motor.'
            },
            'sample_y': {
                'value': None,
                'units': 'mm',
                'docstring': 'Initial position of the Y stage under the rotary motor.'
            },
            'sample_z': {
                'value': None,
                'units': 'mm',
                'docstring': 'Initial position of the Z stage under the rotary motor.'
            },
            'sample_xx': {
                'value': None,
                'units': 'mm',
                'docstring': 'Initial position of the X stage on top of the rotary motor.'
            },
            'sample_zz': {
                'value': None,
                'units': 'mm',
                'docstring': 'Initial position of the Z stage on top of the rotary motor.'
            },
            'detector_distance': {
                'value': None,
                'units': 'mm',
                'docstring': 'Sample to detector distance.'
            }
        }

        self._interferometer = {
            'root': '/measurement/instrument/',
            'entry_name': 'interferometer',
            'docstring': 'interferometer name',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Descriptive name of the interferometer.'
            },
            'description': {
                'value': None,
                'units': 'text',
                'docstring': 'Description of the interferometer.'
            },
        }
        self._interferometer_setup = {
            'root': '/measurement/instrument/interferometer/',
            'entry_name': 'setup',
            'docstring': 'Tomography specific tag to store interferometer parameters.',
            'grid_start': {
                'value': None,
                'units': 'mm',
                'docstring': 'Interferometer grid start.'
            },
            'grid_end': {
                'value': None,
                'units': 'mm',
                'docstring': 'Interferometer grid end.'
            },
            'number_of_grid_periods': {
                'value': None,
                'units': None,
                'docstring': 'Interferometer number of grid periods.'
            },
            'number_of_grid_steps': {
                'value': None,
                'units': None,
                'docstring': 'Interferometer number of grid steps.'
            }
        }

        self._process = {
            'root': '/process',
            'entry_name': '',
            'docstring': 'Describes parameters used to generate raw and processed data.',
            'name': {
                'value': None,
                'units': 'text',
                'docstring': 'Name of the simulation'
            },
        }

        self._acquisition = {
            'root': '/process',
            'entry_name': 'acquisition',
            'docstring': 'Tomography specific tag to store dynamic (per image) parameters.',
            'start_date': {
                'value': None,
                'units': 'text',
                'docstring': 'Date and time measurement starts.'
            },
            'end_date': {
                'value': None,
                'units': 'text',
                'docstring': 'Date and time measurement ends.'
            },
            'sample_position_x': {
                'value': None,
                'units': 'mm',
                'docstring': 'Vector containing the position of the sample axis x at each projection image collection.'
            },
            'sample_position_y': {
                'value': None,
                'units': 'mm',
                'docstring': 'Vector containing the position of the sample axis y at each projection image collection.'
            },
            'sample_position_z': {
                'value': None,
                'units': 'mm',
                'docstring': 'Vector containing the position of the sample axis z at each projection image collection.'
            },
            'sample_image_shift_x': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Vector containing the shift of the sample axis x at each projection on the detector plane.'
            },
            'sample_image_shift_y': {
                'value': None,
                'units': 'pixels',
                'docstring': 'Vector containing the shift of the sample axis y at each projection on the detector plane.'
            },
            'image_theta': {
                'value': None,
                'units': 'degree',
                'docstring': 'Vector containing the rotary stage angular position read from the encoder at each image.'
            },
            'scan_index': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the identifier assigned by beamline controls to each individual series of images or scan.'
            },
            'scan_date': {
                'value': None,
                'units': None,
                'docstring': 'Vector containing for each image the wall date/time at start of scan in iso 8601.'
            },
            'image_date': {
                'value': None,
                'units': 'time',
                'docstring': 'Vector containing the date/time each image was acquired in iso 8601.'
            },
            'time_stamp': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the relative time since scan_date in 1e-7 seconds.'
            },
            'image_number': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the the image serial number as assigned by the camera. Unique for each individual scan. Always starts at 0.'
            },
            'image_exposure_time': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the the measured exposure time in 1e-7 seconds (0.1us)'
            },
            'image_is_complete': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the boolen status of: is any pixel data missing?'
            },
            'shutter': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image the beamline shutter status: 0 for closed, 1 for open'
            },
            'image_type': {
                'value': None,
                'units': None,
                'docstring': 'Vector containin for each image contained in /exchange/data 0 for white, 1 for projection and 2 for dark'
            },
        }

        self._acquisition_setup = {
            'root': '/process/acquisition',
            'entry_name': 'setup',
            'docstring': 'Tomography specific tag to store static scan parameters.',
            'number_of_projections': {
                'value': None,
                'units': None,
                'docstring': 'Number of projections.'
            },
            'number_of_darks': {
                'value': None,
                'units': None,
                'docstring': 'Number of dark images.'
            },
            'number_of_whites': {
                'value': None,
                'units': None,
                'docstring': 'Number of white images.'
            },
            'number_of_inter_whites': {
                'value': None,
                'units': None,
                'docstring': 'Number of inter whites.'
            },
            'white_frequency': {
                'value': None,
                'units': None,
                'docstring': 'White frequency.'
            },
            'sample_in': {
                'value': None,
                'units': 'mm',
                'docstring': 'Position of the sample axis (x or y) used for taking the sample out of the beam during data collection.'
            },
            'sample_out': {
                'value': None,
                'units': 'mm',
                'docstring': 'Position of the sample axis (x or y) used for taking the sample out of the beam during the white field data collection.'
            },
            'rotation_start_angle': {
                'value': None,
                'units': 'degree',
                'docstring': 'Position of rotation axis at the end of data collection.'
            },
            'rotation_end_angle': {
                'value': None,
                'units': 'degree',
                'docstring': 'Position of rotation axis at the start of the data collection.'
            },
            'rotation_speed': {
                'value': None,
                'units': 'degree per second',
                'docstring': 'Rotation axis speed.'
            },
            'angular_step': {
                'value': None,
                'units': 'degree',
                'docstring': 'Rotation axis angular step used during data collection.'
            },
            'mode': {
                'value': None,
                'units': 'text',
                'docstring': 'Scan mode: continuos or stop-go.'
            },
            'comment': {
                'value': None,
                'units': 'text',
                'docstring': 'comment'
            },
        }

    def _generate_classes(self):
        """
        This method is used to turn the Entry._entry_definitions into generate_classes
        which can be instantitated for hold data.
        """

        def __init__(self, **kwargs):
            for kw in kwargs:
                setattr(self, kw, kwargs[kw])

        # Generate a class for each entry definition
        for entry_name in self.__dict__:
            try:
                if entry_name.startswith('_'):
                    entry_type = getattr(self, entry_name)
                    entry_name = entry_name[1:]
                    if entry_name not in Entry.__dict__.keys():
                        entry_type['__base__'] = Entry
                        entry_type['__name__'] = entry_type['entry_name']
                        entry_type['__init__'] = __init__
                        setattr(
                            Entry, entry_name, type(entry_type['entry_name'], (object,), entry_type))
            except:
                print("Unable to create Entry for {:s}".format(entry_name))
                raise

Entry()
