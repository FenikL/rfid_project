import pytest

import variables

def test_ber_zero():
    ber_func = variables.get_prob_of_trans_without_error(0)
    assert ber_func.rn16 == 1
    assert ber_func.epcid == 1
    assert ber_func.new_rn16 == 1
    assert ber_func.tid == 1

def test_ber_01():
    ber_func = variables.get_prob_of_trans_without_error(0.01)
    assert ber_func.rn16 == pytest.approx(0.8514, abs=0.0001)
    assert ber_func.epcid == pytest.approx(0.2763, abs=0.0001)
    assert ber_func.new_rn16 == pytest.approx(0.7250, abs=0.0001)
    assert ber_func.tid == pytest.approx(0.3772, abs=0.0001)

def test_ber_03():
    ber_func = variables.get_prob_of_trans_without_error(0.03)
    assert ber_func.rn16 == pytest.approx(0.6142, abs=0.0001)
    assert ber_func.epcid == pytest.approx(0.0203, abs=0.0001)
    assert ber_func.new_rn16 == pytest.approx(0.3773, abs=0.0001)
    assert ber_func.tid == pytest.approx(0.0521, abs=0.0001)

def test_for_tari_6_25(): # DR = 8
    tari_func = variables.get_variables_from_tari(6.25)
    assert tari_func.trcal == 1875e-8
    assert tari_func.rtcal == pytest.approx(171875e-10, abs=1e-10)
    assert tari_func.t1_and_t2 == pytest.approx(7466e-8, abs=1e-8)
    assert tari_func.t1_and_t3 == pytest.approx(5156e-8, abs=1e-8)

def test_for_tari_12_5():
    tari_func = variables.get_variables_from_tari(12.5)
    assert tari_func.trcal == 3750e-8
    assert tari_func.rtcal == pytest.approx(343750e-10, abs=1e-10)
    assert tari_func.t1_and_t2 == pytest.approx(1473e-7, abs=1e-7)
    assert tari_func.t1_and_t3 == pytest.approx(1031e-7, abs=1e-7)

def test_bitrate_tari_6_25_and_m_1():
    rtcal = 171875e-10
    trcal = 1875e-8
    blf = 8 / trcal
    bitrate_func = variables.get_bitrate(rtcal, blf, 1)
    assert bitrate_func.reader_bitrate == pytest.approx(116363, abs=1)
    assert bitrate_func.tag_bitrate == pytest.approx(426666, abs=1)