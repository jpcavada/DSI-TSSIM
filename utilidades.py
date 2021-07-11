def toSimTime(dias, horas, minutos):
    return dias*1440 + horas*60 + minutos


def toRealTime(simtime):
    time_day = int(simtime / 1440)
    time_hour = int((simtime - time_day * 1440) / 60)
    time_min = int(simtime - time_day * 1440 - time_hour * 60)

    return "{}-{}.{}".format(time_day, time_hour, time_min)
