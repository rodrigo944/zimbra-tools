""" Calendar migration from horde database. Only simple calendars
Requires: python-mysql
"""

#!/usr/bin/python
from MySQLdb import cursors
import MySQLdb
import sys, dateutil
import dateutil.parser as parser
from datetime import datetime
import os


#EVENT_STATUS
#LIVRE = 4
#PROVISORIO = 1
#CONFIRMADO = 2
#CANCELADO = 3


#EVENT_ALARM
#0 = desligado
#1 hora = 60min

#EVENT_MODIFIED
#timestamp

#event_recurenddate
# Repetir todo tempo: 9999-12-31 00:00:00
event_status = {}
event_status['2'] = 'CONFIRMED'
event_status['3'] = 'CANCELLED'
event_status['1'] = 'TENTATIVE'
event_status['4'] = 'TENTATIVE'


#RRULE:FREQ=DAILY;UNTIL=20140515T025959Z;INTERVAL=2
#event_recurtype - repeticao
#1 = Diario - dias
#2 = Semanal - X semanas
#3 = Mensal na mesma data
#4 = Mensal 
#5 =


#           event_id: 01742306328b66f35a7d0d2554879a38
#          event_uid: 20140131091643.45f5o3rbirsb@email.sefa.pa.gov.br
#        calendar_id: 7b8d6b616ae49fe036c65a6227e8769b
#   event_creator_id: migracao_email => OK
#  event_description: Ola Esse e um evento bootstrap de teste => OK
#     event_location: PARA => OK
#       event_status: 2 => OK
#    event_attendees: a:1:{s:19:"sandromll@gmail.com";a:2:{s:10:"attendance";s:1:"2";s:8:"response";i:1;}}
#     event_keywords: => NAO PRECISAO ALL NULL
#   event_exceptions: => IGNORADO
#        event_title: Bootstrap form example => OK
#     event_category: peru => NAO TEM, DESCONSIDERAR
#    event_recurtype: 2 => IGNORADO
#event_recurinterval: 1 => IGNORADO
#    event_recurdays: 6 => IGNORADO
# event_recurenddate: 9999-12-31 00:00:00 => TRANSFORMAR EM ISO8601 => OK
#        event_start: 2014-03-14 00:00:00 => TRANSFORMAR EM ISO8601 => OK
#          event_end: 2014-03-15 00:00:00 => TRANSFORMAR EM ISO8601 => OK
#        event_alarm: 900 => OK -> IGNORADO
#     event_modified: 1391173574 => TRANSFORMAR EM ISO8601 => OK


db_host = 'x-oc-email'
db_user = 'zimbra'
db_pass = 'Zimbra'
db = 'horde'

def connection():
    try:
        conn = MySQLdb.connect(db_host, db_user, db_pass, cursorclass = cursors.DictCursor, use_unicode=True)
        conn.select_db(db)
        #cursor = self.conn.cursor()
        return conn
    except Exception, e:
        print e
        sys.exit(1)
        
def close(conn):
    try:
        conn.close()
    except Exception, e:
        print e
        sys.exit(1)

def getKronoEvents(cursor, user):
    cursor.execute("SELECT * FROM kronolith_events where event_creator_id = '%s'" % user)
    events = cursor.fetchall()
    return events
    #for c in events:
        #c['db'], c['size'], c['myisam'], c['start'], c['end'], c['created_at'], c['updated_at'], c['status'], c['compress']))

def getHordeUsersWithEvents(cursor):
    cursor.execute("select event_creator_id from kronolith_events group by event_creator_id")
    users = cursor.fetchall()
    return users

def convIso(dt):
    dt = str(dt)
    return (parser.parse(dt)).isoformat()

def convFromTimestamp(timestamp):
    if not timestamp:
        timestamp = 0
    return datetime.fromtimestamp(timestamp).isoformat()

def getBegin():
    return """BEGIN:VCALENDAR
X-WR-CALNAME:Calendar
PRODID:Zimbra-Calendar-Provider
VERSION:2.0
METHOD:PUBLISH
BEGIN:VTIMEZONE
TZID:America/Belem
BEGIN:STANDARD
TZOFFSETTO:-0300
TZOFFSETFROM:-0300
RRULE:FREQ=YEARLY;WKST=MO;INTERVAL=1;BYMONTH=2;BYDAY=3SU
TZNAME:BRT
END:STANDARD
END:VTIMEZONE\n"""

def getEnd():
    return """END:VCALENDAR"""

def buildAttendee(attendees):
    mails = []
    for attendee in attendees.split('"'):
        if '@' in attendee:
            mails.append(attendee)

    if not mails:
        return []
    return mails

def get_attendees(attendee):
    return """ATTENDEE;PARTSTAT=ACCEPTED:mailto:%s\n""" % attendee


def get_vevent(event_creator_id, event_description, event_location, event_status, event_attendees, event_title, event_start, event_end, event_modified):
    summary = event_title
    description = event_description
    location = event_location
    attendee = event_attendees
    organizer = event_creator_id + '@sefa.pa.gov.br'
    dtstart = event_start
    dtend = event_end
    status = event_status
    last_modified = event_modified

    if not attendee:
        attendee = 'REMOVETHISLINEPLEASE'

    vevent = """BEGIN:VEVENT
SUMMARY:%s
DESCRIPTION:%s
LOCATION:%s
%s
ORGANIZER:%s
DTSTART;TZID="America/Belem":%s
DTEND;TZID="America/Belem":%s
STATUS:%s
CLASS:PUBLIC
X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY
TRANSP:OPAQUE
LAST-MODIFIED:%s
SEQUENCE:0
END:VEVENT\n""" % (summary, description, location, attendee, organizer, dtstart, dtend, status, last_modified)
    return vevent.replace('REMOVETHISLINEPLEASE\n', '')

def main():
    conn = connection()
    users = getHordeUsersWithEvents(conn.cursor())

    postRestUrl = ''
    for user in users:
        user_events = getKronoEvents(conn.cursor(), user['event_creator_id'])
        # Configura o inicio do vcalendar
        ics_str = getBegin()
        attendees_str = ''
        for user_event in user_events:
            # BUILD ATTENDEESS
            attendees = buildAttendee(user_event['event_attendees'])
            if attendees:
                for attendee in attendees:
                    attendees_str += get_attendees(attendee)

            ics_str += get_vevent(user_event['event_creator_id'].lower(), 
                user_event['event_description'],
                user_event['event_location'],
                event_status[str(user_event['event_status'])],
                attendees_str.strip(),
                user_event['event_title'],
                convIso(user_event['event_start']),
                convIso(user_event['event_end']),
                convFromTimestamp(user_event['event_modified'])
                )
        ics_str += getEnd()
        postRestUrl += 'zmmailbox -z -m %s@sefa.pa.gov.br pru /Calendar /tmp/calendar/calendar-' % user['event_creator_id'].lower()
        postRestUrl += user['event_creator_id'].lower() + '.ics\n'
        if not os.path.exists('calendar'): os.makedirs('calendar')
        with open('calendar/calendar-' + user['event_creator_id'].lower() + '.ics', 'w') as w:
            w.write(ics_str.encode('utf-8'))
    close(conn)
    print postRestUrl
    #events = getKronoEvents(conn.cursor())

if __name__ == '__main__':
    main()
