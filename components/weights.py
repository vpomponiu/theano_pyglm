"""
Weight models for the Network GLM
"""
import theano
import theano.tensor as T
import numpy as np
from component import Component

from inference.hmc import hmc
from inference.slicesample import slicesample

def create_weight_component(model):
        type = model['network']['weight']['type'].lower()
        if type == 'constant':
            weight = ConstantWeightModel(model)
        elif type == 'gaussian':
            weight = GaussianWeightModel(model)
        else:
            raise Exception("Unrecognized weight model: %s" % type)
        return weight

class ConstantWeightModel(Component):
    def __init__(self, model):
        """ Initialize the filtered stim model
        """
        self.model = model
        N = model['N']

        prms = model['network']['weight']
        self.value = prms['value']
        
        # Define weight matrix
        self.W = self.value * T.ones((N,N))

        # Define log probability
        self.log_p = T.constant(0.0)

    def get_state(self):
        return {'W': self.W}
    
class GaussianWeightModel(Component):
    def __init__(self, model):
        """ Initialize the filtered stim model
        """
        self.model = model
        N = model['N']

        prms = model['network']['weight']
        self.mu = prms['mu'] * np.ones((N,N))
        self.sigma = prms['sigma'] * np.ones((N,N))
	
	# HACK: Implement refractory period by having negative mean on self loops
	if 'mu_refractory' in prms:
            self.mu[np.diag_indices(N)] = prms['mu_refractory']

	if 'sigma_refractory' in prms:
            self.sigma[np.diag_indices(N)] = prms['sigma_refractory']


        # Define weight matrix
        self.W_flat = T.dvector(name='W')
        self.W = T.reshape(self.W_flat,(N,N))

        # Define log probability
        self.log_p = T.sum(-1.0/(2.0*self.sigma**2) * (self.W-self.mu)**2)
        
    def sample(self):
        """
        return a sample of the variables
        """
        N = self.model['N']
        W = self.mu + self.sigma * np.random.randn(N,N)
        W_flat = np.reshape(W,(N**2,))
        return {str(self.W_flat): W_flat}

    def get_variables(self):
        """ Get the theano variables associated with this model.
        """
        return {str(self.W_flat): self.W_flat}
    
    def get_state(self):
        return {'W': self.W}
