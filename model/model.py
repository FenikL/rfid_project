import random
from collections import namedtuple

import numpy as np

import variables

ProbRet = namedtuple('ProbRet', ('probability', 'num_cars',
                     'num_rounds', 'round_duration'))

NUM_ITERATIONS = 100

def run_model(interval, velocity, area_length=8, ber=0, number_of_tags=30, Q=2,
                    tid_is_true=False, tari=6.25, num_of_sym_per_bit=1, trext=0):
    trcal = variables.get_trcal(tari)
    rtcal = variables.get_trcal(tari)
    blf = variables.get_blf(trcal)
    tpri = variables.get_tpri(blf)
    t1_and_t2 = variables.get_sum_of_t1_and_t2(rtcal, tpri)
    t1_and_t3 = variables.get_sum_of_t1_and_t3(rtcal, tpri)

    reader_bitrate = variables.get_reader_bitrate(rtcal)
    tag_bitrate = variables.get_tag_bitrate(blf, num_of_sym_per_bit)
    tag_preamble_len = variables.get_tag_preamble_len(trext, num_of_sym_per_bit)
    t_sync_preamble = variables.get_t_sync_preamble(tari, rtcal)
    t_full_preamble = variables.get_t_full_preamble(t_sync_preamble, trcal)

    t_query = variables.get_t_query(reader_bitrate, t_full_preamble)
    t_qrep = variables.get_t_qrep(reader_bitrate, t_sync_preamble)
    t_ack = variables.get_t_ack(reader_bitrate, t_sync_preamble)
    t_req_rn = variables.get_t_req_rn(reader_bitrate, t_sync_preamble)
    t_read = variables.get_t_read(reader_bitrate, t_sync_preamble)
    t_rn16 = variables.get_t_rn16(tag_preamble_len, tag_bitrate)
    t_new_rn16 = variables.get_t_new_rn16(tag_preamble_len, tag_bitrate)
    t_epcid = variables.get_t_epcid(tag_preamble_len, tag_bitrate)
    t_tid = variables.get_t_tid(tag_preamble_len, tag_bitrate)

    t_empty_slot = variables.get_t_empty_slot(t_qrep, t1_and_t3)
    t_success_slot = variables.get_t_success_slot(t_qrep, t1_and_t2, t_rn16, t_ack, t_epcid)
    t_invalid_rn16 = variables.get_t_invalid_rn16(t_qrep, t1_and_t2, t_rn16, t_ack, t1_and_t3)
    t_collided_slot = variables.get_t_collided_slot(t_qrep, t1_and_t2, t_rn16)
    t_success_tid = variables.get_t_success_tid(t_req_rn, t1_and_t2, t_new_rn16, t_read, t_tid)
    t_invalid_new_rn16 = variables.get_t_invalid_new_rn16(t_req_rn, t1_and_t2, t_new_rn16)

    probability_success_rn16 = variables.get_probability_success_rn16(ber)
    probability_success_epc = variables.get_probability_success_epc(ber)
    probability_success_new_rn16 = variables.get_probability_success_new_rn16(ber)
    probability_success_tid = variables.get_probability_success_tid(ber)
    range_slot = 2 ** Q
    num_identified = 0
    num_identified_epc_and_tid = 0
    round_durations = []
    cars_in_area = []
    num_rounds = [0] * NUM_ITERATIONS
    num_rounds_per_car = [0] * number_of_tags

    T = interval*(number_of_tags - 1) + area_length/velocity
    time_enter = [interval * tag for tag in range(number_of_tags)]
    time_exit = [(area_length/velocity) + time_enter[tag] for tag in range(number_of_tags)]

    for _ in range(NUM_ITERATIONS):
        time = 0
        identified = [0] * number_of_tags
        identified_epc_and_tid = [0] * number_of_tags

        while time < T:
            tags_in_area = [tag for tag in range(number_of_tags) if time_enter[tag] < time < time_exit[tag]]
            tags_slots = {tag: random.getrandbits(Q) for tag in tags_in_area}
            # -- Start of new round
            t_round_started = time
            # Since every round starts with QUERY, we can definitely add
            # (t_query - t_qrep) once at the beginning of each round:
            time += t_query - t_qrep

            for tag in tags_in_area:
                num_rounds_per_car[tag] += 1
            for _ in range(range_slot):
                responding_tags = [tag for tag in tags_in_area if tags_slots[tag] == 0]
                num_responding_tags = len(responding_tags)

                if num_responding_tags == 0:
                    time += t_empty_slot

                elif num_responding_tags == 1:

                    if random.random() < probability_success_rn16:
                        time += t_success_slot

                        if random.random() < probability_success_epc:
                            tag = responding_tags[0]

                            if identified[tag] == 0:
                                identified[tag] = 1
                                num_identified += 1

                            if tid_is_true:
                                if random.random() < probability_success_new_rn16:
                                    time += t_success_tid

                                    if random.random() < probability_success_tid:
                                        if identified_epc_and_tid[tag] == 0:
                                            identified_epc_and_tid[tag] = 1
                                            num_identified_epc_and_tid += 1

                                else:
                                    time += t_invalid_new_rn16

                    else:
                        time += t_invalid_rn16

                else:
                    time += t_collided_slot

                # Decrease slot counts:
                for tag in tags_in_area:

                    if tags_slots[tag] > 0:
                        tags_slots[tag] = tags_slots[tag] - 1

                    else:
                        tags_slots[tag] = 0xFFFF

            # -- End of round
            round_durations.append(time - t_round_started)
            num_rounds[_] += 1
            if len(tags_in_area) != 0:
                cars_in_area.append(len(tags_in_area))

    if tid_is_true:
        p = num_identified_epc_and_tid / (number_of_tags*NUM_ITERATIONS)
    else:
        p = num_identified / (number_of_tags*NUM_ITERATIONS)

    round_durations = np.asarray(round_durations)
    cars_in_area = np.asarray(cars_in_area)
    num_rounds_per_car = np.asarray(num_rounds_per_car) / NUM_ITERATIONS

    return ProbRet(
        probability=p,
        num_cars=cars_in_area.mean(),
        num_rounds=num_rounds_per_car.mean(),
        round_duration=round_durations.mean()
        )
