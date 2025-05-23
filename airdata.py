#!/usr/bin/python3

# density -50C: 1.534 kg/m3  +40C:1.127kg/m3
# specific heat capacity -50C:1.005KJ/kg*K +40:1.005 KJ/kg*K
# roh = p/RT pressure / 287058 *  273,15+T isa press 101325Pa
import os
import sys
import math

""" Energy class for handling airdata calculations"""


def condensation_mass(energy):
    """Return equivalent mass of a given energy of condensing water vapor"""
    return float(energy) / 2490  # (g) 2490kJ/kg latent heat conversion


def condensation_energy(grams):
    """Return latent energy in a given mass of condensing water vapor"""
    return float(grams * 2490)  # 2490 kJ/kg condensate water


class Energy(object):
    def __init__(self):
        self.abs = None
        self.pw = None
        try:
            # GET AMBIENT PRESSURE##
            self.P_RED = 0.12  # hPa per meter
            self.press = float(os.popen("./forcast2.0.py pressure").read())
            self.alt = int(os.popen("./forcast2.0.py altitude").read())
            self.press = self.press - (self.alt * self.P_RED)  # Above sea lvl
        except ValueError:
            self.press = 1013.25
            err = open("airdata_error.log", "w")
            err.write("Airdata.py pressure error: " + str(sys.exc_info()))
            err.close()
            print("1013.25")
        except FileNotFoundError:
            print("error occurred getting current pressure ISA assumed")
            self.press = 1013.25
            err = open("airdata_error.log", "w")
            err.write("Airdata.py pressure error: " + str(sys.exc_info()))
            err.close()
            print("1013.25")
        # print"Ambient air pressure used:",self.press,"hPa"
        self.T = 273.15  # Zero degC expressed in Kelvin
        self.R = 287.058  # GAS CONSTANT for dry air for pressures in Pa
        self.density = lambda t: float(self.press * 100) / (self.R * (self.T + t))
        self.specific_heat = 1.005  # J/g*K
        self.humid = 0.50
        self.mass_const = 0.62198
        self.a = 6.1121

    # CALCULATE AIR DENSITY AT A GIVEN TEMPERATURE
    def get_mass(self, temp):
        return self.density(temp)  # kg/m3

    def temp_diff(self, energy, extract_temp, extract_flow):
        d_W = energy
        if energy < 0:
            d_W = -energy
            d_T = 0.01
        else:
            d_W = energy
            d_T = 0.01
        d_temp = 0.0
        while d_W > 0:
            density = self.density(extract_temp - d_temp)
            mass = density * extract_flow
            energy = mass * self.specific_heat * d_T
            d_W -= energy
            d_temp += d_T
        # print d_temp
        # math.log(self.T+extract_temp)
        # dt = (self.R*energy)/(self.press*100*self.specific_heat*math.log(self.T+extract_temp))
        # print dt
        return d_temp

    # CALCULATE THE ENERGY REQUIRED TO SENSIBLY RAISE OR LOWER TEMPERATURE FOR A GIVEN VOLUME
    def energy_flow(self, litres, high, low):
        total = 0
        step = 1
        if low > high:
            step = -1
            top = float(low)
            low = float(high)
            high = float(top)
        volume = float(litres) / 1000  # m3
        try:
            mass = (
                volume
                * self.press
                * 100
                / self.R
                * (math.log(self.T + high) - math.log(self.T + low))
                / (high - low)
            )
        except ZeroDivisionError:
            mass = 0
        energy = mass * self.specific_heat * (high - low) * 1000  # kg * J/gK * K = J
        return energy

    # RETURN MAXIMUM VAPOR CONTENT BY MASS
    def vapor_max(self, T):
        self.pw = 6.1121 * math.exp((18.678 - T / 234.5) * (T / (T + 257.14)))
        self.abs = (
            (self.pw * 2.16679) / (self.T + T) * 100
        )  # BUG WHY FACTOR 100//solved conversion from hPa
        # print self.abs,"g/m3 vapor_max"," temp:",T," sat. pressure:",self.pw
        return self.abs

    def sat_vapor_press(self, T):
        # Constants used acc NOAA std#
        if T < 0:
            a = 0.61115  # mBar
            c = 333.7  # C
            d = 279.82  # acc arden buck (1996)
            b = 23.036

        else:
            a = 0.61121  # mBar
            c = 234.5  # C
            d = 257.14  # acc arden buck (1996)
            b = 18.678
        self.pw = a * math.exp((b - T / c) * (T / (T + d)))  # kPa
        return self.pw  # kPa

    def vapor_mass(self, pw):  # return vapor mass from vapor partial pressure
        return (self.mass_const * pw) / (self.press - pw)

    def energy_to_pwdiff(self, energy, temp):
        mass_equiv = condensation_mass(energy)  # grams condensate per kilogram air
        # d_pw = self.press*100*(float(mass_equiv*0.001)/self.mass_const)
        d_pw = (mass_equiv / 1000 * self.press * 100) / (
            self.mass_const + mass_equiv
        )  # /(self.get_mass(temp)*1000)
        return d_pw

    def xchange_humid(self, T):
        content = (self.abs * self.humid) / 100
        rel = float(content / self.vapor_max(T)) * 100

    def dew_point(self, rh, temp):
        """CALCULATE DEWPOINT FROM temperature and relative humidity"""
        if rh == 100:
            return temp

        def gamma(relative, temperature):
            ps = math.log((float(relative) / 100) * self.sat_vapor_press(temperature))
            return ps

        # return (257.14*gamma(RH,temp))/(18.678-gamma(RH,temp))
        diff = -10000000
        t = temp
        reference = self.sat_vapor_press(t) * (float(rh) / 100)
        while diff < 0:
            diff = reference - self.sat_vapor_press(t)
            t = t - 0.1
        return t + 0.1


# Abs_hum  = C * Pw/T  C = 2.16679 gK/J Pw vapor press T temp in Kelvin
# Pw = A*10^(mT/T+Tn)  -->A=6.116441 m=7.591386 Tn=240.7263   vl -20C ->+50C
# ref Vaisala.com humidity conversion formulas
if "__main__" in __name__:
    air = Energy()
    if len(sys.argv) > 1:
        each = float(sys.argv[-1])
    else:
        each = 23
    for RH in range(1, 101, 1):
        print(each, "C", end=" ")
        print(
            RH,
            "% Dew:",
            round(air.dew_point(RH, each), 1),
            "C ",
            round(1000 * air.sat_vapor_press(each), 0),
            "Pa",
            round(1000 * air.sat_vapor_press(air.dew_point(RH, each)), 0),
            end=" ",
        )
        air.vapor_max(round(air.dew_point(RH, each), 1))
        print(round(air.pw * 100, 0))
    print("")
    # air.a = 16.500
    """for RH in range(1,100,8):
        print  RH,"%:",round(air.dew_point(RH,each),1)," ", 
        print """
    print(str(air.press.__round__(1)) + "hPa")
    top = 8.61
    low = 11.2
    missing_sensible = air.energy_flow(30, top, low)
    print("missing energy", missing_sensible, "J")
    print("equivalent mass:", condensation_mass(air.energy_flow(30, top, low)), "g")
    d_pw = air.sat_vapor_press(top) * 1000 - air.sat_vapor_press(low) * 1000
    print("d_part.pressure:", d_pw, "Pa")
    print(
        "satPtop:",
        air.sat_vapor_press(top) * 1000,
        "satPlow:",
        air.sat_vapor_press(low) * 1000,
    )
    print("d_Mass:", air.vapor_mass(d_pw), "g")
    mass = (
        air.vapor_mass(air.sat_vapor_press(top) * 1000) * 0.001
        - air.vapor_mass(air.sat_vapor_press(low) * 1000) * 0.001
    )
    print(mass)
    added_latent = condensation_energy(mass) * 30
    print("added latent Energy equivalent:", condensation_energy(mass) * 30, "J")
    print("Difference:", added_latent - missing_sensible, "J")
