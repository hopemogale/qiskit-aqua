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
from qiskit.aqua.circuits import FixedValueComparator as Comparator


class TestFixedValueComparator(QiskitAquaTestCase):

    @parameterized.expand([
        # n, value, geq
        [1, 0, True],
        [1, 1, True],
        [2, -1, True],
        [2, 0, True],
        [2, 1, True],
        [2, 2, True],
        [2, 3, True],
        [2, 4, True],
        [3, 5, True],
        [4, 6, False]
    ])
    def test_fixed_value_comparator(self, num_state_qubits, value, geq):

        # initialize weighted sum operator factory
        comp = Comparator(num_state_qubits, value, geq)

        # initialize circuit
        q = QuantumRegister(num_state_qubits+1)
        if comp.required_ancillas() > 0:
            q_a = QuantumRegister(comp.required_ancillas())
            qc = QuantumCircuit(q, q_a)
        else:
            q_a = None
            qc = QuantumCircuit(q)

        # set equal superposition state
        qc.h(q[:num_state_qubits])

        # build circuit
        comp.build(qc, q, q_a)

        # run simulation
        job = execute(qc, BasicAer.get_backend('statevector_simulator'), shots=1)

        for i, a in enumerate(job.result().get_statevector()):

            prob = np.abs(a)**2
            if prob > 1e-6:
                # equal superposition
                self.assertEqual(True, np.isclose(1.0, prob * 2.0**num_state_qubits))
                b_value = '{0:b}'.format(i).rjust(qc.width(), '0')
                x = int(b_value[(-num_state_qubits):], 2)
                comp_result = int(b_value[-num_state_qubits-1], 2)
                if geq:
                    self.assertEqual(x >= value, comp_result == 1)
                else:
                    self.assertEqual(x < value, comp_result == 1)


if __name__ == '__main__':
    unittest.main()
