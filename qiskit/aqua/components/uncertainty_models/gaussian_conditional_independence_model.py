# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import numpy as np
from qiskit.aqua.components.uncertainty_models import MultivariateDistribution
from qiskit.aqua.components.uncertainty_models import NormalDistribution
from scipy.stats.distributions import norm
from qiskit.aqua.circuits.linear_y_rotation import LinearYRotation


class GaussianConditionalIndependenceModel(MultivariateDistribution):
    """
    The Gaussian Conditional Independence Model for Credit Risk
    Reference: https://arxiv.org/abs/1412.1183
    Dependency between individual risk variabels and latent variable is approximated linearly.
    """

    def __init__(self, n_normal, normal_max_value, p_zeros, rhos, i_normal=None, i_ps=None):
        """
        Constructor.

        The Gaussian Conditional Independence Model for Credit Risk
        Reference: https://arxiv.org/abs/1412.1183

        Args:
            n_normal (int): number of qubits to represent the latent normal random variable Z
            normal_max_value (float): min/max value to truncate the latent normal random variable Z
            p_zeros (list or array): standard default probabilities for each asset
            rhos (list or array): sensitivities of default probability of assets with respect to latent variable Z
            i_normal (list or array): indices of qubits to represent normal variable
            i_ps (list or array): indices of qubits to represent asset defaults
        """
        self.n_normal = n_normal
        self.normal_max_value = normal_max_value
        self.p_zeros = p_zeros
        self.rhos = rhos
        self.K = len(p_zeros)
        num_qubits = [n_normal] + [1]*self.K

        # set and store indices
        if i_normal is not None:
            self.i_normal = i_normal
        else:
            self.i_normal = range(n_normal)

        if i_ps is not None:
            self.i_ps = i_ps
        else:
            self.i_ps = range(n_normal, n_normal + self.K)

        # get normal (inverse) CDF and pdf
        F = lambda x: norm.cdf(x)
        F_inv = lambda q: norm.ppf(q)
        f = lambda x: norm.pdf(x)

        # set low/high values
        low = [-normal_max_value] + [0]*self.K
        high = [normal_max_value] + [1]*self.K

        # call super constructor
        super().__init__(num_qubits, low=low, high=high)

        # create normal distribution
        self._normal = NormalDistribution(n_normal, 0, 1, -normal_max_value, normal_max_value)

        # create linear rotations for conditional defaults
        self._slopes = np.zeros(self.K)
        self._offsets = np.zeros(self.K)
        self._rotations = []
        for k in range(self.K):

            psi = F_inv(p_zeros[k]) / np.sqrt(1 - rhos[k])

            # compute slope / offset
            slope = -np.sqrt(rhos[k]) / np.sqrt(1 - rhos[k])
            slope *= f(psi) / np.sqrt(1 - F(psi)) / np.sqrt(F(psi))
            offset = 2*np.arcsin(np.sqrt(F(psi)))

            # adjust for integer to normal range mapping
            offset += slope * (-normal_max_value)
            slope *= 2*normal_max_value / (2**n_normal - 1)

            self._offsets[k] = offset
            self._slopes[k] = slope

            lry = LinearYRotation(slope, offset, n_normal, i_state=self.i_normal, i_target=self.i_ps[k])
            self._rotations += [lry]

    def build(self, qc, q, q_ancillas=None, params=None):

        self._normal.build(qc, q, q_ancillas)
        for lry in self._rotations:
            lry.build(qc, q, q_ancillas)










