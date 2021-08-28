def toSimTime(dias, horas, minutos):
    return dias * 1440 + horas * 60 + minutos


def print_real_time(simtime):
    time_day = int(simtime / 1440)
    time_hour = int((simtime - time_day * 1440) / 60)
    time_min = int(simtime - time_day * 1440 - time_hour * 60)

    return "{}-{}.{:02}".format(time_day, time_hour, time_min)


def real_time(simtime):
    time_day = int(simtime / 1440)
    time_hour = int((simtime - time_day * 1440) / 60)
    time_min = int(simtime - time_day * 1440 - time_hour * 60)

    return time_day, time_hour, time_min
