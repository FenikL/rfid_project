import numpy as np
from scipy import special
from numba import vectorize

SPEED_OF_LIGHT = 299792458.0

def dbm2w(value_dbm):
    return 10 ** (value_dbm / 10 - 3)

def w2dbm(value_watt):
    return 10 * np.log10(value_watt) + 30 if value_watt >= 1e-15 else -np.inf

def db2lin(value_db):
    return 10 ** (value_db / 10)

@vectorize
def lin2db(value_linear):
    return 10 * np.log10(value_linear) if value_linear >= 1e-15 else -np.inf


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
                dbm2w(-110))
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
