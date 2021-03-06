import unittest
from clesto.surjection import Surjection_element, Surjection
from clesto.basics import SymmetricRing
from clesto.eilenberg_zilber import EilenbergZilber, EilenbergZilber_element
from clesto.eilenberg_zilber import CubicalEilenbergZilber, CubicalEilenbergZilber_element


class TestSurjection_element(unittest.TestCase):

    def setUp(self):
        self.x = Surjection_element({(1, 3, 1, 2, 1): 1})

    def test_arity(self):
        self.assertEqual(self.x.arity, 3)

    def test_degree(self):
        self.assertEqual(self.x.degree, 2)

    def test_complexity(self):
        self.assertEqual(self.x.complexity, 1)

    def test_boundary(self):
        self.assertEqual(self.x.boundary().boundary(), self.x.zero())

        self.x.convention = 'Berger-Fresse'
        self.assertEqual(self.x.boundary().boundary(), self.x.zero())

        self.x.set_torsion(2)
        self.assertEqual(self.x.boundary().boundary(), self.x.zero())

    def test_rmul(self):
        rho = SymmetricRing.rotation_element(3)
        a, b = (rho * self.x).boundary(), rho * self.x.boundary()
        self.assertEqual(a, b)

        self.x.convention = 'Berger-Fresse'
        a, b = (rho * self.x).boundary(), rho * self.x.boundary()
        self.assertEqual(a, b)

        self.assertEqual(3 * self.x, Surjection_element({(1, 3, 1, 2, 1): 3}))

    def test_orbit(self):
        a = self.x.orbit(representation='trivial')
        self.assertEqual(a, Surjection_element({(1, 2, 1, 3, 1): 1}))

        b = self.x.orbit(representation='sign')
        self.assertEqual(b, Surjection_element({(1, 2, 1, 3, 1): -1}))

    def test_call_simplicial(self):
        s = self.x
        s.convention = 'McClure-Smith'
        x = EilenbergZilber.standard_element(3)
        ds_x = s.boundary()(x)
        d_sx = s(x).boundary()
        s_dx = s(x.boundary())
        self.assertEqual(d_sx - ((-1)**(s.degree)) * s_dx, ds_x)

        x = EilenbergZilber_element({((0, 1, 2), (3, 4), (5, 6)): 1})
        ds_x = s.boundary()(x, 2)
        d_sx = s(x, 2).boundary()
        s_dx = s(x.boundary(), 2)
        self.assertEqual(d_sx - ((-1)**(s.degree)) * s_dx, ds_x)

    def test_call_cubical(self):
        s = self.x
        y = CubicalEilenbergZilber.standard_element(3)
        ds_y = s.boundary()(y)
        d_sy = s(y).boundary()
        sdy = s(y.boundary())
        self.assertEqual(d_sy - ((-1)**(s.degree)) * sdy, ds_y)

    def test_compose_bf(self):
        i = 3
        x = Surjection_element({(3, 2, 1, 2, 1, 3): 1},
                               convention='Berger-Fresse')
        y = Surjection_element({(3, 1, 2, 1, 4, 3): 1},
                               convention='Berger-Fresse')
        dx, dy = x.boundary(), y.boundary()
        dx_y, x_dy = dx.compose(y, i), x.compose(dy, i)
        xy = x.compose(y, i)
        d_xy = xy.boundary()
        self.assertEqual(d_xy - dx_y - (-1)**(x.degree) * x_dy, x.zero())

    def test_suspension(self):
        x = Surjection_element({(1, 3, 2, 1, 2, 3, 4): 1},
                               convention='Berger-Fresse')
        y = Surjection_element({(1, 2, 3, 1, 2, 3): 1},
                               convention='Berger-Fresse')
        sx = x.suspension()
        sy = y.suspension()
        xy = x.compose(y, 1)
        self.assertEqual(xy.suspension(), sx.compose(sy, 1))

        z = Surjection_element({(1, 2, 1, 3, 1, 2, 3): 1},
                               convention='Berger-Fresse')
        sz = z.suspension()
        xz = x.compose(z, 2)
        self.assertEqual(xz.suspension(), sx.compose(sz, 1))


class TestSurjection(unittest.TestCase):

    def test_steenrod_product(self):
        arity = 6
        t = SymmetricRing.transposition_element(arity)
        x = Surjection.steenrod_product(arity, 3).boundary()
        y = t * Surjection.steenrod_product(arity, 2)
        self.assertEqual(x, y)

        arity = 5
        n = SymmetricRing.norm_element(arity, torsion=7)
        x = Surjection.steenrod_product(arity, 4, torsion=7).boundary()
        y = n * Surjection.steenrod_product(arity, 3, torsion=7)
        self.assertEqual(x, y)

        t = SymmetricRing.transposition_element(arity)
        x = Surjection.steenrod_product(arity, 3,
                                        convention='McClure-Smith').boundary()
        y = t * Surjection.steenrod_product(arity, 2,
                                            convention='McClure-Smith')
        self.assertEqual(x, y)


if __name__ == '__main__':
    unittest.main()
