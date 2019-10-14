from functools import reduce
import datetime

class IncidentAnalizer:
    def __init__(self, work_hour_start, work_hour_end, holidays) -> None:
        self.work_hour_start = work_hour_start
        self.work_hour_end = work_hour_end
        self._parse_holidays(holidays)

    def _parse_holidays(self, holidays):
        self.holidays = []
        for holiday in holidays.split(","):
            date = datetime.datetime.strptime(holiday, "%d.%m.%Y").date()
            self.holidays.append(date)

    def set_kpis(self, incidents):
        for incident in incidents:
            if not 'triggeredDate' in incident.keys():
                # incident['TTA'] = None
                # incident['TTR'] = None
                # incident['in_work_hours'] = None
                continue
            if 'acknowledgedDate' in incident:
                incident['TTA'] = (incident['acknowledgedDate'] - incident['triggeredDate'])
            if 'resolvedDate' in incident:
                incident['TTR'] = (incident['resolvedDate'] - incident['triggeredDate'])
            trigger_date = incident['triggeredDate'].date()
            if incident['triggeredDate'].hour < self.work_hour_start \
                or incident['triggeredDate'].hour > self.work_hour_end\
                or trigger_date.weekday() in [6,7]\
                or trigger_date in self.holidays:
                incident['in_work_hours'] = False
            else:
                incident['in_work_hours'] = True



    def get_statistical_analysis(self, incidents):
        cnt = len(incidents)

        ttas = [incident['TTA'] for incident in incidents if 'TTA' in incident]
        mtta = reduce((lambda x, y: x+y), ttas)/len(ttas)
        ttrs = [incident['TTR'] for incident in incidents if 'TTR' in incident]
        mttr = reduce((lambda x, y: x+y), ttrs)/len(ttrs)

        in_work_hour = 0
        for inc in incidents:
            if inc.get('in_work_hours', True):
                in_work_hour +=1
        return {
            'count': cnt,
            'mtta': mtta,
            'mttr': mttr,
            'in_work_hours': in_work_hour
        }