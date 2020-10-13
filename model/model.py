import random
from collections import namedtuple

import numpy as np

import variables 

ProbRet = namedtuple('ProbRet', ('probability', 'num_cars',
                     'num_rounds', 'round_duration'))

def get_probability(dt, v, AREA_LENGTH=8, BER=0, N=30, Q=2,
                    TID=False, Tari=6.25, M=1, TRext=0):
    TRcal = variables.get_TRcal(Tari)
    RTcal = variables.get_RTcal(Tari)
    BLF = variables.get_BLF(TRcal)
    Tpri = variables.get_Tpri(BLF)
    T1 = variables.get_T1(RTcal, Tpri)
    T2 = variables.get_T2(Tpri)
    T3 =variables.get_T3(T1)
    
    READER_BITRATE = variables.get_READER_BITRATE(RTcal)
    TAG_BITRATE = variables.get_TAG_BITRATE(BLF, M)
    TAG_PREAMBLE_LEN = variables.get_TAG_PREAMBLE_LEN(TRext, M)
    T_SYNC_PREAMBLE = variables.get_T_SYNC_PREAMBLE(Tari, RTcal)
    T_FULL_PREAMBLE = variables.get_T_FULL_PREAMBLE(T_SYNC_PREAMBLE, TRcal)

    T_QUERY = variables.get_T_QUERY(READER_BITRATE, T_FULL_PREAMBLE)
    T_QREP = variables.get_T_QREP(READER_BITRATE, T_SYNC_PREAMBLE)
    T_ACK = variables.get_T_ACK(READER_BITRATE, T_SYNC_PREAMBLE)
    T_REQ_RN16 = variables.get_T_REQ_RN16(READER_BITRATE, T_SYNC_PREAMBLE)
    T_READ = variables.get_T_READ(READER_BITRATE, T_SYNC_PREAMBLE)
    T_RN16 = variables.get_T_RN16(TAG_PREAMBLE_LEN, TAG_BITRATE)
    T_NEW_RN16 = variables.get_T_NEW_RN16(TAG_PREAMBLE_LEN, TAG_BITRATE)
    T_EPCID = variables.get_T_EPCID(TAG_PREAMBLE_LEN, TAG_BITRATE)
    T_TID = variables.get_T_TID(TAG_PREAMBLE_LEN, TAG_BITRATE)

    T_EMPTY_SLOT = variables.get_T_EMPTY_SLOT(T_QREP, T1, T3)
    T_SUCCESS_SLOT = variables.get_T_SUCCESS_SLOT(T_QREP, T1, T_RN16, T2, T_ACK, T_EPCID)
    T_INVALID_RN16 = variables.get_T_INVALID_RN16(T_QREP, T1, T_RN16, T2, T_ACK, T3)
    T_COLLIDED_SLOT = variables.get_T_COLLIDED_SLOT(T_QREP, T1, T_RN16, T2)
    T_SUCCESS_TID = variables.get_T_SUCCESS_TID(T_REQ_RN16, T1, T_NEW_RN16, T2, T_READ, T_TID)
    T_INVALID_NEW_RN16 = variables.get_T_INVALID_NEW_RN16(T_REQ_RN16, T1, T_NEW_RN16, T2)
 
    PROBABILITY_SUCCESS_RN16 = variables.get_probability_success_RN16(BER)
    PROBABILITY_SUCCESS_EPC = variables.get_probability_success_EPC(BER)
    PROBABILITY_SUCCESS_NEW_RN16 = variables.get_probability_success_NEW_RN16(BER)
    PROBABILITY_SUCCESS_TID = variables.get_probability_succes_TID(BER)
    RANGE_SLOT = 2 ** Q
    NUM_ITERATIONS = 100
    num_identified = 0
    num_identified_EPC_and_TID = 0
    round_durations = []
    cars_in_area = []
    num_rounds = [0] * NUM_ITERATIONS
    num_rounds_per_car = [0] * N

    T = dt*(N - 1) + AREA_LENGTH/v
    time_enter = [(dt*(tag - 1)) for tag in range(1, N + 1)]
    time_exit = [(AREA_LENGTH/v) + time_enter[tag] for tag in range(N)]

    for _ in range(NUM_ITERATIONS):
        t = 0
        identified = [0] * N
        identified_EPC_and_TID = [0] * N

        while t < T:
            tags_in_area = [tag for tag in range(N) if (time_enter[tag] < t < time_exit[tag])]              
            tags_slots = {tag : random.getrandbits(Q) for tag in tags_in_area}
            # -- Start of new round
            t_round_started = t

            # Since every round starts with QUERY, we can definitely add
            # (T_QUERY - T_QREP) once at the beginning of each round:
            t += T_QUERY - T_QREP
            
            for tag in tags_in_area:
                num_rounds_per_car[tag] += 1
            for _ in range(RANGE_SLOT):
                responding_tags = [tag for tag in tags_in_area if tags_slots[tag] == 0]
                num_responding_tags = len(responding_tags)                
                    
                if num_responding_tags == 0:
                    t += T_EMPTY_SLOT

                elif num_responding_tags == 1:
                    
                    if random.random() < PROBABILITY_SUCCESS_RN16:
                        t += T_SUCCESS_SLOT
                    
                        if random.random() < PROBABILITY_SUCCESS_EPC:
                            tag = responding_tags[0]

                            if identified[tag] == 0:
                                identified[tag] = 1
                                num_identified += 1

                            if TID == True:
                                if random.random() < PROBABILITY_SUCCESS_NEW_RN16:
                                    t += T_SUCCESS_TID

                                    if random.random() < PROBABILITY_SUCCESS_TID: 
                                        if identified_EPC_and_TID[tag] == 0:
                                            identified_EPC_and_TID[tag] = 1
                                            num_identified_EPC_and_TID += 1                                    

                                else:
                                    t += T_INVALID_NEW_RN16

                    else:
                        t += T_INVALID_RN16

                else:
                    t += T_COLLIDED_SLOT

                # Decrease slot counts:
                for tag in tags_in_area:
                    
                        if tags_slots[tag] > 0:
                            tags_slots[tag] = tags_slots[tag] - 1
                            
                        else:
                            tags_slots[tag] = 0xFFFF

            # -- End of round
            round_durations.append(t - t_round_started)
            num_rounds[_] += 1
            if len(tags_in_area) != 0:
                cars_in_area.append(len(tags_in_area))
            
    if TID == False:
        p = num_identified / (N * NUM_ITERATIONS)
    else:
        p = num_identified_EPC_and_TID / (N * NUM_ITERATIONS)

    round_durations = np.asarray(round_durations)
    cars_in_area = np.asarray(cars_in_area)
    num_rounds_per_car = np.asarray(num_rounds_per_car) / NUM_ITERATIONS
    #print('round durations', round_durations.mean(), round_durations.std() / round_durations.mean())
    #return p, cars_in_area.mean(), num_rounds_per_car.mean(), round_durations.mean()
    return ProbRet(
        probability=p,
        num_cars=cars_in_area.mean(),
        num_rounds=num_rounds_per_car.mean(),
        round_duration=round_durations.mean(),
    )