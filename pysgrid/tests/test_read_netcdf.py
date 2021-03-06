'''
Created on Apr 7, 2015

@author: ayan
'''

from __future__ import (absolute_import, division, print_function)

import unittest

from ..read_netcdf import (NetCDFDataset, parse_axes, parse_padding,
                           parse_vector_axis, find_grid_topology_var)
from .write_nc_test_files import roms_sgrid, wrf_sgrid_2d


class TestParseAxes(unittest.TestCase):
    def setUp(self):
        self.xy = 'X: xi_psi Y: eta_psi'
        self.xyz = 'X: NMAX Y: MMAXZ Z: KMAX'

    def test_xyz_axis_parse(self):
        result = parse_axes(self.xyz)
        expected = ('NMAX', 'MMAXZ', 'KMAX')
        self.assertEqual(result, expected)

    def test_xy_axis_parse(self):
        result = parse_axes(self.xy)
        expected = ('xi_psi', 'eta_psi', None)
        self.assertEqual(result, expected)


class TestParsePadding(unittest.TestCase):
    def setUp(self):
        self.grid_topology = 'some_grid'
        self.with_two_padding = 'xi_rho: xi_psi (padding: both) eta_rho: eta_psi (padding: low)'  # noqa
        self.with_one_padding = 'xi_v: xi_psi (padding: high) eta_v: eta_psi'
        self.with_no_padding = 'MMAXZ: MMAX NMAXZ: NMAX'

    def test_mesh_name(self):
        result = parse_padding(self.with_one_padding, self.grid_topology)
        mesh_topology = result[0].mesh_topology_var
        expected = 'some_grid'
        self.assertEqual(mesh_topology, expected)

    def test_two_padding_types(self):
        result = parse_padding(self.with_two_padding, self.grid_topology)
        expected_len = 2
        padding_datum_0 = result[0]
        padding_type = padding_datum_0.padding
        sub_dim = padding_datum_0.node_dim
        dim = padding_datum_0.face_dim
        expected_sub_dim = 'xi_psi'
        expected_padding_type = 'both'
        expected_dim = 'xi_rho'
        self.assertEqual(len(result), expected_len)
        self.assertEqual(padding_type, expected_padding_type)
        self.assertEqual(sub_dim, expected_sub_dim)
        self.assertEqual(dim, expected_dim)

    def test_one_padding_type(self):
        result = parse_padding(self.with_one_padding, self.grid_topology)
        expected_len = 1
        padding_datum_0 = result[0]
        padding_type = padding_datum_0.padding
        sub_dim = padding_datum_0.node_dim
        dim = padding_datum_0.face_dim
        expected_padding_type = 'high'
        expected_sub_dim = 'xi_psi'
        expected_dim = 'xi_v'
        self.assertEqual(len(result), expected_len)
        self.assertEqual(padding_type, expected_padding_type)
        self.assertEqual(sub_dim, expected_sub_dim)
        self.assertEqual(dim, expected_dim)

    def test_no_padding(self):
        self.assertRaises(ValueError,
                          parse_padding,
                          padding_str=self.with_no_padding,
                          mesh_topology_var=self.grid_topology
                          )


class TestParseVectorAxis(unittest.TestCase):
    def setUp(self):
        self.standard_name_1 = 'sea_water_y_velocity'
        self.standard_name_2 = 'atmosphere_optical_thickness_due_to_cloud'
        self.standard_name_3 = 'ocean_heat_x_transport_due_to_diffusion'

    def test_std_name_with_velocity_direction(self):
        direction = parse_vector_axis(self.standard_name_1)
        expected_direction = 'Y'
        self.assertEqual(direction, expected_direction)

    def test_std_name_without_direction(self):
        direction = parse_vector_axis(self.standard_name_2)
        self.assertIsNone(direction)

    def test_std_name_with_transport_direction(self):
        direction = parse_vector_axis(self.standard_name_3)
        expected_direction = 'X'
        self.assertEqual(direction, expected_direction)


# TestNetCDFDatasetWithNodes.
def test_finding_node_variables(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.find_node_coordinates('xi_psi eta_psi')
    expected = ('lon_psi', 'lat_psi')
    assert result == expected


def test_find_face_coordinates_by_location(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.find_coordinates_by_location('face', 2)
    expected = ('lon_rho', 'lat_rho')
    assert result == expected


def test_find_edge_coordinates_by_location(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.find_coordinates_by_location('edge1', 2)
    expected = ('lon_u', 'lat_u')
    assert result == expected


def test_find_grid_topology(roms_sgrid):
    result = find_grid_topology_var(roms_sgrid)
    expected = 'grid'
    assert result == expected


def test_find_variables_by_standard_name(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.find_variables_by_attr(standard_name='time')
    expected = ['time']
    assert result == expected


def test_find_variables_by_standard_name_none(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.find_variables_by_attr(standard_name='some standard_name')
    assert result == []


def test_sgrid_compliant_check(roms_sgrid):
    nc_ds = NetCDFDataset(roms_sgrid)
    result = nc_ds.sgrid_compliant_file()
    assert result


# TestNetCDFDatasetWithoutNodes
def test_node_coordinates(wrf_sgrid_2d):
    nc_ds = NetCDFDataset(wrf_sgrid_2d)
    node_coordinates = nc_ds.find_node_coordinates('west_east_stag south_north_stag')  # noqa
    assert node_coordinates is None


def test_find_variable_by_attr(wrf_sgrid_2d):
    nc_ds = NetCDFDataset(wrf_sgrid_2d)
    result = nc_ds.find_variables_by_attr(cf_role='grid_topology',
                                          topology_dimension=2)
    expected = ['grid']
    assert result == expected


def test_find_variable_by_nonexistant_attr(wrf_sgrid_2d):
    nc_ds = NetCDFDataset(wrf_sgrid_2d)
    result = nc_ds.find_variables_by_attr(bird='tufted titmouse')
    assert result == []
