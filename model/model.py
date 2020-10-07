import random
from collections import namedtuple

import numpy as np

import variables 

ProbRet = namedtuple('ProbRet', ('probability', 'num_cars',
                     'num_rounds', 'round_duration'))

def probability(dt, v, AREA_LENGTH=8, BER=0, N=30, Q=2,
                TID=False, Tari=6.25, M=1, TRext=0):  
    T_EMPTY_SLOT, T_SUCCESS_SLOT, T_INVALID_RN16, T_COLLIDED_SLOT, T_SUCCESS_TID, T_INVALID_NEW_RN16, T_QUERY, T_QREP = variables.variables(Tari, M, TRext)
    PROBABILITY_SUCCESS_RN16 = (1 - BER) ** 16
    PROBABILITY_SUCCESS_EPC = (1 - BER) ** 128
    PROBABILITY_SUCCESS_NEW_RN16 = (1 - BER) ** 32
    PROBABILITY_SUCCESS_TID = (1 - BER) ** 97
    RANGE_SLOT = 2 ** Q
    NUM_ITERATIONS = 100
    num_identified = 0
    num_identified_EPC_and_TID = 0
    T = (dt * (N - 1) + AREA_LENGTH / v)
    round_durations = []
    cars_in_area = []
    num_rounds = [0] * NUM_ITERATIONS
    time_enter = [(dt*(tag - 1)) for tag in range(1, N + 1)]
    time_exit = [(AREA_LENGTH/v) + time_enter[tag] for tag in range(N)]
    num_rounds_per_car = [0] * N

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