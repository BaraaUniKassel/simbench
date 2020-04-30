# -*- coding: utf-8 -*-

# Copyright (c) 2019 by University of Kassel, Tu Dortmund, RWTH Aachen University and Fraunhofer
# Institute for Energy Economics and Energy System Technology (IEE) Kassel and individual
# contributors (see AUTHORS file for details). All rights reserved.

import numpy as np
from pandas import Series
from pandapower import element_bus_tuples

__author__ = "smeinecke"


def convert_voltlvl_to_int(voltage_level):
    """ Returns voltage level names as int. """
    if voltage_level in ["EHV", "ehv", "UHV", "uhv"]:
        return 1
    elif voltage_level in ["EHV-HV", "ehv-hv", "UHV-HV", "uhv-hv", "EHVHV", "ehvhv", "UHVHV",
                           "uhvhv"]:
        return 2
    elif voltage_level in ["HV", "hv"]:
        return 3
    elif voltage_level in ["HV-MV", "hv-mv", "HVMV", "hvmv"]:
        return 4
    elif voltage_level in ["MV", "mv"]:
        return 5
    elif voltage_level in ["MV-LV", "mv-lv", "MVLV", "mvlv"]:
        return 6
    elif voltage_level in ["LV", "lv"]:
        return 7
    else:
        return int(voltage_level)


def convert_voltlvl_to_str(voltage_level):
    """ Returns voltage level names as string. """
    return ["EHV", "EHV-HV", "HV", "HV-MV", "MV", "MV-LV", "LV"][convert_voltlvl_to_int(
            voltage_level)-1]


def convert_voltlvl_names(voltage_levels, desired_format):
    """ Returns voltage level names in desired format.
    EXAMPLE:
        voltlvl_names = convert_voltlvl_names([1, 2, "hv", 4, 5, "ehv", 7], str)
    """
    if desired_format == str:
        if isinstance(voltage_levels, str) | (not hasattr(voltage_levels, "__iter__")):
            return convert_voltlvl_to_str(voltage_levels)
        else:
            names = []
            for voltage_level in voltage_levels:
                for voltage_level in voltage_levels:
                    names += [convert_voltlvl_to_str(voltage_level)]
                return names
    elif desired_format == int:
        if isinstance(voltage_levels, str) | (not hasattr(voltage_levels, "__iter__")):
            return convert_voltlvl_to_int(voltage_levels)
        else:
            names = []
            for voltage_level in voltage_levels:
                for voltage_level in voltage_levels:
                    names += [convert_voltlvl_to_int(voltage_level)]
                return names
    else:
        raise ValueError("desired_format must be str or int")


def _voltlvl_idx(net, element, voltage_level, branch_bus=None, vn_kv_limits=[145, 60, 1]):
    """ similar to voltlvl_idx, but for only one voltage_level """
    vn_kv_limits = [np.inf] + vn_kv_limits + [-np.inf]
    voltage_level = convert_voltlvl_names(voltage_level, int)
    lim_max = [0, 0, 1, 1, 2, 2, 3][voltage_level-1]
    lim_min = [1, 2, 2, 3, 3, 4, 4][voltage_level-1]
    Idx_bus = net.bus.index[(net.bus.vn_kv <= vn_kv_limits[lim_max]) &
                            (net.bus.vn_kv > vn_kv_limits[lim_min])]
    if element == "bus":
        return list(Idx_bus)

    if branch_bus is None and element not in ["trafo", "trafo3w"]:
        # for all other elements than trafos, take the first possibility
        for elm, bus_name in element_bus_tuples():
            if elm == element:
                branch_bus = bus_name
                break

    if element == "measurement":
        measurement_buses = Series(index=net.measurement.index)
        # bus
        bool_ = net.measurement.element_type == "bus"
        measurement_buses.loc[bool_] = net.measurement.element.loc[bool_]
        # line and trafo
        for branch, side in zip(["line", "line", "trafo", "trafo"], ["from", "to", "hv", "lv"]):
            bus = side + "_bus"
            bool1 = net.measurement.element_type == branch
            bool2 = net.measurement.side == side
            measurement_buses.loc[bool1 & bool2] = net[branch][bus].loc[net.measurement.element.loc[
                bool1 & bool2]].values
        measurement_buses = measurement_buses.astype(int)
        isin_Idx_bus = measurement_buses.isin(Idx_bus)

    elif branch_bus in net[element].columns:  # all other elements than measurement and bus
        isin_Idx_bus = net[element][branch_bus].isin(Idx_bus)

    else:
        raise KeyError("For net[%s] there is no column '%s'. Please" % (element, str(branch_bus)) +
                       " give 'branch_bus' an valid bus column name, e.g. 'hv_bus' or 'lv_bus'.")

    return list(net[element].index[isin_Idx_bus])


def voltlvl_idx(net, element, voltage_levels, branch_bus=None, vn_kv_limits=[145, 60, 1]):
    """
    Returns indices of elements with special voltage level.
    Even voltage_level numbers behave equally to both neighboring numbers, i.e. 4 == [3, 5] and
    "EHV-HV" == ["EHV", "HV"].

    EXAMPLE:
        hv_and_mv_buses = voltlvl_idx(net, "bus", 4)  # 4 == [3, 5]
        hv_and_mv_buses = voltlvl_idx(net, "bus", [3, 5])
        mv_loads = voltlvl_idx(net, "load", "MV")
        hvmv_trafos = voltlvl_idx(net, "trafo", "HV", branch_bus="hv_bus")
        hvmv_trafos = voltlvl_idx(net, "trafo", "MV", branch_bus="lv_bus")
        ehvhv_and_hvmv_trafos = voltlvl_idx(net, "trafo", 2, branch_bus="hv_bus")
        ehvhv_and_hvmv_trafos = voltlvl_idx(net, "trafo", [1, 3], branch_bus="hv_bus")
        ehvhv_and_hvmv_trafos = voltlvl_idx(net, "trafo", 4, branch_bus="lv_bus")
        ehvhv_and_hvmv_trafos = voltlvl_idx(net, "trafo", [3, 5], branch_bus="lv_bus")
        ehvhv_trafos = voltlvl_idx(net, "trafo", 2, branch_bus="lv_bus")
        ehv_measurements = voltlvl_idx(net, "measurement", "EHV")
    """
    if not net[element].shape[0]:
        return []

    if isinstance(voltage_levels, str) | (not hasattr(voltage_levels, "__iter__")):
        return _voltlvl_idx(net, element, voltage_levels, branch_bus=branch_bus,
                            vn_kv_limits=vn_kv_limits)
    else:
        Idx = []
        for voltage_level in voltage_levels:
            Idx += _voltlvl_idx(net, element, voltage_level, branch_bus=branch_bus,
                                vn_kv_limits=vn_kv_limits)
        return Idx


def get_voltlvl(voltage_values, vn_kv_limits=[145, 60, 1]):
    """ Returns an array of voltage levels as integer. """
    iter_ = hasattr(voltage_values, "__iter__")
    voltage_values = voltage_values if iter_ else [voltage_values]
    voltage_values = np.array(voltage_values)
    voltage_levels = np.ones(voltage_values.shape)
    for lim in vn_kv_limits:
        voltage_levels[voltage_values <= lim] += 2
    if iter_:
        return voltage_levels.astype(int)
    else:
        return int(voltage_levels[0])
