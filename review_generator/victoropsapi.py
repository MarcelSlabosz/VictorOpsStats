import datetime
import dateutil.parser
import json


from http.client import HTTPSConnection

class VictorOpsAPI:
    def __init__(self, application_id, api_key) -> None:
        self.application_id = application_id
        self.api_key = api_key
        self.client = HTTPSConnection("api.victorops.com")

    def __str__(self) -> str:
        return "VictorOPSAPI(%s, %s****)" % (self.application_id, self.api_key[:5])

    def get_incidents(self, routing_key, start_date=None, end_date=None):

        if not end_date:
            end_date = datetime.datetime.now().isoformat()

        url = "/api-reporting/v2/incidents?routingKey=%s&startedAfter=%s&startedBefore=%s&limit=200" % (routing_key, start_date.isoformat(), end_date)

        self.client.request("GET", url,
                            headers={"X-VO-Api-Id": self.application_id,
                                     "X-VO-Api-Key": self.api_key})

        response = self.client.getresponse()
        res = response.read()
        json_res = json.loads(res)

        return self.__parse_incidents(json_res.get('incidents', []))

    def __parse_incidents(self, incidents):
        incidents_ret = []

        for incident in incidents:
            start_date = dateutil.parser.parse(incident['startTime'])
            ret_inc = {
                'incidentNumber': incident.get('incidentNumber', 'NA'),
                'entityId': incident.get('entityId', 'NA'),
            }
            dates = self.__get_dates_from_transitions(incident.get('transitions', []))
            ret_inc.update(dates)
            incidents_ret.append(ret_inc)
        return incidents_ret

    def __get_dates_from_transitions(self, transitons):
        dates = {}
        for state in transitons:
            if state.get('name') == 'triggered':
                dates['triggeredDate'] = dateutil.parser.parse(state.get('at')).astimezone()
            elif state.get('name') == 'acknowledged':
                dates['acknowledgedDate'] = dateutil.parser.parse(state.get('at')).astimezone()
            elif state.get('name') == 'resolved':
                dates['resolvedDate'] = dateutil.parser.parse(state.get('at')).astimezone()
        return dates
