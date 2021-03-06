# -*- coding: utf-8 -*-

import logging
import time
import os
import sys
import nose
from oemof.tools import logger

# add path for solph examples
sys.path.append(os.path.join(os.path.dirname(__file__), 'solph'))
from storage_optimization import storage_invest
from simple_least_costs import simple_least_costs
from flexible_modelling import add_constraints
from csv_reader.operational_example import operational_example


tolerance = 0.001  # percent
show_messages = True
testdict = {}
PASSED = True
basic_path = os.path.dirname(__file__)


def check(cdict, runcheck, subdict, new_results=None):
    global PASSED
    print("Check {0}...".format(subdict['name']))
    if runcheck and new_results is not None:
        count = 0
        subdict['run'] = "Okay"
        subdict.setdefault('messages', {})
        for key, value in new_results.items():
            maxval = cdict[key] + abs(cdict[key]) * tolerance
            minval = cdict[key] - abs(cdict[key]) * tolerance

            if not ((float(value) > minval) and (float(value) < maxval)):
                count += 1
                subdict['messages'][count] = (
                    "{0}: {1} not between {2} and {3}".format(
                        key, float(value), minval, maxval))
                PASSED = False
        if count < 1:
            subdict['results'] = "Okay"
        else:
            subdict['results'] = "{0} error(s)".format(count)
        skip = list(set(cdict.keys()) - set(new_results.keys()))
        if len(skip):
            count += 1
            subdict['messages'][count] = (
                "The following tests were skipped: {0}.".format(skip))
    elif runcheck and new_results is None:
        subdict['run'] = "Okay"
        subdict['results'] = "No results to check - Okay"
    else:
        subdict['run'] = "Failed"
        subdict['results'] = "Failed"
        PASSED = False


def check_nosetests():
    testdir = os.path.join(os.path.dirname(__file__), os.pardir)
    argv = sys.argv[:]
    argv.insert(1, "--with-doctest")
    argv.insert(1, "-w{0}".format(testdir))
    if nose.run(argv=argv):
        time.sleep(0.3)
        print("All nosetests passed!")
    else:
        msg = "Some nosetests failed."
        msg += "See the output above for more information!"
        print(msg)


def run_example_checks():
    # ********* storage invest example *****************************************
    key = 'stor_inv'
    testdict[key] = {'name': "Storage invest example", 'solver': 'cbc'}

    number_of_timesteps = 500

    try:
        esys = storage_invest.optimise_storage_size(
            number_timesteps=number_of_timesteps,
            solvername=testdict[key]['solver'], debug=False,
            tee_switch=False)
        esys.dump()
        esys.restore()
        results = storage_invest.get_result_dict(esys)
        testdict[key]['run'] = True

    except Exception as e:
        testdict[key]['messages'] = {'error': e}
        testdict[key]['run'] = False
        results = None

    stor_invest_dict = {8760: {
            'pp_gas_sum': 112750260.00000007,
            'demand_sum': 2255000000.000008,
            'demand_max': 368693.14440990007,
            'wind_sum': 3085699499.7,
            'wind_inst': 1000000,
            'pv_sum': 553984766.734176,
            'pv_inst': 582000,
            'storage_cap': 10805267,
            'objective': 8.93136532898235e+19},
                        500: {
            'demand_max': 341499.463487,
            'demand_sum': 1.339972e+08,
            'objective': 2.806796142614384e+17,
            'pp_gas_sum': 6.435517e+06,
            'pv_inst': 260771.373277,
            'pv_sum': 9.806339e+06,
            'storage_cap': 615506.94,
            'wind_inst': 999979.9978,
            'wind_sum': 391216886.0,
                        }}

    check(stor_invest_dict[number_of_timesteps], testdict[key]['run'],
          testdict[key], results)
    # ********* end of storage invest example **********************************

    # *********** simple least cost  example ***********************************
    key = 'least_costs'
    testdict[key] = {'name': "Simple least costs optimization", 'solver': 'cbc'}

    try:
        esys = simple_least_costs.initialise_energysystem(periods=2000)
        simple_least_costs.simulate(esys,
                                    solver=testdict[key]['solver'],
                                    tee_switch=False)
        results = simple_least_costs.get_results(esys)
        testdict[key]['run'] = True
    except Exception as e:
        testdict[key]['messages'] = {'error': e}
        testdict[key]['run'] = False
        results = None

    test_results = {
        'objective': 2947725.249402091,
        ('b_el', 'to_bus', 'pp_chp', 'val'): 11161.357450000065,
        ('b_el', 'to_bus', 'pp_coal', 'val'): 33723.047672110595,
        ('b_el', 'to_bus', 'pp_gas', 'val'): 30412.377779000046,
        ('b_el', 'to_bus', 'pp_lig', 'val'): 22066.451080999268,
        ('b_el', 'to_bus', 'pp_oil', 'val'): 2.2872599999999998,
        ('b_el', 'to_bus', 'pv', 'val'): 7796.8431880300122,
        ('b_el', 'to_bus', 'wind', 'val'): 28009.549502999955,
        ('b_el', 'from_bus', 'demand_el', 'val'): 132243.7904593189,
        ('b_el', 'from_bus', 'excess', 'val'): 928.12139200000013,
        ('b_th', 'to_bus', 'pp_chp', 'val'): 14881.810039999958,
        ('b_th', 'from_bus', 'demand_th', 'val'): 14881.80983624002,
        ('coal', 'from_bus', 'pp_coal', 'val'): 86469.394787298472,
        ('gas', 'from_bus', 'pp_chp', 'val'): 37204.525720000034,
        ('gas', 'from_bus', 'pp_gas', 'val'): 60824.751778000136,
        ('lignite', 'from_bus', 'pp_lig', 'val'): 53820.634704001102,
        ('oil', 'from_bus', 'pp_oil', 'val'): 8.1687949999999994}

    check(test_results, testdict[key]['run'], testdict[key], results)
    # *********** end of simple least cost  example ****************************

    # *********** flexible modelling example ***********************************
    key = 'flexible_modelling'
    testdict[key] = {'name': "Flexible Modelling",
                     'solver': 'cbc'}

    try:
        add_constraints.run_add_constraints_example(testdict[key]['solver'])
        testdict[key]['run'] = True
    except Exception as e:
        testdict[key]['messages'] = {'error': e}
        testdict[key]['run'] = False

    test_results = {}

    check(test_results, testdict[key]['run'], testdict[key])
    # *********** end of flexible modelling example ****************************

    # *********** csv reader operational example *******************************
    key = 'csv_operational'
    testdict[key] = {
        'name': "Operational model with csv reader",
        'solver': 'cbc',
        'verbose': False,
        'scenario_path': os.path.join(basic_path, 'solph', 'csv_reader',
                                      'operational_example', 'scenarios'),
        'date_from': '2030-01-01 00:00:00',
        'date_to': '2030-01-14 23:00:00',
        'nodes_flows': 'example_energy_system.csv',
        'nodes_flows_sequences': 'example_energy_system_seq.csv', }

    try:
        res = operational_example.run_example(config=testdict[key])
        results = operational_example.create_result_dict(res)
        testdict[key]['run'] = True
    except Exception as e:
        testdict[key]['messages'] = {'error': e}
        testdict[key]['run'] = False
        results = None

    test_results = {
        'objective': 2326255732.5299315,
        'R2_storage_phs': 88911.484028,
        'R2_wind': 1758697.51,
        'R2_R1_powerline': 2.277989e+06}

    check(test_results, testdict[key]['run'], testdict[key], results)
    # *********** end of csv reader operational example ************************

    logger.define_logging()
    for tests in testdict.values():
        logging.info('*********************************************')
        logging.info(tests['name'])
        logging.info("Used solver: {0}".format(tests['solver']))
        logging.info("Run check: {0}".format(tests['run']))
        logging.info("Result check: {0}".format(tests['results']))
        if show_messages and 'messages' in tests:
            for message in tests['messages'].values():
                logging.error(message)

    if PASSED:
        check_nosetests()
        print("All example tests passed!")
    else:
        check_nosetests()
        text = "Some example tests failed."
        text += "See the output above for more information!"
        print(text)

if __name__ == "__main__":
    run_example_checks()
