QUERY_LENGTH = 22
QREP_LENGTH = 4
RN16_LENGTH = 16
ACK_LENGTH = 18
EPCID_LENGTH = 128
TID_LENGTH = 64 + 1 + 16 + 16 # include CRC16 and RN16
REQ_RN_LENGTH = 40
NEW_RN16_LENGTH = 32 # +CRC16
READ_LENGTH = 58
micro = 0.000001

def get_probability_success_RN16(BER):
    PROBABILITY_SUCCESS_RN16 = (1 - BER) ** 16
    return PROBABILITY_SUCCESS_RN16

def get_probability_success_EPC(BER):
    PROBABILITY_SUCCESS_EPC = (1 - BER) ** 128
    return PROBABILITY_SUCCESS_EPC

def get_probability_success_NEW_RN16(BER):
    PROBABILITY_SUCCESS_NEW_RN16 = (1 - BER) ** 32
    return PROBABILITY_SUCCESS_NEW_RN16

def get_probability_succes_TID(BER):
    PROBABILITY_SUCCESS_TID = (1 - BER) ** 97
    return PROBABILITY_SUCCESS_TID

def get_TRcal(Tari):
    TRcal = 3 * Tari * micro
    return TRcal

def get_RTcal(Tari):
    RTcal = 2.75 * Tari * micro
    return RTcal

def get_BLF(TRcal):
    BLF = 8 / TRcal
    return BLF

def get_Tpri(BLF):
    Tpri = 1 / BLF
    return Tpri
    
def get_T1(RTcal, Tpri):
    T1 = 1.1*max(RTcal, 10*Tpri) + 2*micro
    return T1

def get_T2(Tpri):
    T2 = 20 * Tpri
    return T2

def get_T3(T1):
    T3 = T1
    return(T3)

def get_READER_BITRATE(RTcal):
    READER_BITRATE = 2 / RTcal
    return READER_BITRATE

def get_TAG_BITRATE(BLF, M):
    TAG_BITRATE = BLF / M
    return TAG_BITRATE

def get_T_SYNC_PREAMBLE(Tari, RTcal):
    T_SYNC_PREAMBLE = micro*(12.5 + Tari) + RTcal
    return T_SYNC_PREAMBLE

def get_T_FULL_PREAMBLE(T_SYNC_PREAMBLE, TRcal):
    T_FULL_PREAMBLE = T_SYNC_PREAMBLE + TRcal
    return T_FULL_PREAMBLE

def get_TAG_PREAMBLE_LEN(TRext, M):
    if TRext == 0:
        if M == 1:
            TAG_PREAMBLE_LEN = 6
        else:
            TAG_PREAMBLE_LEN = 10
    else:
        if M ==1:
            TAG_PREAMBLE_LEN = 18
        else:
            TAG_PREAMBLE_LEN = 22
    return TAG_PREAMBLE_LEN

def get_T_QUERY(READER_BITRATE, T_FULL_PREAMBLE):
    T_QUERY = (QUERY_LENGTH / READER_BITRATE) + T_FULL_PREAMBLE
    return T_QUERY

def get_T_QREP(READER_BITRATE, T_SYNC_PREAMBLE):
    T_QREP = (QREP_LENGTH / READER_BITRATE) + T_SYNC_PREAMBLE
    return T_QREP

def get_T_ACK(READER_BITRATE, T_SYNC_PREAMBLE):
    T_ACK = (ACK_LENGTH / READER_BITRATE) + T_SYNC_PREAMBLE
    return T_ACK

def get_T_REQ_RN16(READER_BITRATE, T_SYNC_PREAMBLE):
    T_REQ_RN16 = (NEW_RN16_LENGTH / READER_BITRATE) + T_SYNC_PREAMBLE
    return T_REQ_RN16

def get_T_READ(READER_BITRATE, T_SYNC_PREAMBLE):
    T_READ = (READ_LENGTH / READER_BITRATE) + T_SYNC_PREAMBLE
    return T_READ

def get_T_RN16(TAG_PREAMBLE_LEN, TAG_BITRATE):
    T_RN16 = (RN16_LENGTH + TAG_PREAMBLE_LEN + 1) / TAG_BITRATE  # + 1 - for end-of-signalling (suffix)
    return T_RN16

def get_T_NEW_RN16(TAG_PREAMBLE_LEN, TAG_BITRATE):
    T_NEW_RN16 = (NEW_RN16_LENGTH + TAG_PREAMBLE_LEN + 1) / TAG_BITRATE
    return T_NEW_RN16

def get_T_EPCID(TAG_PREAMBLE_LEN, TAG_BITRATE):
    T_EPCID = (EPCID_LENGTH + TAG_PREAMBLE_LEN + 1) / TAG_BITRATE  # + 1 - -//-//-
    return T_EPCID

def get_T_TID(TAG_PREAMBLE_LEN, TAG_BITRATE):
    T_TID = (TID_LENGTH + TAG_PREAMBLE_LEN + 1) / TAG_BITRATE
    return T_TID

def get_T_EMPTY_SLOT(T_QREP, T1, T3):
    T_EMPTY_SLOT = T_QREP + T1 + T3
    return T_EMPTY_SLOT

def get_T_SUCCESS_SLOT(T_QREP, T1, T_RN16, T2, T_ACK, T_EPCID):
    T_SUCCESS_SLOT = T_QREP + T1 + T_RN16 + T2 + T_ACK + T1 + T_EPCID + T2
    return T_SUCCESS_SLOT

def get_T_INVALID_RN16(T_QREP, T1, T_RN16, T2, T_ACK, T3):
    T_INVALID_RN16 = T_QREP + T1 + T_RN16 + T2 + T_ACK + T1 + T3
    return T_INVALID_RN16

def get_T_COLLIDED_SLOT(T_QREP, T1, T_RN16, T2):
    T_COLLIDED_SLOT = T_QREP + T1 + T_RN16 + T2
    return T_COLLIDED_SLOT

def get_T_SUCCESS_TID(T_REQ_RN16, T1, T_NEW_RN16, T2, T_READ, T_TID):
    T_SUCCESS_TID = T_REQ_RN16 + T1 + T_NEW_RN16 + T2 + T_READ + T1 +T_TID + T2
    return T_SUCCESS_TID

def get_T_INVALID_NEW_RN16(T_REQ_RN16, T1, T_NEW_RN16, T2):
    T_INVALID_NEW_RN16 = T_REQ_RN16 + T1 + T_NEW_RN16 + T2
    return T_INVALID_NEW_RN16