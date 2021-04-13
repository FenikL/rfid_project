import numpy as np
from scipy import special
from numba import vectorize
from numpy import linalg as la

SPEED_OF_LIGHT = 299792458.0
PERMITTIVITY = 15.0
CONDUCTIVITY = 3e-2
FREQUENCY = 860e6
THERMAL_NOISE = -114
wavelen = SPEED_OF_LIGHT / FREQUENCY
x_reader = 0
y_reader = 0.0
z_reader = 5.0
a = np.pi / 4
forward_dir_reader = (-np.sin(a), 0, -np.cos(a))
position_reader = (-x_reader, y_reader, z_reader)
polapolarization_reader = 0.5
polapolarization_tag = 1
reader_tx_power = 31.5

def dbm2w(value_dbm):
    return 10 ** (value_dbm / 10 - 3)

def w2dbm(value_watt):
    return 10 * np.log10(value_watt) + 30 if value_watt >= 1e-15 else -np.inf

def db2lin(value_db):
    return 10 ** (value_db / 10)

@vectorize
def lin2db(value_linear):
    return 10 * np.log10(value_linear) if value_linear >= 1e-15 else -np.inf

def dipole_rp(*, azimuth, **kwargs):  
    """
    Returns dipole directional gain
    :param azimuth:
    :return:
    """
    c = np.cos(azimuth)
    s = np.sin(azimuth)
    if c > 1e-9:
        return np.abs(np.cos(np.pi / 2 * s) / c)
    else:
        return 0.0

    # Attenuation due to reflections (reflection coefficient) computation

def _reflection_c_parallel(grazing_angle, permittivity, conductivity, wavelen):
    #eta = permittivity - 60j * wavelen * conductivity
    eta = 15 - 60j * SPEED_OF_LIGHT * 3e-2 / 860e6
    c = np.cos(grazing_angle)
    return (eta - c ** 2) ** 0.5


def _reflection_c_perpendicular(grazing_angle, permittivity, conductivity, wavelen):
    #eta = permittivity - 60j * wavelen * conductivity
    eta = 15 - 60j * SPEED_OF_LIGHT * 3e-2 / 860e6
    c = np.cos(grazing_angle)
    return (eta - c ** 2) ** 0.5 / eta


# noinspection PyUnusedLocal
def reflection_constant(*, grazing_angle, polarization, permittivity, conductivity, wavelen, **kwargs):
    return -1.0 + 0.j


# noinspection PyUnusedLocal
# @vectorize
def reflection(grazing_angle, polarization, permittivity, conductivity, wavelen):
    """
    Computes reflection coefficient from conducting surface with defined grazing angle and supported relative
    permittivity and conductivity of the surface. In order to set type of wave polarization, polarization
    parameter is specified. For parallel to surface polarized wave polarization should set to 1, for perpendicular -
    to 0; for circular - to 0.5. For different type of elliptic polarization use other value in the range of 0..1
    :param grazing_angle: an angle between normal to surface and wave vector
    :param polarization: determine the type of polarization of the grazing wave
    :param permittivity: the relative_permittivity of two media divided by the surface
    :param conductivity: the conductivity of the surface
    :param wavelen: the wave length of the grazing wave
    :return: the reflection coefficient for specified parameters and the given grazing angle
    """
    s = np.sin(grazing_angle)

    if polarization < 0 or polarization > 1:
        return float('nan')

    if polarization != 0:
        c_parallel = _reflection_c_parallel(grazing_angle, permittivity, conductivity, wavelen)
        reflection_parallel = (s - c_parallel) / (s + c_parallel)
    else:
        reflection_parallel = 0.j

    if polarization != 1:
        c_perpendicular = _reflection_c_perpendicular(grazing_angle, permittivity, conductivity, wavelen)
        reflection_perpendicular = (s - c_perpendicular) / (s + c_perpendicular)
    else:
        reflection_perpendicular = 0.j

    return polarization * reflection_parallel + (1 - polarization) * reflection_perpendicular 

def two_ray_path_loss_3d(tx_pos, tx_dir_theta, rx_pos, rx_dir_theta, polarization):
    """
    Computes free space signal attenuation between the transmitter and the receiver in linear scale.
    :param wavelen: a wavelen of signal carrier
    :param time: Time passed from the start of reception
    :param ground_reflection: a function to compute a complex-valued reflection coefficient
    :param tx_velocity: the velocity of the transmitter
    :param tx_dir_phi: the vector pointed the direction with tilt angle equals 0 of the transmitter antenna.
    :param tx_dir_theta: the vector pointed the direction with azimuth angle equals 0 of the transmitter antenna.
    :param tx_pos: a current position of the transmitter.
    :param tx_rp: a radiation patternx_reader = 0

    """
    # LoS - Line-of-Sight, NLoS - Non-Line-of-Sight

    # Ray geometry computation
    ground_normal = np.array([0, 0, 1])
    rx_pos_refl = np.array([rx_pos[0], rx_pos[1], -rx_pos[2]])  # Reflect RX relatively the ground

    d0_vector = rx_pos - tx_pos            # LoS ray vector
    d1_vector = rx_pos_refl - tx_pos       # NLoS ray vector
    d0 = la.norm(d0_vector)                # LoS ray length
    d1 = la.norm(d1_vector)                # NLoS ray length
    d0_vector_tx_n = d0_vector / d0        # LoS ray vector normalized
    d0_vector_rx_n = -d0_vector_tx_n       
    d1_vector_tx_n = d1_vector / d1        # NLoS ray vector normalized
    d1_vector_rx_n = np.array([-d1_vector_tx_n[0], -d1_vector_tx_n[1], d1_vector_tx_n[2]])

    # Azimuth and tilt angle computation for computation of attenuation
    # caused by deflection from polar direction
    tx_azimuth_0 = np.arccos(np.dot(d0_vector_tx_n, tx_dir_theta))
    rx_azimuth_0 = np.arccos(np.dot(d0_vector_rx_n, rx_dir_theta))
    tx_azimuth_1 = np.arccos(np.dot(d1_vector_tx_n, tx_dir_theta))
    rx_azimuth_1 = np.arccos(np.dot(d1_vector_rx_n, rx_dir_theta))

    # A grazing angle of NLoS ray for computation of reflection coefficient
    grazing_angle = np.arccos(-1*np.dot(d1_vector_rx_n, ground_normal))

    #relative_velocity = rx_velocity - tx_velocity
    #velocity_pr_0 = np.dot(d0_vector_tx_n, relative_velocity)
    #velocity_pr_1 = np.dot(d1_vector_tx_n, relative_velocity)

    g0 = (dipole_rp(azimuth=tx_azimuth_0) * dipole_rp(azimuth=rx_azimuth_0))

    g1 = (dipole_rp(azimuth=tx_azimuth_1) * dipole_rp(azimuth=rx_azimuth_1))   

    r1 = reflection(grazing_angle=grazing_angle, wavelen=wavelen, polarization=polarization, permittivity = 15.0, conductivity = 3e-2)


    k = 2 * np.pi / wavelen
    #k = 18.02426718878446
    return (0.5/k)**2 * np.absolute(   g0/d0*np.exp(-1j*k*d0) +
                                    r1*g1/d1*np.exp(-1j*k*d1))**2

def get_rx_power(x, path_loss=None, tx_power=None, cable_loss=0, tag_modulation_loss=0):
    reader_gain = 8.0
    tag_gain = 2.0
    polarization_loss = -3
    if cable_loss == -2.0:
        r1 = np.array(position_reader)
        o1 = np.array(forward_dir_reader)
        r2 = np.array([-x, 0, 0.5])
        o2 = np.array([1,0,0])
    else:
        r1 = np.array([-x, 0, 0.5])
        o1 = np.array([1,0,0])
        r2 = np.array(position_reader)
        o2 = np.array(forward_dir_reader)
    if np.dot(r2 - r1, o1) < 0 or np.dot(r1 - r2, o2) < 0:
        return THERMAL_NOISE
    #cable_loss = -1.0
    #tag_modulation_loss = -10.0
    rx_power = (tx_power + tag_modulation_loss +
                cable_loss + reader_gain +
                path_loss + tag_gain + polarization_loss)
    return rx_power

def get_path_loth_for_reader(x):
    return two_ray_path_loss_3d(position_reader, forward_dir_reader, np.array([-x, 0, 0.5]), np.array([1,0,0]), 0.5)

def get_path_loth_for_tag(x):
    return two_ray_path_loss_3d(np.array([-x, 0, 0.5]), np.array([1,0,0]), position_reader, forward_dir_reader, 1)

def get_reader_power(x):
    reader_power = get_rx_power(x=x, path_loss=lin2db(get_path_loth_for_reader(x)), tx_power=reader_tx_power, cable_loss=-2.0, tag_modulation_loss=0)
    return reader_power

def get_tag_power(x):
    tag_power = get_rx_power(x=x, path_loss=lin2db(get_path_loth_for_tag(x)), tx_power=get_reader_power(x), cable_loss=0, tag_modulation_loss=-10.0)
    return tag_power

def sum_of_rx_power(x):
    reader_power = get_rx_power(x=x, path_loss=lin2db(get_path_loth_for_reader(x)), tx_power=reader_tx_power, cable_loss=-2.0, tag_modulation_loss=0)
    tag_power = get_rx_power(x=x, path_loss=lin2db(get_path_loth_for_tag(x)), tx_power=get_reader_power(x)-10,cable_loss=0, tag_modulation_loss=-10.0)
    return reader_power + tag_power

# noinspection PyUnusedLocal
def signal2noise(*, rx_power, noise_power, **kwargs):
    """
    Computes Signal-to-Noise ratio. Input parameters are in logarithmic scale.
    :param rx_power:
    :param noise_power:
    :param kwargs:
    :return:
    """
    return db2lin(rx_power - noise_power)
# noinspection PyUnusedLocal
def sync_angle(*, snr, preamble_duration=9.3e-6, bandwidth=1.2e6, **kwargs):
    """
    Computes the angle of de-synchronisation.
    :param snr: an SNR of the received signal
    :param preamble_duration: the duration of PHY-preamble in seconds
    :param bandwidth: the bandwidth of the signal in herzs
    :param kwargs:
    :return: the angle of de-synchronisation
    """
    return (snr * preamble_duration * bandwidth) ** -0.5
# noinspection PyUnusedLocal
def snr_extended(*, snr, sync_phi=0, miller=1, symbol_duration=1.25e-6, bandwidth=1.2e6, **kwargs):
    """
    Computes the extended SNR for BER computation.
    :param snr: an SNR of the received signal
    :param sync_phi: the de-synchronization
    :param miller: the order of Miller encoding
    :param symbol_duration: the symbol duration in seconds
    :param bandwidth: the bandwidth of the signal in herzs
    :param kwargs:
    :return: the extended SNR for BER computation
    """
    return miller * snr * symbol_duration * bandwidth * np.cos(sync_phi) ** 2

def get_snr(rx_power, m, preamble_duration, blf):
    noise = (dbm2w(-80) +
                dbm2w(THERMAL_NOISE))
    noise = w2dbm(noise)
    raw_snr = signal2noise(
        rx_power=rx_power, noise_power=noise)
    sync = sync_angle(
        snr=raw_snr, preamble_duration=preamble_duration)
    snr = snr_extended(
        snr=raw_snr, sync_phi=sync, miller=m,
        symbol_duration=1.0 / blf)
    return snr

def ber_over_awgn(snr):
    """
    Computes BER in an additive white gaussian noise (AWGN) channel for Binary Phase Shift Keying (BPSK)
    :param snr: the extended SNR
    :return:
    """
    def q_function(x):
        return 0.5 - 0.5 * special.erf(x / 2 ** 0.5)

    t = q_function(snr ** 0.5)
    return 2 * t * (1 - t)

def ber_over_rayleigh(snr):
    """
    Computes BER in the channel with Rayleigh fading for Binary Phase Shift Keying (BPSK)
    :param snr:
    :param kwargs:
    :return:
    """
    t = (1 + 2 / snr) ** 0.5
    return 0.5 - 1 / t + 2 / np.pi * np.arctan(t) / t