# file with variables for model.py
from collections import namedtuple

QUERY_LENGTH = 22
QREP_LENGTH = 4
RN16_LENGTH = 16
ACK_LENGTH = 18
EPCID_LENGTH = 128
TID_LENGTH = 64 + 1 + 16 + 16 # include CRC16 and RN16
REQ_RN_LENGTH = 40
NEW_RN16_LENGTH = 32 # +CRC16
READ_LENGTH = 58
AREA_LENGTH = 12 #8
NUM_TAGS = 30
INTERVAL = 1
DR = 64 / 3
t_on = 2000e-3
t_off = 100e-3
MICRO = 0.000001

DurationFromReader = namedtuple('DurationFromReader', ['query', 'qrep', 'ack', 'req_rn', 'read'])
DurationFromTag = namedtuple('DurationFromTag', ['rn16', 'new_rn16', 'epcid', 'tid'])
VariablesByTari = namedtuple('VariablesByTari', ['trcal', 'rtcal',
                             'blf', 't1_and_t2', 't1_and_t3'])
Bitrate = namedtuple('Bitrate', ['reader_bitrate', 'tag_bitrate'])
Preamble = namedtuple('Preamble', ['t_sync_preamble', 't_full_preamble', 'tag_preamble_len'])
DurationEvent = namedtuple('DurationEvent', ['empty_slot', 'success_slot', 'invalid_rn16',
                           'collided_slot', 'success_tid', 'invalid_new_rn16'])
ProbabilitySuccessMessage = namedtuple('Probability', ['rn16', 'epcid', 'new_rn16', 'tid'])
VariablesForTime = namedtuple('VariablesForTime', ['total_duration', 'time_enter', 'time_exit'])

def get_prob_of_trans_without_error(ber):
    rn16 = (1-ber) ** RN16_LENGTH
    epc = (1-ber) ** EPCID_LENGTH
    new_rn16 = (1-ber) ** NEW_RN16_LENGTH
    tid = (1-ber) ** TID_LENGTH
    return ProbabilitySuccessMessage(
        rn16=rn16,
        epcid=epc,
        new_rn16=new_rn16,
        tid=tid
        )

def get_variables_from_tari(tari):
    trcal = 3 * tari * MICRO
    rtcal = 2.75 * tari * MICRO
    blf = DR / trcal
    tpri = 1 / blf
    t1_and_t2 = 1.1*max(rtcal, 10*tpri) + 2*MICRO + 20*tpri
    t1_and_t3 = 2*1.1*max(rtcal, 10*tpri)
    return VariablesByTari(
        trcal=trcal,
        rtcal=rtcal,
        blf=blf,
        t1_and_t2=t1_and_t2,
        t1_and_t3=t1_and_t3
        )

def get_bitrate(rtcal, blf, num_of_sym_per_bit):
    reader_bitrate = 2 / rtcal
    tag_bitrate = blf / num_of_sym_per_bit
    return Bitrate(
        reader_bitrate=reader_bitrate,
        tag_bitrate=tag_bitrate
        )

def get_preamble(tari, rtcal, trcal, trext, num_of_sym_per_bit):
    t_sync_preamble = MICRO*(12.5 + tari) + rtcal
    t_full_preamble = t_sync_preamble + trcal
    if trext == 0:
        if num_of_sym_per_bit == 1:
            tag_preamble_len = 6
        else:
            tag_preamble_len = 10
    else:
        if num_of_sym_per_bit == 1:
            tag_preamble_len = 18
        else:
            tag_preamble_len = 22
    return Preamble(
        t_sync_preamble=t_sync_preamble,
        t_full_preamble=t_full_preamble,
        tag_preamble_len=tag_preamble_len
        )

def get_duration_of_mes_from_reader(reader_bitrate, t_full_preamble, t_sync_preamble):
    t_query = (QUERY_LENGTH / reader_bitrate) + t_full_preamble
    t_qrep = (QREP_LENGTH / reader_bitrate) + t_sync_preamble
    t_ack = (ACK_LENGTH / reader_bitrate) + t_sync_preamble
    t_req_rn = (NEW_RN16_LENGTH / reader_bitrate) + t_sync_preamble
    t_read = (READ_LENGTH / reader_bitrate) + t_sync_preamble
    return DurationFromReader(
        query=t_query,
        qrep=t_qrep,
        ack=t_ack,
        req_rn=t_req_rn,
        read=t_read
        )

def get_duration_of_mes_from_tag(tag_preamble_len, tag_bitrare):
    # + 1 - for end-of-signalling (suffix)
    t_rn16 = (RN16_LENGTH + tag_preamble_len + 1) / tag_bitrare
    t_new_rn16 = (NEW_RN16_LENGTH + tag_preamble_len + 1) / tag_bitrare
    t_epcid = (EPCID_LENGTH + tag_preamble_len + 1) / tag_bitrare
    t_tid = (TID_LENGTH + tag_preamble_len + 1) / tag_bitrare
    return DurationFromTag(
        rn16=t_rn16,
        new_rn16=t_new_rn16,
        epcid=t_epcid,
        tid=t_tid
        )

def get_duration_event(duration_from_reader, duration_from_tag, t1_and_t2, t1_and_t3):
    t_empty_slot = duration_from_reader.qrep + t1_and_t3
    t_success_slot = (duration_from_reader.qrep + 2*t1_and_t2 + duration_from_tag.rn16 +
                      duration_from_reader.ack + duration_from_tag.epcid)
    t_invalid_rn16 = (duration_from_reader.qrep + t1_and_t2 + duration_from_tag.rn16 +
                      duration_from_reader.ack + t1_and_t3)
    t_collided_slot = duration_from_reader.qrep + t1_and_t2 + duration_from_tag.rn16
    t_success_tid = (duration_from_reader.req_rn + 2*t1_and_t2 + duration_from_tag.new_rn16 +
                     duration_from_reader.read + duration_from_tag.tid)
    t_invalid_new_rn16 = duration_from_reader.req_rn + t1_and_t2 + duration_from_tag.new_rn16

    #t_success_rn16 = duration_from_reader.qrep + t1_and_t2 + duration_from_tag.rn16 +
                      #duration_from_reader.ack

   #t_success_epcid = t1_and_t2 + duration_from_tag.epcid
    #t_success_new_rn16 = duration_from_reader.req_rn + t1_and_t2 + duration_from_tag.new_rn16 +
                         #duration_from_reader.read
    #t_success_TID = t1_and_t2 + duration_from_tag.tid


    return DurationEvent(
        empty_slot=t_empty_slot,
        success_slot=t_success_slot,
        invalid_rn16=t_invalid_rn16,
        collided_slot=t_collided_slot,
        success_tid=t_success_tid,
        invalid_new_rn16=t_invalid_new_rn16
        )

def get_variables_for_times_in_area(velocity):
    total_duration = INTERVAL*(NUM_TAGS - 1) + AREA_LENGTH/velocity
    time_enter = {tag: INTERVAL * tag for tag in range(NUM_TAGS)}
    time_exit = {tag: (AREA_LENGTH/velocity) + time_enter[tag] for tag in range(NUM_TAGS)}
    return VariablesForTime(
        total_duration=total_duration,
        time_enter=time_enter,
        time_exit=time_exit
        )
