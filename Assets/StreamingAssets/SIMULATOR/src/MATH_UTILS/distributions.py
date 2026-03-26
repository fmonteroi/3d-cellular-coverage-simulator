# Module 'distributions'
# Created 04/06/2020 (version 5.0)
# Modified 20/01/2021 (version 6.0) - Jose Javier Rico Palomo

import numpy as np
import math as m
import random as rd


def weibull(lamda: float, k: float, dist_type="cdf_inv"):
    """
        [REF] https://en.wikipedia.org/wiki/Weibull_distribution#Cumulative_distribution_function
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        x = lamda * (-m.log(1 - rd.random())) ** (1 / k)

    return x


def beta_d(a: float, b: float, dist_type="cdf_inv"):
    """
        [REF] https://en.wikipedia.org/wiki/Beta_distribution
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":

        gamma_x = 0
        gamma_y = 0

        for i in range(0, a):
            gamma_x += - m.log(rd.random())  # pylint: disable=unused-variable

        for i in range(0, b):
            gamma_y += - m.log(rd.random())

        x = gamma_x / (gamma_x + gamma_y)

    return x


def laplacian(beta: float, mu: float, tau_min: float = -0.5, tau_max: float = 0.5, dist_type="cdf_inv"):
    """
        [REF] https://math.stackexchange.com/questions/1632328/cdf-for-laplace-distribution
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        tau = rd.uniform(tau_min, tau_max)
        x = mu - beta * np.sign(tau) * m.log(1 - 2 * abs(tau))

    return x


def log_normal(mu: float, sigma: float, dist_type="cdf_inv"):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal_truncated_ab/log_normal_truncated_ab.html
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        x = log_normal_cdf_inv(rd.random(), mu, sigma)

    return x


def cauchy(a: float, mu: float, dist_type="cdf_inv"):
    """
        [REF] https://es.wikipedia.org/wiki/Distribuci%C3%B3n_de_Cauchy
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        x = mu - m.tan(((-a * m.atan(mu)) - (rd.random() * m.pi)) / a)

    return x


def exponential(lamda: float, dist_type="cdf_inv"):
    """
        [REF] https://en.wikipedia.org/wiki/Exponential_distribution
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        x = (-m.log(1 - rd.random()) / lamda)

    return x


def fisher_tippett(a: float, b: float, dist_type="cdf_inv"):
    """
        [REF] https://en.wikipedia.org/wiki/Generalized_extreme_value_distribution
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        x = a - b * m.log(- m.log(rd.random()))

    return x


def truncated_pareto(a: float, min_v: float, max_v: float, dist_type="cdf_inv"):
    """
        [REF] https://en.wikipedia.org/wiki/Pareto_distribution#Bounded_Pareto_distribution
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":
        u = rd.random()
        x = (- ((u * max_v ** a) - (u * min_v ** a) - (max_v ** a)) / ((max_v ** a) * (min_v ** a))) ** (-1 / a)

    return x


def truncated_log_normal(mu: float, sigma: float, v_min: float, v_max: float, dist_type="cdf_inv"):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal_truncated_ab/log_normal_truncated_ab.html
        - dist_type: "cdf_inv" /
    """

    x = 0

    if dist_type == "cdf_inv":

        seed = 123456
        lncdf_a = log_normal_cdf(v_min, mu, sigma)
        lncdf_b = log_normal_cdf(v_max, mu, sigma)
        cdf_gen, seed = r8_uniform_ab(lncdf_a, lncdf_b, seed)

        x = log_normal_cdf_inv(cdf_gen, mu, sigma)

        cdf = log_normal_truncated_ab_cdf(x, mu, sigma, v_min, v_max)

        if cdf <= 0.0:
            x = v_min

        elif 1.0 <= cdf:
            x = v_max

        else:

            lncdf_min = log_normal_cdf(v_min, mu, sigma)
            lncdf_max = log_normal_cdf(v_max, mu, sigma)

            lncdf_x = lncdf_min + cdf * (lncdf_max - lncdf_min)
            x = log_normal_cdf_inv(lncdf_x, mu, sigma)

    return x


# ----------------------------- #

def log_normal_cdf(x, mu, sigma):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    if x <= 0.0:
        cdf = 0.0

    else:

        logx = np.log(x)
        cdf = normal_cdf(logx, mu, sigma)

    return cdf


def log_normal_cdf_inv(cdf, mu, sigma):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    if cdf < 0.0 or 1.0 < cdf:
        print('')
        print('LOG_NORMAL_CDF_INV - Fatal error!')
        print('  CDF < 0 or 1 < CDF.')
        exit('LOG_NORMAL_CDF_INV - Fatal error!')

    logx = normal_cdf_inv(cdf, mu, sigma)
    x = np.exp(logx)

    return x


def normal_cdf(x, a, b):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    y = (x - a) / b

    cdf = normal_01_cdf(y)

    return cdf


def normal_cdf_inv(cdf, a, b):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    if cdf < 0.0 or 1.0 < cdf:
        print('')
        print('NORMAL_CDF_INV - Fatal error!')
        print('  CDF < 0 or 1 < CDF.')
        exit('NORMAL_CDF_INV - Fatal error!')

    x2 = normal_01_cdf_inv(cdf)
    x = a + b * x2

    return x


def normal_01_cdf(x):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    a1 = 0.398942280444E+00
    a2 = 0.399903438504E+00
    a3 = 5.75885480458E+00
    a4 = 29.8213557808E+00
    a5 = 2.62433121679E+00
    a6 = 48.6959930692E+00
    a7 = 5.92885724438E+00
    b0 = 0.398942280385E+00
    b1 = 3.8052E-08
    b2 = 1.00000615302E+00
    b3 = 3.98064794E-04
    b4 = 1.98615381364E+00
    b5 = 0.151679116635E+00
    b6 = 5.29330324926E+00
    b7 = 4.8385912808E+00
    b8 = 15.1508972451E+00
    b9 = 0.742380924027E+00
    b10 = 30.789933034E+00
    b11 = 3.99019417011E+00

    if abs(x) <= 1.28:
        y = 0.5 * x * x
        q = 0.5 - abs(x) * (a1 - a2 * y / (y + a3 - a4 / (y + a5 + a6 / (y + a7))))

    elif abs(x) <= 12.7:
        y = 0.5 * x * x
        q = np.exp(- y) * b0 / (abs(x) - b1 + b2 / (abs(x) + b3 + b4 / (abs(x) - b5 + b6 / (abs(x) + b7 - b8 / (abs(x) + b9 + b10 / (abs(x) + b11))))))

    else:
        q = 0.0

    if x < 0.0:
        cdf = q
    else:
        cdf = 1.0 - q

    return cdf


def normal_01_cdf_inv(p):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    r8_huge = 1.0E+30
    const1 = 0.180625
    const2 = 1.6

    a = np.array([3.3871328727963666080, 1.3314166789178437745e+2, 1.9715909503065514427e+3, 1.3731693765509461125e+4, 4.5921953931549871457e+4, 6.7265770927008700853e+4, 3.3430575583588128105e+4, 2.5090809287301226727e+3])
    b = np.array([1.0, 4.2313330701600911252e+1, 6.8718700749205790830e+2, 5.3941960214247511077e+3, 2.1213794301586595867e+4, 3.9307895800092710610e+4, 2.8729085735721942674e+4, 5.2264952788528545610e+3])
    c = np.array([1.42343711074968357734, 4.63033784615654529590, 5.76949722146069140550, 3.64784832476320460504, 1.27045825245236838258, 2.41780725177450611770e-1, 2.27238449892691845833e-2, 7.74545014278341407640e-4])
    d = np.array([1.0, 2.05319162663775882187, 1.67638483018380384940, 6.89767334985100004550e-1, 1.48103976427480074590e-1, 1.51986665636164571966e-2, 5.47593808499534494600e-4, 1.05075007164441684324e-9])
    e = np.array([6.65790464350110377720, 5.46378491116411436990, 1.78482653991729133580, 2.96560571828504891230e-1, 2.65321895265761230930e-2, 1.24266094738807843860e-3, 2.71155556874348757815e-5, 2.01033439929228813265e-7])
    f = np.array([1.0, 5.99832206555887937690e-1, 1.36929880922735805310e-1, 1.48753612908506148525e-2, 7.86869131145613259100e-4, 1.84631831751005468180e-5, 1.42151175831644588870e-7, 2.04426310338993978564e-15])

    split1 = 0.425
    split2 = 5.0

    if p <= 0.0:
        value = - r8_huge
        return value

    if 1.0 <= p:
        value = r8_huge
        return value

    q = p - 0.5

    if abs(q) <= split1:
        r = const1 - q * q
        value = q * r8poly_value_horner(7, a, r) / r8poly_value_horner(7, b, r)

    else:

        if q < 0.0:
            r = p
        else:
            r = 1.0 - p

        if r <= 0.0:
            value = r8_huge

        else:
            r = np.sqrt(- np.log(r))

            if r <= split2:
                r = r - const2
                value = r8poly_value_horner(7, c, r) / r8poly_value_horner(7, d, r)

            else:

                r = r - split2
                value = r8poly_value_horner(7, e, r) / r8poly_value_horner(7, f, r)

        if q < 0.0:
            value = - value

    return value


def r8poly_value_horner(m_m, c, x):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    value = c[m_m]

    for i in range(m_m - 1, -1, -1):
        value = value * x + c[i]

    return value


def log_normal_truncated_ab_cdf(x, mu, sigma, a, b):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    if x <= a:
        cdf = 0.0

    elif b <= x:
        cdf = 1.0

    else:

        lncdf_a = log_normal_cdf(a, mu, sigma)
        lncdf_b = log_normal_cdf(b, mu, sigma)
        lncdf_x = log_normal_cdf(x, mu, sigma)

        cdf = (lncdf_x - lncdf_a) / (lncdf_b - lncdf_a)

    return cdf


def r8_uniform_ab(a, b, seed):
    """
        [REF] https://people.sc.fsu.edu/~jburkardt/py_src/log_normal/log_normal.html
    """

    i4_huge = 2147483647

    seed = int(seed)

    seed = (seed % i4_huge)

    if seed < 0:
        seed = seed + i4_huge

    k = (seed // 127773)

    seed = 16807 * (seed - k * 127773) - k * 2836

    if seed < 0:
        seed = seed + i4_huge

    r = a + (b - a) * seed * 4.656612875E-10

    return r, seed
