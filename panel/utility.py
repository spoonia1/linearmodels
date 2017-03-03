import functools
from collections import OrderedDict

import numpy as np
from numpy import diag, sqrt
from numpy.linalg import matrix_rank, eigh
from scipy.stats import chi2, f


class AttrDict(dict):
    """
    Dictionary-like object that exposes keys as attributes 
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def has_constant(x):
    """
    Parameters
    ----------
    x: ndarray
        Array to be checked for a constant (n,k)

    Returns
    -------
    const : bool
        Flag indicating whether x contains a constant or has column span with
        a constant
    """
    if np.any(np.all(x == 1, axis=0)):
        return True

    if np.any((np.ptp(x, axis=0) == 0) & ~np.all(x == 0, axis=0)):
        return True

    n = x.shape[0]
    aug_rank = matrix_rank(np.c_[np.ones((n, 1)), x])
    rank = matrix_rank(x)
    return aug_rank == rank


def inv_sqrth(x):
    """
    Matrix inverse square root

    Parameters
    ----------
    x : ndarray
        Real, symmetric matrix

    Returns
    -------
    invsqrt : ndarray
        Input to the power -1/2
    """
    vals, vecs = eigh(x)
    return vecs @ diag(1 / sqrt(vals)) @ vecs.T


class WaldTestStatistic(object):
    def __init__(self, stat, null, df, df_denom=None, name=None):
        self._stat = stat
        self._null = null
        self.df = df
        self.df_denom = df_denom
        self._name = name
        if df_denom is None:
            self.dist = chi2(df)
            self.dist_name = 'chi2({0})'.format(df)
        else:
            self.dist = f(df, df_denom)
            self.dist_name = 'f({0},{1})'.format(df, df_denom)

    @property
    def stat(self):
        return self._stat

    @property
    def pval(self):
        return 1 - self.dist.cdf(self.stat)

    @property
    def critical_values(self):
        return OrderedDict(zip(['10%', '5%', '1%'],
                               self.dist.ppf([.9, .95, .99])))

    @property
    def null(self):
        return self._null

    def __str__(self):
        name = '' if not self._name else self._name + '\n'
        msg = '{name}H0: {null}\nWaldTestStatistic(stat={stat}, ' \
              'pval={pval:0.3f}, dist={dist})'
        return msg.format(name=name, null=self.null, stat=self.stat,
                          pval=self.pval, dist=self.dist_name)

    def __repr__(self):
        return self.__str__() + '\nid={id}'.format(id=hex(id(self)))


def _proj(y, x):
    """
    Projection of y on x from y

    Parameters
    ----------
    x : ndarray
        Array to project onto (nobs by nvar)
    y : ndarray
        Array to project (nobs by nseries)

    Returns
    -------
    yhat : ndarray
        Projected values of y (nobs by nseries)
    """
    return x @ np.linalg.pinv(x) @ y


def _annihilate(y, x):
    """
    Remove projection of y on x from y

    Parameters
    ----------
    x : ndarray
        Array to project onto (nobs by nvar)
    y : ndarray
        Array to project (nobs by nseries)

    Returns
    -------
    eps : ndarray
        Residuals values of y minus y projected on x (nobs by nseries)
    """
    return y - _proj(y, x)


# cahced_property taken from bottle.py
# Copyright (c) 2016, Marcel Hellkamp.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
def update_wrapper(wrapper, wrapped, *a, **ka):
    try:
        functools.update_wrapper(wrapper, wrapped, *a, **ka)
    except AttributeError:
        pass


class CachedProperty(object):
    """ A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property. """

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, cls):
        if obj is None: return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value

cached_property = CachedProperty