import pymc3 as pm
import theano.tensor as tt

###Note - this specificiation is slightly different to the existing PyMC3 
###AR(1) model. This specification uses the correct variance for calculating 
###the likelihood of the first observation, which in real life does not start at
###zero. Here, the likelihood of the first observation is calculated using the 
###equation for the variance of an AR(1) process. 

class fixedAR1(pm.distributions.Continuous):
    """
    Autoregressive process with 1 lag.
    Parameters
    ----------
    k: tensor
       effect of lagged value on current value
    tau_e: tensor
       precision for innovations
    """

    def __init__(self, k, tau_e, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k = k = tt.as_tensor_variable(k)
        self.tau_e = tau_e = tt.as_tensor_variable(tau_e)
        self.tau = tau_e * (1 - k ** 2)
        self.mode = tt.as_tensor_variable(0.)

    def logp(self, x):
        """
        Calculate log-probability of AR1 distribution at specified value.
        Parameters
        ----------
        x: numeric
            Value for which log-probability is calculated.
        Returns
        -------
        TensorVariable
        """
        k = self.k
        tau_e = self.tau_e

        x_im1 = x[:-1]
        x_i = x[1:]
        
        ##removed this:
        #boundary = Normal.dist(0., tau=tau_e).logp
        ##added this:
        var_ar1 = 1 / ((1-k**2)*tau_e)
        sd_ar1 = tt.sqrt(var_ar1)
        boundary = pm.Normal.dist(0., sigma=sd_ar1).logp

        innov_like = pm.Normal.dist(k * x_im1, tau=tau_e).logp(x_i)
        return boundary(x[0]) + tt.sum(innov_like)
