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

import unittest

from test.common import QiskitAquaTestCase

from parameterized import parameterized

import numpy as np

from qiskit import QuantumRegister, QuantumCircuit, BasicAer, execute
from qiskit.aqua.circuits import WeightedSumOperator


class TestWeightedSumOperator(QiskitAquaTestCase):

    @parameterized.expand([
        # n, weights, x, sum
        [1, [1], [0], 0],
        [1, [1], [1], 1],
        [1, [2], [0], 0],
        [1, [2], [1], 2],
        [3, [1, 2, 3], [0, 0, 0], 0],
        [3, [1, 2, 3], [0, 0, 1], 3],
        [3, [1, 2, 3], [0, 1, 0], 2],
        [3, [1, 2, 3], [1, 0, 0], 1],
        [3, [1, 2, 3], [0, 1, 1], 5],
        [3, [1, 2, 3], [1, 1, 1], 6]
    ])
    def test_weighted_sum_operator(self, num_state_qubits, weights, input, result):

        # initialize weighted sum operator factory
        sum_op = WeightedSumOperator(num_state_qubits, weights)

        # initialize circuit
        q = QuantumRegister(num_state_qubits + sum_op.get_required_sum_qubits(weights))
        if sum_op.required_ancillas() > 0:
            q_a = QuantumRegister(sum_op.required_ancillas())
            qc = QuantumCircuit(q, q_a)
        else:
            q_a = None
            qc = QuantumCircuit(q)

        # set initial state
        for i, x in enumerate(input):
            if x == 1:
                qc.x(q[i])

        # build circuit
        sum_op.build(qc, q, q_a)

        # run simulation
        job = execute(qc, BasicAer.get_backend('statevector_simulator'), shots=1)

        num_results = 0
        value = None
        for i, a in enumerate(job.result().get_statevector()):
            if np.abs(a)**2 >= 1e-6:
                num_results += 1
                b_value = '{0:b}'.format(i).rjust(qc.width(), '0')
                b_sum = b_value[(-len(q)):(-num_state_qubits)]
                value = int(b_sum, 2)

        # make sure there is only one result with non-zero amplitude
        self.assertEqual(num_results, 1)

        # compare to precomputed solution
        self.assertEqual(value, result)


if __name__ == '__main__':
    unittest.main()
