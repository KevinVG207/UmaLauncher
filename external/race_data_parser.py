import base64
import gzip
import struct
import sys
import util
sys.path.append(util.get_asset('external'))

import race_data_pb2


def deserialize_header(b: bytearray) -> (race_data_pb2.RaceSimulateHeaderData, int):
    header = race_data_pb2.RaceSimulateHeaderData()
    header.max_length, header.version = struct.unpack_from('<ii', b, offset=0)
    return header, 4 + header.max_length


def deserialize_horse_frame(b: bytearray, offset: int) -> race_data_pb2.RaceSimulateHorseFrameData:
    horse_frame = race_data_pb2.RaceSimulateHorseFrameData()
    (horse_frame.distance, horse_frame.lane_position, horse_frame.speed, horse_frame.hp, horse_frame.temptation_mode,
     horse_frame.block_front_horse_index) = struct.unpack_from('<fHHHbb', b, offset=offset)
    return horse_frame


def deserialize_frame(b: bytearray, offset: int, horse_num: int,
                      horse_frame_size: int) -> race_data_pb2.RaceSimulateFrameData:
    frame = race_data_pb2.RaceSimulateFrameData()
    frame.time = struct.unpack_from('<f', b, offset=offset)[0]
    offset += 4
    for i in range(horse_num):
        frame.horse_frame.append(deserialize_horse_frame(b, offset))
        offset += horse_frame_size
    return frame


def deserialize_horse_result(b: bytearray, offset: int) -> race_data_pb2.RaceSimulateHorseResultData:
    horse_result = race_data_pb2.RaceSimulateHorseResultData()
    (horse_result.finish_order, horse_result.finish_time, horse_result.finish_diff_time, horse_result.start_delay_time,
     horse_result.guts_order, horse_result.wiz_order, horse_result.last_spurt_start_distance,
     horse_result.running_style, horse_result.defeat,
     horse_result.finish_time_raw) = struct.unpack_from('<ifffBBfBif', b, offset)
    return horse_result


def deserialize_event(b: bytearray, offset: int) -> race_data_pb2.RaceSimulateEventData:
    event = race_data_pb2.RaceSimulateEventData()
    fmt = '<fbb'
    (event.frame_time, event.type, event.param_count) = struct.unpack_from(fmt, b, offset)
    offset += struct.calcsize(fmt)
    for i in range(event.param_count):
        event.param.append(struct.unpack_from('<i', b, offset)[0])
        offset += 4
    return event


def deserialize(b: bytearray) -> race_data_pb2.RaceSimulateData:
    data = race_data_pb2.RaceSimulateData()

    header, offset = deserialize_header(b)
    data.header.CopyFrom(header)

    fmt = '<fiii'
    data.distance_diff_max, data.horse_num, data.horse_frame_size, data.horse_result_size = \
        struct.unpack_from(fmt, b, offset)
    offset += struct.calcsize(fmt)

    data.__padding_size_1 = struct.unpack_from('<i', b, offset)[0]
    offset += 4 + data.__padding_size_1

    fmt = '<ii'
    data.frame_count, data.frame_size = struct.unpack_from(fmt, b, offset)
    offset += struct.calcsize(fmt)

    for i in range(data.frame_count):
        data.frame.append(deserialize_frame(b, offset, data.horse_num, data.horse_frame_size))
        offset += data.frame_size

    data.__padding_size_2 = struct.unpack_from('<i', b, offset)[0]
    offset += 4 + data.__padding_size_2

    for i in range(data.horse_num):
        data.horse_result.append(deserialize_horse_result(b, offset))
        offset += data.horse_result_size

    data.__padding_size_3 = struct.unpack_from('<i', b, offset)[0]
    offset += 4 + data.__padding_size_3

    data.event_count = struct.unpack_from('<i', b, offset)[0]
    offset += 4

    for i in range(data.event_count):
        event_wrapper = race_data_pb2.RaceSimulateData.EventDataWrapper()
        event_wrapper.event_size = struct.unpack_from('<h', b, offset)[0]
        offset += 2
        event_wrapper.event.CopyFrom(deserialize_event(b, offset))
        offset += event_wrapper.event_size
        data.event.append(event_wrapper)

    return data

def parse(race_scenario):
    return deserialize(gzip.decompress(base64.b64decode(race_scenario)))

def main():
    b = input('Please paste content of field "race_scenario" here: ').strip('"')
    b = gzip.decompress(base64.b64decode(b))
    print(deserialize(b))


if __name__ == '__main__':
    main()
