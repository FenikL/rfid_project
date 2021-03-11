"""
This module includes the main function in my model.
The probability and other parameters are calculated.
"""

import random
from collections import namedtuple

import numpy as np

from model import variables
from model import snr_to_ber
from model.variables import NUM_TAGS

ProbRet = namedtuple('ProbRet', ('ber', 'velocity', 'probability', 'num_cars',
                     'num_rounds', 'round_duration'))
ReturnForRn16 = namedtuple('ReturnForRn16', ['time', 'last_event_is_success'])
ReturnForId = namedtuple('ReturnForId', ['last_event_is_success', 'identified'])
ForTagsInArea = namedtuple('ForTagsInArea', ['tags_in_area', 'num_rounds_per_tag'])

NUM_ITERATIONS = 100

def get_tags_in_area(time, time_enter, time_exit, list_of_tags, num_rounds_per_tag):
    """
    Search for tags in the reading area
    :param time: an SNR of the received signal
    :param time_enter: the de-synchronization
    :param time_exit: the order of Miller encoding
    :param list_of_tags: the symbol duration in seconds
    :return: list of tags in area in the reading area at a given time
    """
    tags_in_area = []
    delete_first = False
    for tag in list_of_tags:
        if time < time_enter[tag]:
            break
        if time_enter[tag] <= time < time_exit[tag]:
            tags_in_area.append(tag)
            num_rounds_per_tag[tag] += 1
        if time >= time_exit[tag]:
            delete_first = True
    if delete_first:
        list_of_tags.pop(0)
    return ForTagsInArea(
        tags_in_area=tags_in_area,
        num_rounds_per_tag=num_rounds_per_tag
    )

def simulate_rn16_transmission(time, probability_success_message,
                duration_event_success, duration_event_invalid):
    if random.random() < probability_success_message:
        time += duration_event_success
        this_event_is_success = True
    else:
        time += duration_event_invalid
        this_event_is_success = False
    return ReturnForRn16(
        time=time,
        last_event_is_success=this_event_is_success
        )

def simulate_id_transmission(last_event_is_success, probability_success_message, identified):
    if last_event_is_success and random.random() < probability_success_message:
        this_event_is_success = True
        identified = True
    else:
        this_event_is_success = False
    return ReturnForId(
        last_event_is_success=this_event_is_success,
        identified=identified,
        )

def run_model(velocity, q_bit=2, tid_is_on=False,
              tari=6.25, num_of_sym_per_bit=1, trext=0, rx_power=-78):
    variables_by_tari = variables.get_variables_from_tari(tari)
    bitrate = variables.get_bitrate(variables_by_tari.rtcal,
                                    variables_by_tari.blf,
                                    num_of_sym_per_bit)
    preamble = variables.get_preamble(tari,
                                      variables_by_tari.rtcal,
                                      variables_by_tari.trcal,
                                      trext, num_of_sym_per_bit)
    duration_from_reader = variables.get_duration_of_mes_from_reader(bitrate.reader_bitrate,
                                                                     preamble.t_full_preamble,
                                                                     preamble.t_sync_preamble)
    duration_from_tag = variables.get_duration_of_mes_from_tag(preamble.tag_preamble_len,
                                                               bitrate.tag_bitrate)
    duration_event = variables.get_duration_event(duration_from_reader,
                                                  duration_from_tag,
                                                  variables_by_tari.t1_and_t2,
                                                  variables_by_tari.t1_and_t3)
    snr = snr_to_ber.get_snr(rx_power=rx_power ,m=num_of_sym_per_bit,
                             preamble_duration=preamble.tag_preamble_len/bitrate.tag_bitrate,
                             blf=variables_by_tari.blf)
    ber = snr_to_ber.ber_over_awgn(snr)
    probability_success_message = variables.get_prob_of_trans_without_error(ber)
    variables_for_time = variables.get_variables_for_times_in_area(velocity)

    range_slot = 2 ** q_bit
    probability_this_iteration = []
    round_durations = []
    cars_in_area = []
    num_rounds = [0] * NUM_ITERATIONS
    num_rounds_per_tag = [0] * NUM_TAGS

    for _ in range(NUM_ITERATIONS):
        time = 0
        identified_epc = [0] * NUM_TAGS
        identified_epc_and_tid = [0] * NUM_TAGS
        list_of_tags = [tag for tag in range(NUM_TAGS)]

        while time < variables_for_time.total_duration:
            #tags_in_area = [
            #    tag for tag in range(NUM_TAGS) if (
            #    variables_for_time.time_enter[tag] < time < variables_for_time.time_exit[tag]
            #                )]
            tags_in_area_variables = get_tags_in_area(time, variables_for_time.time_enter,
                                    variables_for_time.time_exit, list_of_tags, num_rounds_per_tag) 
            tags_in_area = tags_in_area_variables.tags_in_area
            num_rounds_per_tag = tags_in_area_variables.num_rounds_per_tag
            tags_slots = {tag: random.getrandbits(q_bit) for tag in tags_in_area}
            # -- Start of new round
            t_round_started = time
            # Since every round starts with QUERY, we can definitely add
            # (t_query - t_qrep) once at the beginning of each round:
            time += duration_from_reader.query - duration_from_reader.qrep

            #for tag in tags_in_area:
                #num_rounds_per_car[tag] += 1
            for _ in range(range_slot):
                responding_tags = [tag for tag in tags_in_area if tags_slots[tag] == 0]
                num_responding_tags = len(responding_tags)

                if num_responding_tags == 0:
                    time += duration_event.empty_slot

                elif num_responding_tags == 1:
                    tag = responding_tags[0]
                    rn16 = simulate_rn16_transmission(time, probability_success_message.rn16,
                                      duration_event.success_slot, duration_event.invalid_rn16)
                    epcid = simulate_id_transmission(rn16.last_event_is_success,
                                             probability_success_message.epcid, identified_epc[tag])
                    time = rn16.time
                    identified_epc[tag] = epcid.identified
                    if tid_is_on and epcid.last_event_is_success:
                        new_rn16 = simulate_rn16_transmission(time,
                                              probability_success_message.new_rn16,
                                              duration_event.success_tid,
                                              duration_event.invalid_new_rn16)
                        tid = simulate_id_transmission(new_rn16.last_event_is_success,
                                               probability_success_message.tid,
                                               identified_epc_and_tid[tag])
                        time = new_rn16.time
                        identified_epc_and_tid[tag] = tid.identified

                else:
                    time += duration_event.collided_slot

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
        if tid_is_on:
            probability_this_iteration.append(np.mean(identified_epc_and_tid))
        else:
            probability_this_iteration.append(np.mean(identified_epc))

    probability = np.mean(probability_this_iteration)
    round_durations = np.asarray(round_durations)
    cars_in_area = np.asarray(cars_in_area)
    num_rounds_per_tag = np.asarray(num_rounds_per_tag) / NUM_ITERATIONS

    return ProbRet(
        ber=ber,
        velocity=velocity,
        probability=probability,
        num_cars=cars_in_area.mean(),
        num_rounds=num_rounds_per_tag.mean(),
        round_duration=round_durations.mean()
        )
