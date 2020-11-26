QUERY_LENGTH = 22
QREP_LENGTH = 4
RN16_LENGTH = 16
ACK_LENGTH = 18
EPCID_LENGTH = 128
TID_LENGTH = 64 + 1 + 16 + 16 # include CRC16 and RN16
REQ_RN_LENGTH = 40
NEW_RN16_LENGTH = 32 # +CRC16
READ_LENGTH = 58
MICRO = 0.000001

def get_probability_success_rn16(ber):
    probability_success_rn16 = (1-ber) ** 16
    return probability_success_rn16

def get_probability_success_epc(ber):
    probability_success_epc = (1-ber) ** 128
    return probability_success_epc

def get_probability_success_new_rn16(ber):
    probability_success_new_rn16 = (1-ber) ** 32
    return probability_success_new_rn16

def get_probability_success_tid(ber):
    probability_success_tid = (1-ber) ** 97
    return probability_success_tid

def get_trcal(tari):
    trcal = 3 * tari * MICRO
    return trcal

def get_rtcal(tari):
    rtcal = 2.75 * tari * MICRO
    return rtcal

def get_blf(trcal):
    blf = 8 / trcal
    return blf

def get_tpri(blf):
    tpri = 1 / blf
    return tpri

def get_sum_of_t1_and_t2(rtcal, tpri):
    t1_and_t2 = 1.1*max(rtcal, 10*tpri) + 2*MICRO + 20*tpri
    return t1_and_t2

def get_sum_of_t1_and_t3(rtcal, tpri):
    t1_and_t3 = 2*1.1*max(rtcal, 10*tpri)
    return t1_and_t3

def get_reader_bitrate(rtcal):
    reader_bitrate = 2 / rtcal
    return reader_bitrate

def get_tag_bitrate(blf, num_of_sym_per_bit):
    tag_bitrare = blf / num_of_sym_per_bit
    return tag_bitrare

def get_t_sync_preamble(tari, rtcal):
    t_sync_preamble = MICRO*(12.5 + tari) + rtcal
    return t_sync_preamble

def get_t_full_preamble(t_sync_preamble, trcal):
    t_full_preamble = t_sync_preamble + trcal
    return t_full_preamble

def get_tag_preamble_len(trext, num_of_sym_per_bit):
    if trext == 0:
        if num_of_sym_per_bit == 1:
            tag_preamble_len = 6
        else:
            tag_preamble_len = 10
    else:
        if num_of_sym_per_bit ==1:
            tag_preamble_len = 18
        else:
            tag_preamble_len = 22
    return tag_preamble_len

def get_t_query(reader_bitrate, t_full_preamble):
    t_query = (QUERY_LENGTH / reader_bitrate) + t_full_preamble
    return t_query

def get_t_qrep(reader_bitrate, t_sync_preamble):
    t_qrep = (QREP_LENGTH / reader_bitrate) + t_sync_preamble
    return t_qrep

def get_t_ack(reader_bitrate, t_sync_preamble):
    t_ack = (ACK_LENGTH / reader_bitrate) + t_sync_preamble
    return t_ack

def get_t_req_rn(reader_bitrate, t_sync_preamble):
    t_req_rn = (NEW_RN16_LENGTH / reader_bitrate) + t_sync_preamble
    return t_req_rn

def get_t_read(reader_bitrate, t_sync_preamble):
    t_read = (READ_LENGTH / reader_bitrate) + t_sync_preamble
    return t_read

def get_t_rn16(tag_preamble_len, tag_bitrare):
    t_rn16 = (RN16_LENGTH + tag_preamble_len + 1) / tag_bitrare  # + 1 - for end-of-signalling (suffix)
    return t_rn16

def get_t_new_rn16(tag_preamble_len, tag_bitrare):
    t_new_rn16 = (NEW_RN16_LENGTH + tag_preamble_len + 1) / tag_bitrare
    return t_new_rn16

def get_t_epcid(tag_preamble_len, tag_bitrare):
    t_epcid = (EPCID_LENGTH + tag_preamble_len + 1) / tag_bitrare  # + 1 - -//-//-
    return t_epcid

def get_t_tid(tag_preamble_len, tag_bitrare):
    t_tid = (TID_LENGTH + tag_preamble_len + 1) / tag_bitrare
    return t_tid

def get_t_empty_slot(t_qrep, t1_and_t3):
    t_empty_slot = t_qrep + t1_and_t3
    return t_empty_slot

def get_t_success_slot(t_qrep, t1_and_t2, t_rn16, t_ack, t_epcid):
    t_success_slot = t_qrep + 2*t1_and_t2 + t_rn16 + t_ack + t_epcid
    return t_success_slot

def get_t_invalid_rn16(t_qrep, t1_and_t2, t_rn16, t_ack, t1_and_t3):
    t_invalid_rn16 = t_qrep + t1_and_t2 + t_rn16 + t_ack + t1_and_t3
    return t_invalid_rn16

def get_t_collided_slot(t_qrep, t1_and_t2, t_rn16):
    t_collided_slot = t_qrep + t1_and_t2 + t_rn16
    return t_collided_slot

def get_t_success_tid(t_req_rn, t1_and_t2, t_new_rn16, t_read, t_tid):
    t_success_tid = t_req_rn + 2*t1_and_t2 + t_new_rn16 + t_read + t_tid
    return t_success_tid

def get_t_invalid_new_rn16(t_req_rn, t1_and_t2, t_new_rn16):
    t_invalid_new_rn16 = t_req_rn + t1_and_t2 + t_new_rn16
    return t_invalid_new_rn16
