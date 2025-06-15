import pytest
import math
import sys
sys.path.append("..")
sys.path.append(".")

import math
import pytest

from airdata import Energy, condensation_mass, condensation_energy

# ----------------------------
# Unit tests for helper functions
# ----------------------------

def test_condensation_mass():
    # 2490 J of latent energy = 1 gram of water condensed
    assert condensation_mass(2490) == 1.0

def test_condensation_energy():
    # 1 gram of water = 2490 J of latent energy
    assert condensation_energy(1) == 2490.0


# ----------------------------
# Tests for the Energy class
# ----------------------------

@pytest.fixture
def air():
    return Energy()


def test_density_at_0C(air):
    # Air density at 0°C and 1013.25 hPa ≈ 1.292 kg/m³
    density = air.get_mass(0)
    assert 1.28 < density < 1.30, f"Expected approx. 1.292, got {density}"


def test_temp_diff_cooling(air):
    # Simulate removing 1000 J from air at 20°C with 1000 m3/s flow
    delta_temp = air.temp_diff(-1000, 20, 1000)
    # Expected temperature drop: Q = mcΔT; m = ρ * flow ≈ 1.2 * 1 = 1.2 kg
    # ΔT = Q / (mc) ≈ 1000 / (1.2 * 1005) ≈ 0.83°C
    assert 0.7 < delta_temp < 1.0


def test_energy_flow_heating(air):
    # Heat 1000L (1m³) of air from 20°C to 30°C
    energy = air.energy_flow(1000, 30, 20)
    # Estimate: m = ~1.2 kg (density), ΔT = 10°C, c = 1005 J/kgK
    # Q = mcΔT ≈ 1.2 * 1005 * 10 = ~12060 J
    assert 11000 < energy < 13000


def test_vapor_max(air):
    # Max vapor content at 30°C should be around 30.4 g/m³
    vm = air.vapor_max(30)
    assert 29 < vm < 32


def test_sat_vapor_press(air):
    # At 30°C, saturation vapor pressure ≈ 4.24 kPa (Arden Buck equation)
    pw = air.sat_vapor_press(30)
    assert 4.2 < pw < 4.3


def test_vapor_mass(air):
    # Example: 1.5 kPa vapor pressure, at ~1013.25 hPa total pressure
    pw = 1.5  # kPa
    vmass = air.vapor_mass(pw * 10)  # Convert to hPa for internal formula
    # Formula: (mass_const * pw) / (P - pw)
    expected = (0.62198 * 15) / (1013.25 - 15)
    assert math.isclose(vmass, expected, rel_tol=0.011)


def test_energy_to_pwdiff(air):
    # Energy equivalent to 10g of condensation
    energy = condensation_energy(10)  # 10g -> 24900 J
    assert energy == 24900
    d_pw = air.energy_to_pwdiff(energy, 20)
    # Expect partial pressure difference (Pa) to increase
    assert  94 < d_pw < 95


def test_dew_point_100_rh(air):
    # At RH = 100%, dew point = temperature
    dp = air.dew_point(100, 22)
    assert dp == 22.0


def test_dew_point_50_rh(air):
    # At 50% RH and 22°C, dew point is around 11°C (from standard calc)
    dp = air.dew_point(50, 22)
    assert 10 < dp < 12
