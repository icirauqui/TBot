import datetime
import telegram_send

def report_go(extradata):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
    eqbalmsg = 'B ' + str(nowstr) + '\n' + str(extradata)
    telegram_send.send(messages=[eqbalmsg])