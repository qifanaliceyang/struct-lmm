# -*- coding: utf-8 -*-
import pdb

import scipy as sp
import scipy.linalg as la
import scipy.stats as st
from limix_core.covar import FreeFormCov
from limix_core.gp import GP2KronSumLR


class OptimalRho():
    r"""
    Estimates proportion of genetic variance that is explained by interaction between the variant and the environments

    Parameters
    ----------
    y : (`N`, 1) ndarray
        phenotype vector
    x : (`N`, 1)
        SNP vector
    F : (`N`, L) ndarray
        fixed effect design for covariates.
    Env : (`N`, `K`)
        Environmental matrix (indviduals by number of environments)
    W : (`N`, `T`)
        design of random effect in the null model.
        By default, W is set to ``Env``.

    Examples
    --------
    This example shows how to run OptimalRho.
    .. doctest::

        >>> from numpy.random import RandomState
        >>> import scipy as sp
        >>> from struct_lmm.interpretation import OptimalRho
        >>> random = RandomState(1)
        >>>
        >>> # generate data
        >>> n = 20 # number samples
        >>> k = 4 # number environments
        >>>
        >>> y = random.randn(n, 1) # phenotype
        >>> x = 1. * (random.rand(n, 1) < 0.2) # genotype
        >>> E = random.randn(n, k) # environemnts
        >>> covs = sp.ones((n, 1)) # intercept
        >>>
        >>> rho = OptimalRho(y, x, F = covs, Env = E, W=E)
        >>> opt_rho = rho.calc_opt_rho()
        >>> print('%.4f' % opt_rho)
        0.0000
    """

    def __init__(self, y, x, F, Env, W=None):
        self.y = y
        self.x = x
        self.F = F
        self.Env = Env
        self.W = W
        if self.W is None: self.W = self.Env

    def calc_opt_rho(self):
        _covs = sp.concatenate([self.F, self.W, self.x], 1)
        xoE = self.x*self.Env
        gp=GP2KronSumLR(Y=self.y, F=_covs, A=sp.eye(1), Cn=FreeFormCov(1), G=xoE)
        gp.covar.Cr.setCovariance(1e-4 * sp.ones((1,1)))
        gp.covar.Cn.setCovariance(0.02 * sp.ones((1,1)))
        RV = gp.optimize(verbose=False)

        # var_xEEx = sp.tr(xEEx P)/(n-1) = sp.tr(PW (PW)^T)/(n-1) = (PW**2).sum()/(n-1)
        # W = xE

        # variance heterogenenty
        var_xEEx = ((xoE - xoE.mean(0))**2).sum()
        var_xEEx /= float(self.y.shape[0] - 1)
        v_het = gp.covar.Cr.K()[0, 0] * var_xEEx

        # variance persistent
        v_comm = sp.var(gp.b()[-1] * self.x)

        rho = v_het / (v_comm + v_het)

        return rho
