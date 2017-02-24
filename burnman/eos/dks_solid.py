# This file is part of BurnMan - a thermoelastic and thermodynamic toolkit for the Earth and Planetary Sciences
# Copyright (C) 2012 - 2015 by the BurnMan team, released under the GNU
# GPL v2 or later.

from __future__ import absolute_import

import numpy as np
import scipy.optimize as opt
import warnings

from . import equation_of_state as eos
from ..tools import bracket


class DKS_S(eos.EquationOfState):
    """
    Base class for the finite strain solid equation of state detailed
    in :cite:`deKoker2013` (supplementary materials).
    """

    # Finite strain
    def __finite_strain(self, temperature, volume, params): # f(V), eq. S3a
        return (1./2.)*(np.power(params['V_0']/volume, 2./3.) - 1.0)        

    # Evaluate the integral of aK_T(V,To) from V1 to V2, assuming gamma = gamma_0*(V/Vo)^q
    def __int_aKt_dV(self, temperature, volume, params):
        return params['Cv']*params['grueneisen_0']/params['q_0']*(np.power(volume/params['V_0'], params['q_0']) - 1.)

    def __F_cmp(self, temperature, volume, params):
        f = self.__finite_strain(temperature, volume, params)
        K_0 = params['K_0']
        Kprime_0 = params['Kprime_0']
        Kdprime_0 = params['Kdprime_0']
        a3 = 3.*(Kprime_0 - 4.)
        a4 = 9.* ( K_0 * Kdprime_0 + Kprime_0 * (Kprime_0 - 7.) ) + 143.
        return 9.*K_0*params['V_0']*(f*f/2. + a3*f*f*f/6. + a4*f*f*f*f/24.)

    def __F_th(self, temperature, volume, params):
        F_th = -params['S_0']*(temperature - params['T_0'])  \
            - params['Cv']*(temperature*np.log(temperature/params['T_0']) \
                                 - (temperature - params['T_0'])) \
                                 - self.__int_aKt_dV(temperature, volume, params) * (temperature - params['T_0'])
        return F_th

    # Pressure
    def pressure(self, temperature, volume, params):
        f = self.__finite_strain(temperature, volume, params)
        n = params['n']
        K_0 = params['K_0']
        Kprime_0 = params['Kprime_0']
        Kdprime_0 = params['Kdprime_0']
        a3 = 3. * ( Kprime_0 - 4. )
        a4 = 9. * ( K_0 * Kdprime_0 + Kprime_0 * (Kprime_0 - 7.) ) + 143.
        return 3.*params['K_0']*np.power(1+2.*f, 2.5)*(f + a3*f*f/2. + a4/6.*f*f*f) \
            + params['Cv'] * (temperature - params['T_0']) \
            * self.grueneisen_parameter(0., temperature, volume, params) / volume


    def volume(self, pressure, temperature, params):
        _delta_pressure = lambda x, pressure, temperature, params: pressure - self.pressure(temperature, x, params)
        
        # we need to have a sign change in [a,b] to find a zero. Let us start with a
        # conservative guess:
        args = (pressure, temperature, params)
        try:
            sol = bracket(_delta_pressure, params['V_0'],
                          1.e-2 * params['V_0'], args)
        except ValueError:
            raise Exception(
                'Cannot find a volume, perhaps you are outside of the range of validity for the equation of state?')
        return opt.brentq(_delta_pressure, sol[0], sol[1], args=args)


    def isothermal_bulk_modulus(self, pressure,temperature, volume, params):
        """
        Returns isothermal bulk modulus :math:`[Pa]` 
        """
        return 0.

    def adiabatic_bulk_modulus(self, pressure, temperature, volume, params):
        """
        Returns adiabatic bulk modulus. :math:`[Pa]` 
        """
        return 0.

    def grueneisen_parameter(self, pressure, temperature, volume, params):
        """
        Returns grueneisen parameter. :math:`[unitless]` 
        """
        return params['grueneisen_0'] * \
            np.power(volume/params['V_0'], params['q_0'])

    def shear_modulus(self, pressure, temperature, volume, params):
        """
        Returns shear modulus. :math:`[Pa]` 
        """
        return 0.

    def heat_capacity_v(self, pressure, temperature, volume, params):
        """
        Returns heat capacity at constant volume. :math:`[J/K/mol]` 
        """
        return params['Cv']

    def heat_capacity_p(self, pressure, temperature, volume, params):
        """
        Returns heat capacity at constant pressure. :math:`[J/K/mol]` 
        """
        return 0.

    def thermal_expansivity(self, pressure, temperature, volume, params):
        """
        Returns thermal expansivity. :math:`[1/K]` 
        """
        return 0.

    def gibbs_free_energy( self, pressure, temperature, volume, params):
        """
        Returns the Gibbs free energy at the pressure and temperature of the mineral [J/mol]
        """
        G = self.helmholtz_free_energy( pressure, temperature, volume, params) + pressure * volume
        return G

    def entropy( self, pressure, temperature, volume, params):
        """
        Returns the entropy at the pressure and temperature of the mineral [J/K/mol]
        """
        S = params['S_0'] + self.__int_aKt_dV(temperature, volume, params) + params['Cv']*np.log(temperature/params['T_0'])
        return S 

    def enthalpy( self, pressure, temperature, volume, params):
        """
        Returns the enthalpy at the pressure and temperature of the mineral [J/mol]
        """
        
        return self.helmholtz_free_energy( pressure, temperature, volume, params) + \
               temperature * self.entropy( pressure, temperature, volume, params) + \
               pressure * self.volume( pressure, temperature, params)

    def helmholtz_free_energy( self, pressure, temperature, volume, params):
        """
        Returns the Helmholtz free energy at the pressure and temperature of the mineral [J/mol]
        """
        F = params['E_0'] - params['T_0']*params['S_0'] \
            + self.__F_cmp(temperature, volume, params) \
            + self.__F_th(temperature, volume, params)
        return F

    def internal_energy(self, pressure, temperature, volume, params):
        E = self.helmholtz_free_energy(pressure, temperature, volume, params) + \
            temperature*self.entropy(pressure, temperature, volume, params)
        return E

    def validate_parameters(self, params):
        """
        Check for existence and validity of the parameters
        """
  
        #check that all the required keys are in the dictionary
        expected_keys = ['V_0', 'T_0', 'E_0', 'S_0', 'K_0', 'Kprime_0', 'Kdprime_0', 'n', 'Cv', 'grueneisen_0', 'q_0']
        for k in expected_keys:
            if k not in params:
                raise KeyError('params object missing parameter : ' + k)
        
        #now check that the values are reasonable.  I mostly just
        #made up these values from experience, and we are only 
        #raising a warning.  Better way to do this? [IR]


