import csv
import os
import time
import json
import random
import logging.config
import shutil
import networkx as nx
import matplotlib.pyplot as plt

from pathlib import Path

import pandas as pd
import numpy as np

# Meus imports
import plots_concatenator
from playground_functions import data_analysis
from playground_functions import environment_generation as eg, myConfig
from playground_functions.routing_algorithms import MaxBW, MaxBW_Root

from yafs.core import Sim
from yafs.application import create_applications_from_json
from yafs.topology import Topology

from yafs.placement import JSONPlacement
from yafs.distribution import deterministic_distribution
from yafs.path_routing import DeviceSpeedAwareRouting



# NUMBER_OF_NODES = 15

def delete_files_in_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print("Folder does not exist:", folder_path)
        return

    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file and not a directory
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {filename}")


def append_results(it, path):
    if it == 0:
        last_node_id = 0
        last_link_id = 0

        # Se for a primeria iteração apaga os dados anteriores
        with open(path + "sim_trace.csv", "w") as f_nodes, open(path + "sim_trace_link.csv", "w") as f_links:
            f_links.close()
            f_nodes.close()

    else:
        last_node_id = max(pd.read_csv(path + "sim_trace.csv").id)
        last_link_id = max(pd.read_csv(path + "sim_trace_link.csv").id)

    with open(path + "sim_trace_temp.csv", newline='') as f_src, open(path + 'sim_trace.csv', 'a', newline='') as f_dst:
        reader = csv.reader(f_src)
        writer = csv.writer(f_dst)
        for enum, row in enumerate(reader):
            if it == 0 or (enum != 0 and enum != 1):
                converted_row = [int(val) if val.isdigit() else float(val) if val.replace('.', '', 1).isdigit() else val for val in row]
                if it != 0 and len(converted_row) != 0:
                    converted_row[0] += last_node_id
                writer.writerow(converted_row)

    with open(path + "sim_trace_temp_link.csv", newline='') as f_src, open(path + 'sim_trace_link.csv', 'a', newline='') as f_dst:
        reader = csv.reader(f_src)
        writer = csv.writer(f_dst)
        for enum, row in enumerate(reader):
            if it == 0 or (enum != 0 and enum != 1):
                converted_row = [int(val) if val.isdigit() else float(val) if val.replace('.', '', 1).isdigit() else val for val in row]
                if it != 0 and len(converted_row) != 0:
                    converted_row[0] += last_link_id
                writer.writerow(converted_row)


def sum_mods_per_node(placement, nodes):
    for dt in placement.data['initialAllocation']:
        nodes[int(dt['id_resource'])] += 1


def append_mods_per_node(placement, total_mods_per_node, total_mods_per_node_with_node_id, data_network, total_mods_cloud, avg_mods_per_tier_node):
    mods_per_node = dict()
    temp_tier = {}
    for i in range(NUMBER_OF_NODES+1):
        mods_per_node[i] = [0, 0]
        tier = max([node['tier'] if node['id'] == i else -1 for node in data_network['entity']])
        mods_per_node[i][1] = tier
        if tier not in temp_tier.keys():
            temp_tier[tier] = []
        if tier not in avg_mods_per_tier_node[algorithm].keys():
            avg_mods_per_tier_node[algorithm][tier] = []


    for dt in placement.data['initialAllocation']:
        mods_per_node[int(dt['id_resource'])]
        mods_per_node[int(dt['id_resource'])][0] += 1
        mods_per_node[int(dt['id_resource'])][1] = max([node['tier'] if node['id'] == dt['id_resource'] else -1 for node in data_network['entity']])
    for element in mods_per_node.values():
        temp_tier[element[1]] += [element[0]]

    total_mods_per_node[algorithm] += [n_mods[0] for n_mods in mods_per_node.values()]
    total_mods_per_node_with_node_id[algorithm] += mods_per_node.values()
    total_mods_cloud[algorithm] += mods_per_node[NUMBER_OF_NODES][0]
    for key, values in temp_tier.items():
        avg_mods_per_tier_node[algorithm][key] += [sum(values)/len(values)]


# appends the FRAM per tier
def append_FRAM_per_tier(data_network, total_FRAM_per_tier):
    for node in data_network['entity']:
        if node['tier'] not in total_FRAM_per_tier[algorithm].keys():
            total_FRAM_per_tier[algorithm][int(node['tier'])] = [0, 0]

        total_FRAM_per_tier[algorithm][int(node['tier'])][0] += node['FRAM']
        total_FRAM_per_tier[algorithm][int(node['tier'])][1] += node['RAM']


def simulation(path, stop_time, it, folder_results, folder_data_processing, algorithm, seed, total_mods_per_node, total_mods_per_node_with_node_id, total_mods_cloud, avg_mods_per_tier_node, app1st_mode, lnodes, allocation_file='allocDefinition.json'):
    """
    TOPOLOGY
    """
    t = Topology()
    dataNetwork = json.load(open('data/network.json'))
    t.load(dataNetwork)

    """
    APPLICATION or SERVICES
    """
    dataApp = json.load(open('data/appDefinition.json'))
    apps = create_applications_from_json(dataApp)

    """
    SERVICE PLACEMENT 
    """

    # print("allocation file: ", allocation_file)
    placementJson = json.load(open('data/'+ allocation_file))
    placement = JSONPlacement(name="Placement", json=placementJson)

    if it == 0:
        # for n in t.get_nodes():
        #     nodes[int(n)] = 0

        total_mods_per_node[algorithm] = []
        for n in t.get_nodes():
            lnodes[int(n)] = 0

    # sum_mods_per_node(placement, nodes)
    append_mods_per_node(placement, total_mods_per_node, total_mods_per_node_with_node_id, dataNetwork, total_mods_cloud, avg_mods_per_tier_node)
    append_FRAM_per_tier(dataNetwork, total_FRAM_per_tier)

    """
    Defining ROUTING algorithm to define how path messages in the topology among modules
    """
    selectorPath = MaxBW()
    graph_file_ = 'networkx_alg'


    """
    SIMULATION ENGINE
    """
    s = Sim(t, default_results_path=folder_results+"sim_trace_temp")

    """
    Deploy services == APP's modules
    """
    for aName in apps.keys():
        s.deploy_app(apps[aName], placement, selectorPath) # Note: each app can have a different routing algorithm

    """
    Deploy users
    """

    userJSON = json.load(open('data/usersDefinition.json'))
    for user in userJSON["sources"]:
        app_name = user["app"]
        app = s.apps[app_name]
        msg = app.get_message(user["message"])
        node = user["id_resource"]
        dist = deterministic_distribution(100, name="Deterministic")
        idDES = s.deploy_source(app_name, id_node=node, msg=msg, distribution=dist)

    """
    RUNNING - last step
    """
    logging.info(" Performing simulation: %i " % it)
    s.run(stop_time)  # To test deployments put test_initial_deploy a TRUE
    s.print_debug_assignaments()


    append_results(it, folder_results)

    if it == nIterations-1:

        src_csv = folder_results + "sim_trace_link.csv"
        dst_csv = folder_data_processing + algorithm + "_sim_trace_link.csv"
        shutil.copyfile(src_csv, dst_csv)

        if nIterations > 1:
            for node in nodes.keys():
                nodes[node] /= it
        modules_per_node[algorithm] = nodes

        print(algorithm, 'len\n',len(total_mods_per_node[algorithm]), '\n\n')


def main(stop_time, it, folder_results,folder_data_processing, algorithm, seed, total_mods_per_node, total_mods_per_node_with_node_id, total_mods_cloud, avg_mods_per_tier_node, app1st_mode):

    global nodes
    random.seed(seed)
    conf = myConfig.myConfig()
    exp_conf = eg.ExperimentConfiguration(conf, lpath=os.path.dirname(__file__))
    global NUMBER_OF_NODES
    NUMBER_OF_NODES = exp_conf.loadNetworkConfiguration(conf.myConfiguration)


    random.seed(seed)
    exp_conf.app_generation(app_struct='linear')
    random.seed(seed)
    exp_conf.networkGeneration(n=NUMBER_OF_NODES, file_name_network='network.json')
    random.seed(seed)
    exp_conf.user_generation()

    # Algoritmo de alloc

    start_clock = time.time()

    if app1st_mode:
        if algorithm == 'near_GW_BW_PR':
            exp_conf.near_GW_placement_app1st(weight='BW_PR')

        elif algorithm == 'near_GW_PR':
            exp_conf.near_GW_placement_app1st(weight='PR')

        elif algorithm == 'near_GW_BW':
            exp_conf.near_GW_placement_app1st(weight='BW')

        elif algorithm == 'greedy_FRAM':
            exp_conf.greedy_algorithm_FRAM(app1st=True)

        elif algorithm == 'greedy_latency':
            exp_conf.greedy_algorithm_latency(app1st=True, extra=False)

        elif algorithm == 'RR_IPT_placement':
            exp_conf.RR_IPT_placement_v5()

    else:
        if algorithm == 'near_GW_BW_PR':
            exp_conf.near_GW_placement(weight='BW_PR')

        elif algorithm == 'near_GW_PR':
            exp_conf.near_GW_placement(weight='PR')

        elif algorithm == 'near_GW_BW':
            exp_conf.near_GW_placement(weight='BW')

        elif algorithm == 'greedy_FRAM':
            exp_conf.greedy_algorithm_FRAM(app1st=False)

        elif algorithm == 'greedy_latency':
            exp_conf.greedy_algorithm_latency(app1st=False, extra=False)

        elif algorithm == 'RR_IPT_placement':
            exp_conf.RR_IPT_placement_v6()

        elif algorithm == 'evo_placement':
            bestSolution, histoSolutions, fitness_every_50_generations = exp_conf.evoPlacement()
            data_analysis.plot_fitness_for_generation(histoSolutions)
            data_analysis.plot_difference_in_fitness_for_generations(histoSolutions)



    placement_clock[algorithm].append(time.time() - start_clock)


    nodes = dict()
    plot_name = algorithm

    # Run the simulation
    # if algorithm == 'evo_placement':
    #     for i in range(conf.num_windows):
    #         simulation(path=folder_results, stop_time=stop_time, it=it, folder_results=folder_results, folder_data_processing=folder_data_processing, algorithm=algorithm, seed=seed, total_mods_per_node=total_mods_per_node, total_mods_per_node_with_node_id=total_mods_per_node_with_node_id, total_mods_cloud=total_mods_cloud, avg_mods_per_tier_node=avg_mods_per_tier_node, app1st_mode=app1st_mode, lnodes=nodes, allocation_file='allocDefinitionEA'+str(i)+'.json')
    #         data_analysis.plot_avg_latency(folder_results)
    # else:
    #     simulation(path=folder_results, stop_time=stop_time, it=it, folder_results=folder_results, folder_data_processing=folder_data_processing, algorithm=algorithm, seed=seed, total_mods_per_node=total_mods_per_node, total_mods_per_node_with_node_id=total_mods_per_node_with_node_id, total_mods_cloud=total_mods_cloud, avg_mods_per_tier_node=avg_mods_per_tier_node, app1st_mode=app1st_mode, lnodes=nodes)
    simulation(path=folder_results, stop_time=stop_time, it=it, folder_results=folder_results, folder_data_processing=folder_data_processing, algorithm=algorithm, seed=seed, total_mods_per_node=total_mods_per_node, total_mods_per_node_with_node_id=total_mods_per_node_with_node_id, total_mods_cloud=total_mods_cloud, avg_mods_per_tier_node=avg_mods_per_tier_node, app1st_mode=app1st_mode, lnodes=nodes)
    # data_analysis.plot_avg_latency(folder_results)

if __name__ == '__main__':
    # LOGGING_CONFIG = Path(__file__).parent / 'logging.ini'
    # logging.config.fileConfig(LOGGING_CONFIG)

    delete_files_in_folder("data_analysis")

    folder_results = Path("results")
    folder_results.mkdir(parents=True, exist_ok=True)
    folder_results = str(folder_results) + '/'  # TODO bool

    folder_data_processing = Path('data_processing')
    folder_data_processing.mkdir(parents=True, exist_ok=True)
    folder_data_processing = str(folder_data_processing) + '/'  # TODO bool

    nIterations = 1 # iteration for each experiment
    simulationDuration = 20000

    god_tier_seed = 1706457491
    random_seed = False
    if random_seed:
        seed = int(time.time())
        print("\nseed\n", seed, "\n\n")
    else:
        seed = god_tier_seed
    random.seed(seed)
    seed_list = [random.randint(1, 100000) for _ in range(nIterations)]

    modules_per_node = dict()
    total_mods_per_node = dict()
    total_mods_per_node_with_node_id = dict()
    placement_clock = dict()
    total_mods_cloud = dict()
    avg_mods_per_tier_node = dict()
    total_FRAM_per_tier = dict()

    # algorithm_list = ['randomPlacement', 'bt_min_mods','near_GW_placement', 'greedy_algorithm']
    # algorithm_list = ['bt_min_mods']

    # algorithm_list = ['random', 'greedy_FRAM' ,'greedy_latency', 'near_GW_BW', 'near_GW_PR', 'near_GW_BW_PR', 'lambda' ]
    # algorithm_list = ['random', 'greedy_FRAM' ,'greedy_latency', 'near_GW_BW', 'near_GW_PR', 'near_GW_BW_PR', 'RR_IPT_placement']

    # algorithm_list = [ 'greedy_FRAM' ,'greedy_latency', 'near_GW_BW', 'near_GW_PR', 'near_GW_BW_PR', 'RR_IPT_placement']

    # list_for_greedy_latency = ['greedy_latency_app1st', 'greedy_latency_mod1st', 'greedy_latency_mod1st_extra']
    # list_for_greedy_latency2 = ['greedy_latency_app1st', 'greedy_latency_mod1st', 'greedy_latency_mod1st_mean', 'greedy_latency_app1st_mean']
    # list_for_greedy_FRAM = ['greedy_FRAM_mod1st', 'greedy_FRAM_app1st']
    # list_for_near_GW = ['near_GW_BW_PR_mod1st', 'near_GW_BW_PR_app1st', 'near_GW_PR_mod1st', 'near_GW_PR_app1st', 'near_GW_BW_mod1st', 'near_GW_BW_app1st']
    # list_for_communities = ['RR_IPT_placement_app1st', 'RR_IPT_placement_mod1st']
    # list_for_near_GW_mod1st = ['near_GW_BW_PR_mod1st', 'near_GW_PR_mod1st',  'near_GW_BW_mod1st']
    # list_for_near_GW_app1st = ['near_GW_BW_PR_app1st', 'near_GW_PR_app1st', 'near_GW_BW_app1st']
    # list_for_mod1st = ['RR_IPT_placement_mod1st', 'greedy_latency_mod1st', 'greedy_FRAM_mod1st','near_GW_BW_PR_mod1st', 'near_GW_PR_mod1st',  'near_GW_BW_mod1st']
    # list_for_app1st = ['RR_IPT_placement_app1st', 'greedy_latency_app1st', 'greedy_FRAM_app1st','near_GW_BW_PR_app1st', 'near_GW_PR_app1st', 'near_GW_BW_app1st']
    # # list_for_communities = ['RR_IPT_placement']
    # # list_for_communities = ['RR_IPT_placement_app1st', 'RR_IPT_placement_mod1st']
    # combo_list = ['RR_IPT_placement', 'greedy_latency', 'greedy_FRAM','near_GW_BW_PR', 'near_GW_PR', 'evo_placement']
    # combo_list = ['RR_IPT_placement', 'greedy_latency', 'near_GW_PR', 'evo_placement']

    # algorithm_list = list_for_mod1st
    # algorithm_list = combo_list
    algorithm_list = ['evo_placement']
    app1st_mode = False


    for algorithm in algorithm_list:
        placement_clock[algorithm] = []
        total_mods_per_node_with_node_id[algorithm] = []
        total_mods_cloud[algorithm] = 0
        avg_mods_per_tier_node[algorithm] = dict()
        total_FRAM_per_tier[algorithm] = dict()

        print('\n\n', algorithm,'\n')
        # Iteration for each experiment changing the seed of randoms
        for iteration in range(nIterations):
            random.seed(iteration)
            logging.info("Running experiment it: - %i" % iteration)

            start_time = time.time()
            main(stop_time=simulationDuration,
                 it=iteration, folder_results=folder_results, folder_data_processing=folder_data_processing,algorithm=algorithm, seed=seed_list[iteration], total_mods_per_node=total_mods_per_node, total_mods_per_node_with_node_id=total_mods_per_node_with_node_id, total_mods_cloud=total_mods_cloud, avg_mods_per_tier_node=avg_mods_per_tier_node, app1st_mode = app1st_mode)
            sim_duration = time.time() - start_time
            print("\n--- %s seconds ---" % (sim_duration))

        print("Simulation Done!")

    # print(modules_per_node)
    # print(placement_clock)

    # # latency
    # data_analysis.scatter_plot_app_latency_per_algorithm(folder_data_processing, algorithm_list)
    # data_analysis.plot_latency_per_placement_algorithm(folder_data_processing, algorithm_list)
    # data_analysis.boxplot_latency_per_placement_algorithm(folder_data_processing, algorithm_list)
    # # execution time
    # data_analysis.plot_algorithm_exec_time(placement_clock, nIterations)

    # # modules distribution across nodes
    # data_analysis.plot_modules_per_node_per_algorithm(total_mods_per_node)
    # data_analysis.plot_max_stress_per_algorithm(total_mods_per_node)
    # data_analysis.plot_used_nodes_per_algorithm(total_mods_per_node, n_iterations=nIterations)
    # data_analysis.plot_percentage_used_nodes_per_algorithm(total_mods_per_node)
    # # modules distribution across tiers
    # data_analysis.plot_modules_in_each_tier_per_algorithm(total_mods_per_node_with_node_id, nIterations)
    # data_analysis.plot_average_n_mods_in_each_node_per_tier(avg_mods_per_tier_node=avg_mods_per_tier_node)
    # data_analysis.plot_fram_per_tier_per_algorithm(total_FRAM_per_tier=total_FRAM_per_tier, nIterations=nIterations)
    # # modules distribution in cloud
    # data_analysis.plot_number_modules_in_cloud(total_mods_cloud, nIterations)
    # # data_analysis.plot_number_modules_in_cloud(total_mods_cloud, nIterations)
    # plots_concatenator.concatenate_images('collection.png')

    # if(app1st_mode):
    #     print("\n\nAPP 1ST")
    # else:
    #     print("\n\nMOD 1ST")