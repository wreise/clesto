from ..basics import Module_element
from ..basics import SymmetricGroup_element
from ..basics import SymmetricRing_element, SymmetricRing

from ..eilenberg_zilber import Simplex, EilenbergZilber_element
from ..eilenberg_zilber import CubicalEilenbergZilber_element
from ..utils import pairwise

from itertools import chain, combinations, product, combinations_with_replacement
from operator import itemgetter
from functools import reduce
from math import floor, factorial


class Surjection_element(Module_element):
    """Elements in the surjection operad

    As defined in:

    [McS]: J. McClure, and J. Smith. "Multivariable cochain operations and little
    n-cubes." Journal of the American Mathematical Society 16.3 (2003): 681-704.

    [BF]: C. Berger, and B. Fresse. "Combinatorial operad actions on cochains."
    Mathematical Proceedings of the Cambridge Philosophical Society. Vol. 137.
    No. 1. Cambridge University Press, 2004.

    """

    default_convention = 'Berger-Fresse'

    def __init__(self, data=None, torsion=None, convention=None):
        """Initialize an instance of Surjection_element

        Create a new, empty Surjection_element object representing 0, and, if
        given, initialize a Surjection_element from a dict with tuple of int keys
        and int values.

        """
        def check_input_data(data):
            if not (isinstance(data, dict)
                    and all(isinstance(surj, tuple) for surj in data.keys())
                    and all(isinstance(i, int) for i in
                            chain.from_iterable(data.keys()))
                    ):
                raise TypeError(
                    'data type must be dict with tuple of int keys')

            if convention not in {None, 'Berger-Fresse', 'McClure-Smith'}:
                raise TypeError('convention must be Berger-Fresse or' +
                                'McClure-Smith')
        if data:
            check_input_data(data)
        if convention is None:
            convention = Surjection_element.default_convention
        self.convention = convention
        super(Surjection_element, self).__init__(data=data, torsion=torsion)

    def __str__(self):
        string = super().__str__()
        return string.replace(', ', ',')

    @property
    def arity(self):
        """Arity of self

        Defined as None if self is not homogeneous. The arity of a basis
        surjection agrees with the max value it attains.

        >>> Surjection_element({(1,2,1,3,1): 1}).arity
        3

        """
        if not self:
            return None
        arities = set(max(surj) for surj in self.keys())
        if len(arities) == 1:
            return arities.pop()
        return None

    @property
    def degree(self):
        """Degree of self

        Defined as None if self is not homogeneous. The degree of a basis
        surjection agrees with the cardinality of its domain minus its arity.


        >>> Surjection_element({(1,2,1,3,1): 1}).arity
        3

        """
        if not self:
            return None
        degs = set(len(surj) - max(surj) for surj in self.keys())
        if len(degs) == 1:
            return degs.pop()
        return None

    @property
    def complexity(self):
        """Returns the complexity of self, defined as None if self is
        not homogeneous.

        For elements in arity 2, the complexity agrees with the degree. For higher
        arity elements, it is the max of its arity 2 components.

        >>> Surjection_element({(1,2,1,3,1): 1}).complexity
        1

        """
        complexities = [0]
        for key in self.keys():
            for i, j in combinations(range(1, max(key) + 1), 2):
                r = tuple(k for k in key if k == i or k == j)
                cpxty = len([p for p, q in pairwise(r) if p != q]) - 1
                complexities.append(cpxty)

        return max(complexities)

    def boundary(self):
        """boundary of self

        Up to signs, it is defined by taking the sum of all elements
        obtained by removing one entry at the time.
        The sign of each summand depends on the convention, either
        'McClure-Smith' or 'Berger-Fresse'. See [McCS] and [BF] for
        details.

        >>> s = Surjection_element({(1,2,1,3,1,3): 1})
        >>> print(s.boundary())
        (2,1,3,1,3) - (1,2,3,1,3) - (1,2,1,3,1)

        """
        answer = self.zero()

        if self.torsion == 2:
            for k in self.keys():
                for idx in range(0, len(k)):
                    bdry_summand = k[:idx] + k[idx + 1:]
                    if k[idx] in bdry_summand:
                        answer += self.create({bdry_summand: 1})
            return answer

        if self.convention == 'Berger-Fresse':
            for k, v in self.items():
                # determining the signs of the summands
                signs = {}
                alternating_sign = 1
                for idx, i in enumerate(k):
                    if i in k[idx + 1:]:
                        signs[idx] = alternating_sign
                        alternating_sign *= (-1)
                    elif i in k[:idx]:
                        occurs = (pos for pos, j in enumerate(k[:idx]) if i == j)
                        signs[idx] = signs[max(occurs)] * (-1)
                    else:
                        signs[idx] = 0

                # computing the summands
                for idx in range(0, len(k)):
                    bdry_summand = k[:idx] + k[idx + 1:]
                    if k[idx] in bdry_summand:
                        answer += self.create({bdry_summand: signs[idx] * v})

        if self.convention == 'McClure-Smith':
            for k, v in self.items():
                sign = 1
                for i in range(1, max(k) + 1):
                    for idx in (idx for idx, j in enumerate(k) if j == i):
                        new_k = k[:idx] + k[idx + 1:]
                        if k[idx] in new_k:
                            answer += answer.create({new_k: v * sign})
                        sign *= -1
                    sign *= -1

        return answer

    def __rmul__(self, other):
        """Left action: other * self

        Left multiplication by a symmetric group element or an integer.

        >>> surj = Surjection_element({(1,2,3,1,2): 1})
        >>> print(- surj)
        - (1,2,3,1,2)
        >>> rho = SymmetricRing_element({(2,3,1): 1})
        >>> print(rho * surj)
        (2,3,1,2,3)

        """

        def check_input(self, other):
            if not isinstance(other, SymmetricRing_element):
                raise TypeError(
                    f'Type int or SymmetricRing_element not {type(other)}')
            if self.torsion != other.torsion:
                raise TypeError('Unequal torsion attribute')
            if self.arity != other.arity:
                raise TypeError('Unequal arity attribute')

        def sign(perm, surj, convention):
            if convention == 'Berger-Fresse':
                return 1
            assert convention == 'McClure-Smith'
            weights = [surj.count(i) - 1 for
                       i in range(1, max(surj) + 1)]
            sign_exp = 0
            for idx, i in enumerate(perm):
                right = [weights[perm.index(j)] for
                         j in perm[idx + 1:] if i > j]
                sign_exp += sum(right) * weights[idx]
            return (-1)**(sign_exp % 2)

        if isinstance(other, int):
            return super().__rmul__(other)

        check_input(self, other)

        answer = self.zero()
        for (k1, v1), (k2, v2) in product(self.items(), other.items()):
            new_key = tuple(k2[i - 1] for i in k1)
            new_sign = sign(k2, k1, self.convention)
            answer += self.create({new_key: new_sign * v1 * v2})
        return answer

    def orbit(self, representation='trivial'):
        """Returns the preferred element in the symmetric orbit of an element.

        The preferred representative in the orbit of basis surjections is the
        one satisfying that the first occurence of each integer appear in
        increasing order.

        The representation used can be either 'trivial' or 'sign'.

        >>> s = Surjection_element({(1,3,2): 1})
        >>> print(s.orbit(representation='trivial'))
        (1,2,3)
        >>> print(s.orbit(representation='sign'))
        - (1,2,3)

        """
        def sign(permutation, representation):
            if representation == 'trivial':
                return 1
            if representation == 'sign':
                return permutation.sign

        answer = self.zero()
        for k, v in self.items():
            seen = []
            for i in k:
                if i not in seen:
                    seen.append(i)
            permutation = SymmetricGroup_element(seen).inverse()
            new_v = sign(permutation, representation) * v
            answer += permutation * self.create({k: new_v})

        return answer

    def __call__(self, other, coord=1):
        """Action on an element in the normalized chains of a standard
        cube or simplex represented by an arity 1 element in the (cubical)
        Eilenberg-Zilber operad.

        >>> from clesto.eilenberg_zilber import EilenbergZilber
        >>> s = Surjection_element({(1,2,1):1}, convention='McClure-Smith')
        >>> x = EilenbergZilber.standard_element(2)
        >>> print(s(x))
        - ((0,1,2),(0,1)) + ((0,2),(0,1,2)) - ((0,1,2),(1,2))

        >>> from clesto.eilenberg_zilber import CubicalEilenbergZilber
        >>> s = Surjection_element({(1,2,1):1})
        >>> x = CubicalEilenbergZilber.standard_element(2)
        >>> print(s(x))
        - ((2,2),(1,2)) + ((2,1),(2,2)) + ((0,2),(2,2)) - ((2,2),(2,0))

        """

        def check_input(self, other, coord=1):
            if self.degree is None or self.arity is None:
                raise TypeError('defined for homogeneous surjections')
            if other.arity < coord:
                raise TypeError(f'arity = {other.arity} < coord = {coord}')
            if self.torsion != other.torsion:
                raise TypeError('Unequal torsion attribute')

        def compute_sign(k1, k2):
            """Returns the sign associated to a pair."""
            def ordering_sign(permu, weights):
                """Returns the exponent of the Koszul sign of the given
                permutation acting on the elements of degrees given by the
                list of weights

                """
                sign_exp = 0
                for idx, j in enumerate(permu):
                    to_add = [weights[permu.index(i)] for
                              i in permu[idx + 1:] if i < j]
                    sign_exp += weights[idx] * sum(to_add)
                return sign_exp % 2

            def action_sign(ordered_k1, ordered_weights):
                """Given a ordered tuple [1,..,1, 2,...,2, ..., r,...,r]
                and weights [w_1, w_2, ..., w_{r+d}] of the same length, gives
                the kozul sign obtained by inserting from the left a weight 1
                operator between equal consecutive elements.

                """
                sign_exp = 0
                for idx, (i, j) in enumerate(pairwise(ordered_k1)):
                    if i == j:
                        sign_exp += sum(ordered_weights[:idx + 1])
                return sign_exp % 2

            sign_exp = 0
            weights = [e.dimension % 2 for e in k2]
            inv_ordering_permu = [pair[0] for pair in
                                  sorted(enumerate(k1), key=itemgetter(1))]
            ordering_permu = tuple(inv_ordering_permu.index(i)
                                   for i in range(len(inv_ordering_permu)))
            sign_exp += ordering_sign(ordering_permu, weights)
            ordered_k1 = list(sorted(k1))
            ordered_weights = [weights[i] for i in inv_ordering_permu]
            sign_exp += action_sign(ordered_k1, ordered_weights)
            return (-1)**sign_exp

        def simplicial(self, other, coord):
            """Action on Eilenberg-Zilber elements."""
            answer = other.zero()
            times = self.arity + self.degree - 1
            pre_join = other.iterated_diagonal(times, coord)
            for (k1, v1), (k2, v2) in product(self.items(), pre_join.items()):
                i, j = coord - 1, coord + len(k1) - 1
                left, k2, right = k2[:i], k2[i:j], k2[j:]
                new_k = []
                zero_summand = False
                for i in range(1, max(k1) + 1):
                    to_join = (spx for idx, spx in enumerate(k2)
                               if k1[idx] == i)
                    joined = Simplex(reduce(lambda x, y: x + y, to_join))
                    if joined.is_degenerate():
                        zero_summand = True
                        break
                    new_k.append(joined)

                if not zero_summand:
                    if self.torsion == 2:
                        sign = 1
                    else:
                        sign = compute_sign(k1, k2)
                        deg_left = sum(len(spx) - 1 for spx in left) % 2
                        sign *= (-1)**(deg_left * self.degree)

                    answer += answer.create({left + tuple(new_k) + right:
                                             sign * v1 * v2})
            return answer

        def cubical(self, other):
            """Action on cubical Eilenberg-Zilber elements."""
            answer = other.zero()
            pre_join = other.iterated_diagonal(self.arity + self.degree - 1)
            for (k1, v1), (k2, v2) in product(self.items(), pre_join.items()):
                to_dist = []
                zero_summand = False
                for i in range(1, max(k1) + 1):
                    key_to_join = tuple(cube for idx, cube in enumerate(k2)
                                        if k1[idx] == i)
                    joined = other.create({key_to_join: 1}).join()
                    if not joined:
                        zero_summand = True
                        break
                    to_dist.append(joined)

                if not zero_summand:
                    if self.torsion == 2:
                        sign = 1
                    else:
                        sign = compute_sign(k1, k2)

                    items_to_dist = [summand.items() for summand in to_dist]
                    for pairs in product(*items_to_dist):
                        new_k = reduce(lambda x, y: x + y, (pair[0] for pair in pairs))
                        new_v = reduce(lambda x, y: x * y, (pair[1] for pair in pairs))
                        to_add = answer.create({tuple(new_k): sign * new_v * v1 * v2})
                        answer += to_add
            return answer

        if not self or not other:
            return other.zero()

        check_input(self, other, coord=1)

        if isinstance(other, EilenbergZilber_element):
            if self.convention != 'McClure-Smith':
                raise NotImplementedError
            return simplicial(self, other, coord)
        elif isinstance(other, CubicalEilenbergZilber_element):
            return cubical(self, other)
        else:
            raise NotImplementedError

    def compose(self, other, position):
        """Operadic compositions: self o_position other

        We think of other being inserted into self and in the Berger-Fresse
        convention this pair is ordered: self tensor other.

        From [BF] 1.6.2:

        >>> x = Surjection_element({(1,2,1,3): 1}, convention='Berger-Fresse')
        >>> y = Surjection_element({(1,2,1): 1}, convention='Berger-Fresse')
        >>> print(x.compose(y, 1))
        (1,3,1,2,1,4) - (1,2,3,2,1,4) - (1,2,1,3,1,4)

        """
        def bf_sign(p1, k1, p2, k2):
            """Sign associated to the Berger-Fresse composition."""

            def caesuras(k):
                """Returns the caesuras of a basis element."""
                caesuras = []
                for idx, i in enumerate(k):
                    if i in k[idx + 1:]:
                        caesuras.append(idx)
                return caesuras

            def weights(cae, p):
                """Returns the weights of the splitting knowing the caesuras."""
                weights = []
                for i, j in pairwise(p):
                    closed_open = len([e for e in cae if i <= e < j])
                    weights.append(closed_open)
                return [value % 2 for value in weights]

            p1 = [0] + p1 + [len(k1) - 1]
            cae1 = caesuras(k1)
            w1 = weights(cae1, p1)
            cae2 = caesuras(k2)
            w2 = weights(cae2, p2)
            sign_exp = 0
            for idx, w in enumerate(w2):
                if w:
                    sign_exp += sum(w1[idx + 1:]) % 2
            return (-1) ** sign_exp

        def ms_sign(positions, k1, p, k2):
            raise NotImplementedError

        answer = self.zero()
        for (k1, v1), (k2, v2) in product(self.items(), other.items()):
            positions = [idx for idx, j in enumerate(k1) if j == position]
            for p in combinations_with_replacement(
                    range(len(k2)), len(positions) - 1):
                p = (0,) + p + (len(k2) - 1,)
                split = []
                for a, b in pairwise(p):
                    split.append(tuple(k2[a:b + 1]))
                to_insert = (tuple(j + position - 1 for j in part) for part in split)
                new_k = list()
                for j in k1:
                    if j < position:
                        new_k.append(j)
                    elif j == position:
                        new_k += next(to_insert)
                    else:
                        new_k.append(j + other.arity - 1)

                if self.torsion == 2:
                    sign = 1
                elif self.convention == 'Berger-Fresse':
                    sign = bf_sign(positions, k1, p, k2)
                elif self.convention == 'McClure-Smith':
                    sign = ms_sign()

                answer += answer.create({tuple(new_k): v1 * v2 * sign})

        return answer

    def suspension(self):
        """Returns the image in the suspension of the surjection operad

        Given a basis element u in arity r and degree d the suspension is
        in degree d-r+1 and is 0 if (u(1),...,u(r)) is not a permutation
        and sgn(u(1),...,u(r)) (u(r),...,u(r+d)) otherwise.

        >>> x = Surjection_element({(1,3,2,1,2):1}, convention='Berger-Fresse')
        >>> print(x.suspension())
        - (2,1,2)

        """
        if not self:
            return self

        if self.arity is None or self.degree is None:
            raise TypeError('defined for homogeneous elements only')

        if self.convention != 'Berger-Fresse':
            raise NotImplementedError

        answer = self.zero()
        for k, v in self.items():
            nonzero = False
            try:
                p = SymmetricGroup_element(k[:self.arity])
                sign = p.sign
                nonzero = True
            except TypeError:
                pass
            if nonzero:
                answer += self.create({k[self.arity - 1:]: v * sign})

        return answer

    def _reduce_rep(self):
        """Sets to 0 all degenerate surjections."""
        # removes non-surjections
        zeros = list()
        for k in self.keys():
            if set(k) != set(range(1, max(k) + 1)):
                zeros.append(k)
        for k in zeros:
            del self[k]

        # removes keys w/ equal consecutive values
        for k, v in self.items():
            for i in range(len(k) - 1):
                if k[i] == k[i + 1]:
                    self[k] = 0

        super()._reduce_rep()


class Surjection():
    """Class producing instances of Surjection_elements of interest."""

    @staticmethod
    def steenrod_product(arity, degree, torsion=None,
                         convention=Surjection_element.default_convention):
        """Returns a representative of the requested Steenrod product

        Constructed recursively by mapping the minimal resolution W(r)
        of Z[S_r] to Surj(r). We use the chain homotopy equivalence
        of Surj(r) and Z defined using the chain contraction (i, p, s)
        relating Surj(r-1) and Surj(r).

        """
        def i(surj, iterate=1):
            """Inclusion of Surj(r) into Surj(r+1)

            Defined by appending 1 at the start of basis elements and
            raising the value of all other entries by 1."""

            if iterate == 1:
                answer = surj.zero()
                for k, v in surj.items():
                    answer += answer.create(
                        {(1,) + tuple(j + 1 for j in k): v})
                return answer
            if iterate > 1:
                return i(i(surj, iterate=iterate - 1))

        def p(surj, iterate=1):
            """Projection of Surj(r) to Surj(r-1)

            Defined by removing 1 from a basis element with only one
            occurence of value 1 and substracting 1 from all other entries.

            """
            if iterate == 1:
                answer = surj.zero()
                for k, v in surj.items():
                    if k.count(1) == 1:
                        idx = k.index(1)
                        new_k = (tuple(j - 1 for j in k[:idx]) +
                                 tuple(j - 1 for j in k[idx + 1:]))
                        answer += answer.create({new_k: v})
                return answer
            if iterate > 1:
                return p(p(surj, iterate=iterate - 1))

        def s(surj):
            """Chain homotopy from the identity to the composition pi

            Explicitly, id - ip = ds + sd."""

            answer = surj.zero()
            for k, v in surj.items():
                answer += answer.create({(1,) + tuple(j for j in k): v})
            return answer

        def h(surj):
            """Chain homotopy from the identiy to i...i p..p

            In Surj(r), realizing its contractibility to Surj(1).

            """
            answer = s(surj)
            for r in range(1, arity - 1):
                answer += i(s(p(surj, r)), r)
            return answer

        operators = {
            0: SymmetricRing.norm_element(arity),
            1: SymmetricRing.transposition_element(arity)
        }

        def psi(arity, degree, convention=convention):
            """Recursive definition of steenrod product over the integers."""

            if degree == 0:
                return Surjection_element({tuple(range(1, arity + 1)): 1},
                                          convention=convention)
            else:
                previous = psi(arity, degree - 1, convention=convention)
                acted_on = operators[degree % 2] * previous
                answer = h(acted_on)
                return answer

        integral_answer = psi(arity, degree, convention=convention)
        if torsion:
            integral_answer.set_torsion(torsion)
        return integral_answer

    @staticmethod
    def steenrod_operation(p, s, q, bockstein=False):
        """Chain level representative of P_s or bP_s

        Over the prime p acting on an element of degree q."""

        # input check
        if not all(isinstance(i, int) for i in {p, s, q}):
            raise TypeError('initialize with three int p,s,n')
        if not isinstance(bockstein, bool):
            raise TypeError('bockstein must be a boolean')
        if p == 2 and bockstein:
            raise TypeError('bP only defined for odd primes')

        if p == 2:
            coeff = 1
            d = s - q
            if d < 0:
                return Surjection_element(torsion=p)
        else:
            b = int(bockstein)
            # Serre convention: v(2j)=(-1)^j & v(2j+1)=v(2j)*m! w/ m=(p-1)/2
            coeff = (-1)**(floor(q / 2) + s)
            if q / 2 - floor(q / 2):
                coeff *= factorial((p - 1) / 2)
            # degree of the element: (2s-q)(p-1)-b
            d = (2 * s - q) * (p - 1) - b
            if d < 0:
                return Surjection_element(torsion=p)

        return int(coeff) * Surjection.steenrod_product(
            p, d, torsion=p, convention='McClure-Smith')

    @staticmethod
    def basis(arity, degree, complexity=None):
        """Basis of the chain complex

        In the given arity, degree and complexity.

        """
        if complexity is None:
            complexity = degree
        a, d, c = arity, degree, complexity
        basis = []
        for s in product(range(1, a + 1), repeat=a + d):
            surj = Surjection_element({s: 1})
            if surj and surj.complexity <= c and surj.arity == a:
                basis.append(s)

        return basis
