import inspect
import json
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class Maas2AlertManager(object):

    MAAS_KEYS = ['alarms', 'checks', 'entity', 'latest_alarm_states']

    def __init__(self, maas_overview=None, mapper=None):

        self.mapper = mapper
        self.maas_overview = maas_overview

    def _validate_obj_length(self, obj):
        if len(obj) > 0:
            return obj
        return

    def _props(self, obj):
        pr = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if (not name.startswith('__') and not
                    inspect.ismethod(value) and not name == 'driver'):
                pr[name] = value
        return pr

    def _parse_lazy_list(self, value):
        values = {'values': []}
        for index, obj in enumerate(value):
            values['values'].append({'alarms': [], 'checks': [],
                                     'entity': None,
                                     'latest_alarm_states': []})
            for key in self.MAAS_KEYS:
                if hasattr(obj[key], '__len__'):
                    if self._validate_obj_length(obj[key]):
                        values['values'][index][key].append(
                            self._props(obj[key][0])
                        )
                else:
                    values['values'][index][key] = self._props(obj[key])
        return values

    @property
    def maas_alerts(self):
        non_states = ['OK', 'DISABLED']
        alerts = {'values': []}
        for maas_obj in self.maas_overview['values']:
            if len(maas_obj['latest_alarm_states']) > 0:
                if (maas_obj['latest_alarm_states'][0]['state'] not in
                    non_states):
                    alerts['values'].append(maas_obj)
        return alerts

    @property
    def maas_overview(self):
        return self.__maas_overview

    @maas_overview.setter
    def maas_overview(self, value):
        if not isinstance(value, dict):
            values = self._parse_lazy_list(value)
        else:
            try:
                value = json.dumps(value)
                json_value = json.loads(value)
            except TypeError as e:
                return(e)
            values = json_value
        self.__maas_overview = values

    def gen_alert_manager_dict(self):
        alert_list = []
        for item in self.maas_alerts['values']:
            am_dict = {'labels': {}, 'annotations': {}}
            for key, mapping in self.mapper.items():
                if key in am_dict:
                    for maas_outer_key, inner_mapping in mapping.items():
                        if item.get(maas_outer_key):
                            for am_label, maas_inner_key in inner_mapping.items():
                                if isinstance(item[maas_outer_key], list):
                                    try:
                                        am_dict[key][am_label] = \
                                        item[maas_outer_key][0][maas_inner_key]
                                    except TypeError:
                                        for k, v in maas_inner_key.items():
                                            am_dict[key][k] = \
                                            item[maas_outer_key][0][am_label][v]
                                elif isinstance(item[maas_outer_key].get(am_label), dict):
                                    for k, v in maas_inner_key.items():
                                        am_dict[key][k] = \
                                         item[maas_outer_key][am_label][v]
                                else:
                                    am_dict[key][am_label] = \
                                      item[maas_outer_key][maas_inner_key]
                        elif maas_outer_key not in item:
                            am_dict[key][maas_outer_key] = inner_mapping
            alert_list.append(am_dict)
        return alert_list
