from collections import OrderedDict

import numpy as np
import astropy.units as u
import astropy.constants as ct
from astropy.modeling.blackbody import blackbody_nu

from .model import Model

def deriv_planck(x, T):
    """Derivative of the planck fuction."""
    aux1 = 2. * ct.h**2 * x**4 / (T**2 * ct.c**2 * ct.k_B)
    aux2 = np.exp(ct.h*x / (ct.k_B * T))
    deriv = aux1 * aux2/(aux2 - 1.)**2
    deriv = deriv.decompose()
    return deriv / u.sr

def validate_bb(params, constraints):
    for key, param in params.items():
        if key=='beta':
            assert constraints[key][0]<param<constraints[key][1]
            assert not hasattr(param, 'unit')
        else:
            assert constraints[key][0]<param.value<constraints[key][1]
            assert hasattr(param, 'unit')

class ModifiedBBCold(Model):
    """Modified blackbody cold component model.

    Attributes:
        params (dict): model parameters.
        units (dict): standard units for the model.
        constraints (tuple): constraints on model parameters.
    """
    constraints = OrderedDict([('T',(2.3,np.inf)), ('size',(0.,np.inf)), 
        ('nu0',(0.,np.inf)), ('beta',(0.5,4.))])

    def __init__(self, T, size, nu0, beta):
        params = OrderedDict()
        params['T'] = T
        params['size'] = size
        params['nu0'] = nu0
        params['beta'] = beta
        super(ModifiedBB, self).__init__(params)

    def validate(self, params):
        validate_bb(params, self.constraints)

    def model_function(self, x):
        """Modified black body cold component."""
        assert hasattr(x, 'unit')
        cold = self['size'] * blackbody_nu(x, self['T']) * \
                (1. - np.exp(-(x/self['nu0'])**self['beta']))
        return cold

    def deriv(self, x, yunit=u.Jy):
        # Components
        cold = self.model_function(x).to(yunit)

        # Blackbody functions
        bbcold = blackbody_nu(x, self['T'])

        # Derivatives
        d_size = cold / self['size']
        d_T = cold * deriv_planck(x, self['T']) / bbcold
        d_T = d_T.to(yunit/self.units['T'])
        d_beta = -self['size'] * bbcold * \
                np.exp(-(x/self['nu0'])**self['beta']) * \
                (x/self['nu0'])**self['beta'] * np.log(x/self['nu0'])
        d_beta = d_beta.to(yunit)
        d_nu0 = -self['beta']*(x/self['nu0'])**self['beta'] * \
                cold / (self['nu0']*(np.exp((x/self['nu0'])**self['beta'])-1.))
        d_nu0 = d_nu0.to(yunit/self.units['nu0'])

        return [d_T, d_size, d_nu0, d_beta]

class ModifiedBBWarm(Model):
    """Modified blackbody warm component model.

    Attributes:
        params (dict): model parameters.
        units (dict): standard units for the model.
        constraints (tuple): constraints on model parameters.
        dust (Dust): dust properties.
    """
    constraints = OrderedDict([('T',(2.3,np.inf)), ('size',(0.,np.inf)), 
        ('N',(0.,np.inf))])

    def __init__(self, dust, T, size, N):
        params = OrderedDict()
        params['T'] = T
        params['size'] = size
        params['N'] = N
        super(ModifiedBB, self).__init__(params)
        self.dust = dust

    def validate(self, params):
        validate_bb(params, self.constraints)

    def model_function(self, x, **kwargs):
        """Modified black body warm component."""
        assert hasattr(x, 'unit')
        assert 'nu0' in kwargs and hasattr(kwargs['nu0'], 'unit')
        assert 'beta' in kwargs and not hasattr(kwargs['beta'], 'unit')
        sigma = sigma_nu(x, rdg=1.E-2, mu=2.33)
        warm = self['size'] * blackbody_nu(x, self['T']) * \
                (1. - np.exp(-self['N']*sigma)) * \
                np.exp(-0.5 * (x/kwargs['nu0'])**kwargs['beta'])
        return warm

    def deriv(self, x, yunit=u.Jy, **kwargs):
        # Component
        warm = self.model_function(x, **kwargs).to(yunit)
        sigma = self.sigma_nu(x)

        # Blackbody functions
        bbwarm = blackbody_nu(x, self['T'])

        # Derivatives
        d_size =  warm / self['size']
        d_T = warm * deriv_planck(x, self['T']) / bbwarm 
        d_T = d_Tw.to(yunit/self.units['T'])
        d_N = sigma * warm / (np.exp(sigma*self['N']) - 1.)
        d_N = d_Nw.to(yunit/self.units['N'])

        return [d_T, d_size, d_N]

class ModifiedBBHot(ModifiedBBWarm):
    """Modified blackbody hot component model.

    Attributes:
        params (dict): model parameters.
        units (dict): standard units for the model.
        constraints (tuple): constraints on model parameters.
        dust (Dust): dust properties.
    """

    def model_function(self, x, **kwargs):
        """Modified black body warm component."""
        assert 'Nw' in kwargs and hasattr(kwargs['Nw'], 'unit')
        hot = super(ModifiedBBHot,self).model_function(s, **kwargs)
        sigma = sigma_nu(x, rdg=1.E-2, mu=2.33)
        hot = hot * np.exp(-0.5*kwargs['Nw']*sigma)
        return hot

class ModifiedBB(Model):
    """Modified blackbody model.

    Attributes:
        params (dict): model parameters.
        units (dict): standard units for the model.
        constraints (tuple): constraints on model parameters.
        dust (Dust): dust properties.
    """
    constraints = OrderedDict([('Tc',(2.3,np.inf)), ('Tw',(2.3,np.inf)),
        ('Th',(2.3,np.inf)), ('size_c',(0.,np.inf)), ('size_w',(0.,np.inf)),
        ('size_h',(0.,np.inf)), ('nu0',(0.,np.inf)), ('beta',(0.5,4.)),
        ('Nw',(0.,np.inf)), ('Nh',(0.,np.inf))])

    def __init__(self, dust, Tc, Tw, Th, size_c, size_w, size_h, nu0, beta, Nw,
            Nh):
        params = OrderedDict()
        params['Tc'] = Tc
        params['Tw'] = Tw
        params['Th'] = Th
        params['size_c'] = size_c
        params['size_w'] = size_w
        params['size_h'] = size_h
        params['nu0'] = nu0
        params['beta'] = beta
        params['Nw'] = Nw
        params['Nh'] = Nh
        super(ModifiedBB, self).__init__(params)
        self.dust = dust

    def validate(self, params):
        validate_bb(params, self.constraints)

    def sigma_nu(self, x, rdg=1.E-2, mu=2.33):
        """Cross section."""
        assert hasattr(x, 'unit')
        return rdg * mu * ct.m_p * self.dust.interpolate(x)

    def cold_component(self, x):
        """Modified black body cold component."""
        assert hasattr(x, 'unit')
        cold = self['size_c'] * blackbody_nu(x, self['Tc']) * \
                (1. - np.exp(-(x/self['nu0'])**self['beta']))
        return cold

    def warm_component(self, x, rdg=1.E-2, mu=2.33):
        """Modified black body warm component."""
        assert hasattr(x, 'unit')
        sigma = self.sigma_nu(x, rdg=1.E-2, mu=2.33)
        warm = self['size_w'] * blackbody_nu(x, self['Tw']) * \
                (1. - np.exp(-self['Nw']*sigma)) * \
                np.exp(-0.5 * (x/self['nu0'])**self['beta'])
        return warm

    def hot_component(self, x, rdg=1.e-2, mu=2.33):
        """Modified black body hot component."""
        sigma = self.sigma_nu(x, rdg=1.E-2, mu=2.33)
        hot = self['size_h'] * blackbody_nu(x, self['Th']) * \
                (1. - np.exp(-self['Nh']*sigma)) * \
                np.exp(-0.5*((x/self['nu0'])**self['beta']+self['Nw']*sigma))
        return hot

    def model_function(self, x):
        cold = self.cold_component(x) 
        warm = self.warm_component(x)
        hot = self.hot_component(x)
        return cold + warm + hot

    def deriv(self, x, yunit=u.Jy):
        # Components
        cold = self.cold_component(x).to(yunit)
        warm = self.warm_component(x).to(yunit)
        hot = self.hot_component(x).to(yunit)
        sigma = self.sigma_nu(x)

        # Blackbody functions
        bbcold = blackbody_nu(x, self['Tc'])
        bbwarm = blackbody_nu(x, self['Tw'])
        bbhot = blackbody_nu(x, self['Th'])

        d_size_c =  cold / self['size_c']
        d_size_w =  warm / self['size_w']
        d_size_h =  hot / self['size_h']
        d_Tc = cold * deriv_planck(x, self['Tc']) / bbcold
        d_Tc = d_Tc.to(yunit/self.units['Tc'])
        d_Tw = warm * deriv_planck(x, self['Tw']) / bbwarm 
        d_Tw = d_Tw.to(yunit/self.units['Tw'])
        d_Th = hot * deriv_planck(x, self['Th']) / bbhot 
        d_Th = d_Th.to(yunit/self.units['Th'])
        d_beta = -self['size_c'] * bbcold * \
                np.exp(-(x/self['nu0'])**self['beta']) * \
                (x/self['nu0'])**self['beta'] * np.log(x/self['nu0'])
        d_beta += -0.5*(x/self['nu0'])**self['beta'] * \
                np.log(x/self['nu0']) * (warm+hot)
        d_beta = d_beta.to(yunit)
        d_nu0 = -self['beta']*(x/self['nu0'])**self['beta'] * \
                cold / (self['nu0']*(np.exp((x/self['nu0'])**self['beta'])-1.))
        d_nu0 += 0.5*self['beta']*(x/self['nu0'])**self['beta'] / \
                self['nu0'] * (warm+hot)
        d_nu0 = d_nu0.to(yunit/self.units['nu0'])
        d_Nw = sigma * warm / (np.exp(sigma*self['Nw']) - 1.)
        d_Nw += -0.5*sigma * hot 
        d_Nw = d_Nw.to(yunit/self.units['Nw'])
        d_Nh = sigma * hot / (np.exp(sigma*self['Nh']) - 1.)
        d_Nh = d_Nh.to(yunit/self.units['Nh'])

        return [d_Tc, d_Tw, d_Th, d_size_c, d_size_w, d_size_h, d_nu0, d_beta,
                d_Nw, d_Nh]

