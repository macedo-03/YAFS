import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx
from math import ceil, floor
from collections import Counter

import statistics
import json

# from pathlib import Path

# folder_results = Path("../../tutorial_scenarios/Playground/results/")
# folder_results.mkdir(parents=True, exist_ok=True)
# folder_results = str(folder_results)+"/"

def save_plot(plot_name):
    try:
        os.stat('data_analysis/')
    except:
        os.mkdir('data_analysis/')

    plt.savefig('data_analysis/' + plot_name)

def remove_outliers(values_list):
    q1 = np.percentile(values_list, 25)
    q3 = np.percentile(values_list, 75)
    iqr = q3 - q1
    threshold = 1.5 * iqr
    upper_bound = q3 + threshold
    lower_bound = q1 - threshold
    no_outliers_list = [x for x in values_list if lower_bound < x < upper_bound]
    return no_outliers_list

def plot_paths_taken(folder_results, plot_name=None):
    dfl = pd.read_csv(folder_results + "sim_trace" + "_link.csv")

    apps_deployed = np.unique(dfl.app)

    pallet = np.linspace(0, 100, len(apps_deployed))

    fig, ax = plt.subplots()

    for en, a in enumerate(apps_deployed):
        ax.scatter(np.array(dfl[dfl.app == a].src), np.array(dfl[dfl.app == a].dst),
                   c=(pallet[en] * np.ones(len(dfl[dfl.app == a].src))), cmap='plasma', vmin=0, vmax=100, marker='x',
                   label=f'App: {a}')

    ax.set_xlabel('Source nodes')
    ax.set_ylabel('Destiny nodes')
    ax.legend()

    if plot_name is None:
        ax.set_title(f'Simulation hops')

    else:
        plot_name += '_sim_hops'
        ax.set_title(plot_name)
        save_plot(plot_name)

    plt.show()


def plot_app_path(folder_results, application, t, pos=None, placement=None, plot_name=None):
    if pos is None:
        pos = nx.spring_layout(t.G)

    plt.figure(figsize=(10, 5))
    sml = pd.read_csv(folder_results + "sim_trace_temp_link.csv")
    sm = pd.read_csv(folder_results + "sim_trace_temp.csv")

    path = sml[sml.app == application]

    path = path[path.id == min(path.id)]

    # path = path[sml.at[0, 'id'] == sml.id]            # << antigo
    # Na versao anterior só funcionava se o link com id 1 fosse o da aplicação que se quer ver

    path2 = sm[sm.app == application]
    path2 = sm[sm.at[0, 'id'] == sm.id]
    # path2 = sm[(sm.id == 1) & (sm.app == application)]
    print(type(path))

    highlighted_edges = []
    labels = {}
    for index, hops in path.iterrows():
        highlighted_edges.append([hops.src, hops.dst])
        labels[(hops.src, hops.dst)] = "{}\nBW={}\tPR={}".format(hops.message, t.get_edge((hops.src, hops.dst))['BW'],
                                                                 t.get_edge((hops.src, hops.dst))['PR'])
    print(highlighted_edges)

    print('tempo total')

    total_time = path2.at[path2.index[-1], 'time_out'] - path2.at[0, 'time_in']
    total_time = "total time = {:.2f}".format(total_time)
    plt.text(11, 0.3, total_time, fontsize=12, ha='right')

    if placement is not None:
        node_labels = dict()

        for dt in placement.data['initialAllocation']:
            if int(dt['id_resource']) not in node_labels:
                node_labels[int(dt['id_resource'])] = ([dt['module_name']], [str(dt['app'])])

            else:
                node_labels[int(dt['id_resource'])][0].append(dt['module_name'])
                node_labels[int(dt['id_resource'])][1].append(str(dt['app']))

        for lbl in node_labels:
            node_labels[
                lbl] = f"\n\n\n\nModule: {', '.join(node_labels[lbl][0])}\nApp: {', '.join(node_labels[lbl][1])}"

        nx.draw_networkx_labels(t.G, pos, labels=node_labels, font_size=8)
        nx.draw_networkx(t.G, pos, arrows=True)
    else:
        nx.draw_networkx(t.G, pos, arrows=True)
    nx.draw_networkx_edges(t.G, pos, edge_color='black')
    # # Draw the highlighted edges in red
    nx.draw_networkx_edges(t.G, pos, edgelist=highlighted_edges, edge_color='red', arrows=True, arrowstyle='->')
    nx.draw_networkx_edge_labels(t.G, pos, edge_labels=labels, label_pos=0.5, font_size=8, font_family='Arial')

    if plot_name is not None:
        save_plot(plot_name + f'_{application}_path')

    plt.show()


def plot_occurrences(folder_results, mode='module', plot_name=None):
    df = pd.read_csv(folder_results + "sim_trace.csv")

    if mode == 'module':
        res_used = df.module
    elif mode == 'node':
        res_used = df['TOPO.src'] + df['TOPO.dst']
    elif mode == 'node_src':
        res_used = df['TOPO.src']
    else:  # elif mode == 'node_dst':
        res_used = df['TOPO.dst']

    unique_values, occurrence_count = np.unique(res_used, return_counts=True)

    ax = plt.subplot()

    plt.bar(unique_values, occurrence_count)

    ax.set_xlabel(mode.title())
    ax.set_ylabel('Occurrences')

    if plot_name is None:
        ax.set_title(f'Times a {mode.title()} is used')

    else:
        plot_name += '_occur'
        ax.set_title(plot_name)
        save_plot(plot_name)

    plt.show()


def plot_latency(folder_results, plot_name=None):
    dfl = pd.read_csv(folder_results + "sim_trace_link.csv")

    apps_deployed = np.unique(dfl.app)

    app_lat = []

    for app_ in apps_deployed:
        app_lat.append(np.array(dfl[dfl.app == app_].latency))

    ax = plt.subplot()

    plt.boxplot(app_lat)
    plt.xticks(range(1, len(apps_deployed) + 1), apps_deployed)

    ax.set_xlabel(f'Apps')
    ax.set_ylabel('Latency (\u03bcs)')

    if plot_name is None:
        ax.set_title('Latency')

    else:
        plot_name += '_latency'
        ax.set_title(plot_name)
        save_plot(plot_name)

    plt.show()


def plot_avg_latency(folder_results, plot_name=None):
    dfl = pd.read_csv(folder_results + "sim_trace_link.csv")

    apps_deployed = np.unique(dfl.app)

    for app_ in range(max(apps_deployed)):
        if app_ not in apps_deployed:
            apps_deployed = np.append(apps_deployed, app_)
    
    apps_deployed = np.sort(apps_deployed)

    app_lat = []

    for app_ in apps_deployed:
        if app_ in np.unique(dfl.app):
            app_lat.append(np.average(np.array(dfl[dfl.app == app_].latency)))
        
        else:
            app_lat.append(0)

    mean = sum(app_lat) / len(app_lat)

    apps_deployed = [str(x) for x in apps_deployed] + ['mean']
    app_lat.append(mean)

    ax = plt.subplot()

    # Set colors for bars
    colors = ['blue'] * len(apps_deployed)
    colors[-1] = 'red'  # Set color for mean bar

    # plt.boxplot(app_lat)
    plt.bar(range(0, len(apps_deployed)), app_lat, color=colors)
    plt.xticks(range(0, len(apps_deployed)), apps_deployed)

    ax.set_xlabel(f'Apps')
    ax.set_ylabel('Latency (\u03bcs)')

    if plot_name is None:
        ax.set_title('Average Latency')

    else:
        plot_name += '_avg_latency'
        ax.set_title(plot_name)
        save_plot(plot_name)

    # Add value on top of each bar
    for i, v in enumerate(app_lat):
        plt.text(i, v, str(round(v, 2)), ha='center', va='bottom')

    plt.show()


def scatter_plot_app_latency_per_algorithm(folder_data_processing, algorithm_list):
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'cyan', 'pink']
    plt.figure(figsize=(10, 6))
    # dfl = pd.read_csv(folder_results + "algorithm1")
    i = 0
    mean = []
    labels = []
    for algorithm in algorithm_list:
        dfl = pd.read_csv(folder_data_processing + algorithm + "_sim_trace_link.csv")
        apps_deployed = np.unique(dfl.app)

        app_lat = []
        for app_ in apps_deployed:
            app_lat.append(np.average(np.array(dfl[dfl.app == app_].latency)))
        mean+=app_lat
        plt.scatter(range(len(app_lat)), app_lat, label=algorithm, c=colors[i], marker='o')
        labels.append(algorithm)
        i = (i + 1) % len(colors)
        ticks = range(len(app_lat))

    no_outliers = remove_outliers(mean)
    plt.ylim(max(min(no_outliers)-0.5, 0), max(no_outliers)+0.5)


    plt.xticks(ticks)
    plt.xlabel(f'Apps')
    plt.ylabel('Latency (\u03bcs)')
    # plt.title('Average App Latency per algorithm')
    plt.legend(labels, loc='upper right', bbox_to_anchor=(1.25, 1))
    plt.subplots_adjust(right=0.8)
    save_plot('Latency__Average_App_Latency_per_algorithm')
    plt.show()


def plot_latency_per_placement_algorithm(folder_data_processing, algorithm_list):
    # colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'cyan', 'pink']

    mean = []

    for algorithm in algorithm_list:
        dfl = pd.read_csv(folder_data_processing + algorithm + "_sim_trace_link.csv")
        apps_deployed = np.unique(dfl.app)

        app_lat = []
        for app_ in apps_deployed:
            app_lat.append(np.average(np.array(dfl[dfl.app == app_].latency)))
        mean.append(sum(app_lat) / len(app_lat))

    plt.figure(figsize=(10, 6))
    bars = plt.bar(algorithm_list, mean, color=colors)
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)


    # media = sum(mean)/len(mean)
    # plt.figure(figsize=(10, 6))
    # plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)

    plt.ylim(0, max(mean) * 1.1)
    # plt.xlabel(f'Placement Algorithms')
    plt.ylabel('Latency (\u03bcs)')
    # plt.title('Latency Per Placement Algorithm')
    # plt.legend(algorithm_list, loc='upper right')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), va='bottom', ha='center')

    save_plot('Latency__Barplot_Latency_per_Placement_Algorithm')
    plt.show()

def boxplot_latency_per_placement_algorithm(folder_data_processing, algorithm_list):
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'cyan', 'pink']
    algorithm_latency = [[] for x in range(len(algorithm_list))]

    i = 0
    for algorithm in algorithm_list:
        dfl = pd.read_csv(folder_data_processing + algorithm + "_sim_trace_link.csv")
        apps_deployed = np.unique(dfl.app)

        for app_ in apps_deployed:
            algorithm_latency[i] += list(np.array(dfl[dfl.app == app_].latency))
        i+=1

    plt.figure(figsize=(10, 6))

    # plt.boxplot(algorithm_latency, labels=algorithm_list, showfliers=False, showmeans=True, meanprops=dict(marker='X', markerfacecolor='c', markeredgecolor='c'))
    plt.boxplot(algorithm_latency, labels=algorithm_list, showfliers=False)
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)
    plt.xlabel(f'Placement Algorithms')
    plt.ylabel('Latency (\u03bcs)')
    plt.title('Latency Per Placement Algorithm')

    save_plot('Latency__Boxplot_Latency_per_Placement_Algorithm')
    plt.show()

def plot_nodes_per_time_window(folder_results, t, n_wind=10, graph_type=None, show_values=False, plot_name=None):
    df = pd.read_csv(folder_results + "sim_trace.csv")

    max_time = max(df['time_out'])
    window_sz = ceil(max_time / n_wind)

    nodes_per_window = []
    window_rate = []
    n_nodes = len(t.G.nodes)

    for i in range(n_wind):
        add = np.unique(
            np.concatenate((df[(df['time_out'] < ((i + 1) * window_sz)) & (df['time_out'] > i * window_sz)]['TOPO.src'],
                            df[(df['time_out'] < ((i + 1) * window_sz)) & (df['time_out'] > i * window_sz)][
                                'TOPO.dst'])))
        nodes_per_window.append(add)

        window_rate.append(len(nodes_per_window[i]) * 100 / n_nodes)

    ax = plt.subplot()

    plt.ylim(0, 100)

    x_min, x_max = plt.xlim()
    y_min, y_max = plt.ylim()
    plt.text(x_max - 0.02, y_min + 0.02, f'# Topology Nodes: {n_nodes}', fontsize=10, ha='right', va='bottom',
             transform=plt.gca().transAxes)

    if graph_type is None:
        plt.plot(range(len(window_rate)), window_rate)
        plt.scatter(range(len(window_rate)), window_rate, marker='x')
    elif graph_type == 'bar':
        plt.bar(range(len(window_rate)), window_rate)

    if show_values:
        for enum, rate in enumerate(window_rate):
            plt.text(enum, rate, f'{int(floor((rate * n_nodes) / 100))}')

    ax.set_xlabel(f'Window')
    ax.set_ylabel('% Used Nodes')

    if plot_name is not None:
        save_plot(plot_name)
    plt.show()


def modules_per_node(placement, topology, plot_name=None):
    nodes = dict()
    for n in topology.get_nodes():
        nodes[int(n)] = 0

    for dt in placement.data['initialAllocation']:
        # if int(dt['id_resource']) not in nodes:
        #     nodes[int(dt['id_resource'])] = 1
        # else:
        nodes[int(dt['id_resource'])] += 1

    plt.bar(nodes.keys(), nodes.values())
    plt.yticks(range(0, int(max(nodes.values())) + 1))
    plt.xlabel('nodes')
    plt.ylabel('number of modules allocated')

    ax = plt.subplot()

    if plot_name is None:
        ax.set_title('Modules per node')
    else:
        plot_name += '_mods_per_nds'
        ax.set_title(plot_name)
        save_plot(plot_name)

    plt.show()

#


def plot_modules_per_node_per_algorithm(total_mods_per_node):
    data_list = [list(total_mods_per_node[algorithm]) for algorithm in total_mods_per_node.keys()]
    print(data_list)

    plt.figure(figsize=(10, 6))
    plt.boxplot(data_list, labels=total_mods_per_node.keys())

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)
    plt.yticks(range(max(max(data) for data in data_list)+1))
    plt.xlabel('Algorithms')
    plt.ylabel('Modules per node')
    plt.title('Modules per node of each algorithm')
    save_plot('ModsNodes__Modules_per_Node_of_each_Algorithm')
    plt.show()

def plot_max_stress_per_algorithm(total_mods_per_node):
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'cyan', 'pink']
    data_list = [max(list(total_mods_per_node[algorithm])) for algorithm in total_mods_per_node.keys()]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(total_mods_per_node.keys(), data_list, color=colors)

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)
    plt.yticks(range(max(data_list)))
    plt.xlabel('Algorithms')
    plt.ylabel('Max modules per node')
    plt.title('Max modules in a node for each algorithm')
    save_plot('ModsNodes__Max_Modules_per_Node_of_each_Algorithm')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), va='bottom', ha='center')
    plt.show()

def plot_used_nodes_per_algorithm(total_mods_per_node, n_iterations):
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    data_list = [
        (len(list(total_mods_per_node[algorithm])) - list(total_mods_per_node[algorithm]).count(0)) / n_iterations
        for algorithm in total_mods_per_node.keys()]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(total_mods_per_node.keys(), data_list, color=colors)

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)
    plt.xlabel('Algorithms')
    plt.ylabel('Number of Nodes')
    plt.title('Number of Used Nodes in Each Algorithm')
    save_plot('ModsNodes__Used_Nodes_per_Algorithm')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), va='bottom', ha='center')
    plt.show()


def plot_percentage_used_nodes_per_algorithm(total_mods_per_node):
    colors = ['C0', 'C1']
    labels = ["Unused", "Used"]
    wedges = []
    row = col = 0

    n = len(total_mods_per_node)
    nrows = int(n / 2) + n % 2
    ncols = 2 if n > 1 else 1

    fig, ax = plt.subplots(nrows, ncols)
    i = 0
    for algorithm in total_mods_per_node.keys():
        row = int(i / ncols)
        col = i % ncols
        i += 1

        total_nodes = len(list(total_mods_per_node[algorithm]))
        unused_nodes = list(total_mods_per_node[algorithm]).count(0)

        if nrows == 1:
            if ncols != 1:
                wedges, _, __ = ax[col].pie(
                    [unused_nodes / total_nodes * 100, (total_nodes - unused_nodes) / total_nodes * 100], autopct='%1.1f%%',
                    colors=colors)
                ax[col].set_title(algorithm)
            else:
                wedges, _, __ = ax.pie(
                    [unused_nodes / total_nodes * 100, (total_nodes - unused_nodes) / total_nodes * 100],
                    autopct='%1.1f%%',
                    colors=colors)
                ax.set_title(algorithm)

        else:
            wedges, _, __ = ax[row, col].pie(
                [unused_nodes / total_nodes * 100, (total_nodes - unused_nodes) / total_nodes * 100], autopct='%1.1f%%',
                colors=colors)
            ax[row, col].set_title(algorithm)

    if n % 2 == 1 and n != 1:
        fig.delaxes(ax[row, col + 1])

    fig.suptitle('Percentage of Used Nodes in Each Algorithm')
    fig.legend(wedges, labels, loc='lower center')
    save_plot('ModsNodes__Percentage_Used_Nodes_per_Algorithm')

    plt.show()


def plot_messages_node(folder_results, plot_name=None):
    df = pd.read_csv(folder_results + "sim_trace_link.csv")
    res_used = df['dst']

    src_nodes = df.drop_duplicates(subset='id')
    src_nodes = src_nodes['src']

    nodes_used = pd.concat([src_nodes, res_used], axis=0)

    values = Counter(nodes_used)
    x = [i for i in range(max(values.keys()) + 1)]
    y = [values[i] if i in values.keys() else 0 for i in x]

    ax = plt.subplot()

    plt.bar(x, y)

    for i in range(len(x)):
        plt.text(i, y[i] + 0.005 * max(y), y[i], ha='center')

    ax.set_xlabel('Node')
    ax.set_xticks(x)
    ax.set_ylabel('Occurrences')

    if plot_name is None:
        ax.set_title('Number of Messages')
    else:
        plot_name += '_nr_msgs'
        ax.set_title(plot_name)
        save_plot(plot_name)
    plt.show()


def plot_algorithm_exec_time(algorithm_clock, iterations):
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    data_list_temp = [list(algorithm_clock[algorithm]) for algorithm in algorithm_clock.keys()]
    data_list = [sum(x)/iterations for x in data_list_temp]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(algorithm_clock.keys(), data_list, color=colors)

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 8), va='bottom', ha='center')

    plt.xlabel('Algorithms')
    plt.ylabel('Average Execution Time (s)')
    plt.title('Average Execution Time per Algorithm')
    save_plot("ExecutionTime__Average_Execution_Time_per_Algorithm")
    plt.show()




def plot_modules_in_each_tier_per_algorithm(total_mods_per_node_with_node_id, n_iterations):
    i = 0
    fig, axs = plt.subplots(len(total_mods_per_node_with_node_id), 1, figsize=(5, len(total_mods_per_node_with_node_id)*3))
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    for algorithm in total_mods_per_node_with_node_id.keys():
        tier_dict = {}
        for node in total_mods_per_node_with_node_id[algorithm]:
            if node[1] not in tier_dict.keys():
                tier_dict[node[1]] = []

            tier_dict[node[1]] += [node[0]]

        tier_list = tier_dict.keys()
        info_list = [sum(tier_dict[x]) / n_iterations for x in tier_list]
        max_info = int(max(info_list))
        if len(total_mods_per_node_with_node_id) == 1:
            axs.bar(tier_list, info_list, color=colors)
            axs.set_title(algorithm)
            axs.set_xlabel('Tier')
            axs.set_xticks(range(0, len(tier_list)))
            axs.set_yticks(range(0, max_info, int(max_info / 5)))
            axs.set_ylabel('Number of Modules Allocated')
        else:
            axs[i].bar(tier_list, info_list, color=colors)
            axs[i].set_title(algorithm)
            axs[i].set_xlabel('Tier')
            axs[i].set_xticks(range(0, len(tier_list)))
            axs[i].set_yticks(range(0, max_info, int(max_info/5)))
            axs[i].set_ylabel('Number of Modules Allocated')
        i += 1

    plt.subplots_adjust(hspace=0.5)
    #plt.subplots_adjust(top=0.9, bottom=0.1)
    #plt.tight_layout(rect=(0.9, 0.9, 0.1, 0.1))  # Increase or decrease the pad parameter to control spacing

    #plt.tight_layout()
    fig.suptitle('plot_modules_in_each_tier_per_algorithm')
    save_plot('ModsTiers__Plot_Modules_in_each_Tier_per_Algorithm')
    plt.show()

def plot_average_n_mods_in_each_node_per_tier(avg_mods_per_tier_node):
    i = 0
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    fig, axs = plt.subplots(len(avg_mods_per_tier_node), 1, figsize=(5, len(avg_mods_per_tier_node)*3))
    for algorithm, values in avg_mods_per_tier_node.items():
        tier_avg = dict()
        for tier, avg_n_modules in values.items():
            tier_avg[tier] = sum(avg_n_modules) / len(avg_n_modules)
        if len(avg_mods_per_tier_node) == 1:
            axs.bar(tier_avg.keys(), tier_avg.values(), color=colors)
            axs.set_title(algorithm)
            axs.set_xlabel('Tier')
            axs.set_xticks(range(0, len(tier_avg)))
            # axs.set_yticks(range(0, max_info, int(max_info / 5)))
            axs.set_ylabel('Avg Num of Modules in a Node')

        else:
            axs[i].bar(tier_avg.keys(), tier_avg.values(), color=colors)
            axs[i].set_title(algorithm)
            axs[i].set_xlabel('Tier')
            axs[i].set_xticks(range(0, len(tier_avg)))
            #axs.set_yticks(range(0, max_info, int(max_info / 5)))
            axs[i].set_ylabel('Avg Num of Modules in a Node')
        i += 1
    plt.subplots_adjust(hspace=0.5)
    fig.suptitle('Average Number of Mods in Each Node per Tier')
    save_plot('ModsTiers__Average_N_Mods_in_each_Node_per_Tier')
    plt.show()


def plot_number_modules_in_cloud(total_modules_cloud, n_iterations):
    algorithms = total_modules_cloud.keys()
    n_modules_cloud = [total_modules_cloud[x] / n_iterations for x in algorithms]
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']

    plt.figure(figsize=(10, 6))
    bars = plt.bar(algorithms, n_modules_cloud, color=colors)

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.21, top=0.9)
    plt.xticks(rotation=45)
    plt.xlabel('Algorithms')
    plt.ylabel('Number of Modules in the Cloud')
    plt.title('Number of modules in the cloud per algorithm')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), va='bottom', ha='center')

    save_plot('ModsCloud__Plot_Number_Modules_in_Cloud')
    plt.show()


# plot FRAM per tier per algorithm
def plot_fram_per_tier_per_algorithm(total_FRAM_per_tier, nIterations):
    i = 0
    fig, axs = plt.subplots(len(total_FRAM_per_tier), 1, figsize=(5, len(total_FRAM_per_tier) * 3))
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']

    for algorithm in total_FRAM_per_tier.keys():

        tier_list = total_FRAM_per_tier[algorithm].keys()
        info_list_FRAM = [total_FRAM_per_tier[algorithm][x][0] / total_FRAM_per_tier[algorithm][x][1] * 100 for x in
                          tier_list]
        max_info = int(max(info_list_FRAM))
        incremento = 20
        if len(total_FRAM_per_tier) == 1:
            axs.bar(tier_list, info_list_FRAM, color=colors)
            axs.set_title(algorithm)
            axs.set_xlabel('Tier')
            axs.set_xticks(range(0, len(tier_list)))
            axs.set_yticks(range(0, max_info, incremento))
            axs.set_ylabel('FRAM (%)')
            axs[i].set_ylim(0, 110)
        else:
            axs[i].bar(tier_list, info_list_FRAM, color=colors)
            axs[i].set_title(algorithm)
            axs[i].set_xlabel('Tier')
            axs[i].set_xticks(range(0, len(tier_list)))
            axs[i].set_yticks(range(0, max_info, incremento))
            axs[i].set_ylabel('FRAM (%)')
            axs[i].set_ylim(0, 110)

        for x, y in zip(tier_list, info_list_FRAM):
            axs[i].text(x, y + 1, round(total_FRAM_per_tier[algorithm][x][0] / nIterations, 2), ha='center')

        i += 1

    plt.subplots_adjust(hspace=0.5)
    fig.suptitle('FRAM per Tier per Algorithm')
    save_plot('ModsTiers__FRAM_per_Tier_per_Algorithm')
    plt.show()

def plot_difference_in_fitness_for_generations(histoSolutions, tournament_size=2):
    # line plot, histoSolutions = ((min fitness, avg fitness, generation), ...)
    min_fitness = [x[0] for x in histoSolutions]
    avg_fitness = [x[1] for x in histoSolutions]
    dif = [avg_fitness[i] - min_fitness[i] for i in range(len(min_fitness))]
    generation = [x[2] for x in histoSolutions]

    plt.figure()  # Create a new figure
    plt.plot(generation, dif, label='Difference')
    plt.xlabel('Generation')
    plt.ylabel('Difference')
    plt.title('Difference between Min and Avg Fitness per Generation' + f'(Tournament_{tournament_size})')
    plt.legend()
    save_plot('Difference_between_Min_and_Avg_Fitness_per_Generation' + f'(Tournament_{tournament_size})')
    plt.show()


def plot_fitness_for_generation(histoSolutions, tournament_size=2):
    # line plot, histoSolutions = ((min fitness, avg fitness, generation), ...)
    min_fitness = [x[0] for x in histoSolutions]
    avg_fitness = [x[1] for x in histoSolutions]
    generation = [x[2] for x in histoSolutions]

    plt.figure()  # Create a new figure
    plt.plot(generation, min_fitness, label='Min Fitness')
    plt.plot(generation, avg_fitness, label='Avg Fitness')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.title('Fitness per Generation' + f'(Tournament_{tournament_size})')
    plt.legend()
    save_plot('Fitness_per_Generation' + f'(Tournament_{tournament_size})')
    plt.show()

def plot_box_plot_fitness_each_50_generations(fitness_per_50th_generation):
    # box plot, fitness_per_50th_generation = [[fitness for each element in generation 50], [fitness for each element in generation 100], ...]
    plt.boxplot(fitness_per_50th_generation)
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.title('Fitness per Generation')
    plt.show()
    