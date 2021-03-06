import os
import sys
import glob

import hydra
import numpy as np
import plotly.graph_objects as go
import plotly

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dotmap import DotMap

import logging

log = logging.getLogger(__name__)

# label_dict = {'t': 'Trajectory Based Deterministic',
#               'd': 'One Step Deterministic',
#               'p': 'One Step Probabilistic',
#               'tp': 'Trajectory Based Probabilistic',
#               'te': 'Trajectory Based Deterministic Ensemble',
#               'de': 'One Step Deterministic Ensemble',
#               'pe': 'One Step Probabilistic Ensemble',
#               'tpe': 'Trajectory Based Probabilistic Ensemble',
#               'c': 'Custom'}
# color_dict = {'t': 'r',
#               'd': 'b',
#               'p': 'g',
#               'tp': 'y',
#               'te': '#b53636',
#               'de': '#3660b5',
#               'pe': '#52b536',
#               'tpe': '#b57f11',
#               'c': '#8d67a6'}
# color_dict_plotly = {'t': 'rgb(200,0,0)',
#                      'd': 'rgb(0,0,128)',
#                      'p': 'rgb(0,128,0)',
#                      'tp': 'rgb(200,200,0)',
#                      'te': 'rgb(180,20,20)',
#                      'de': 'rgb(20,20,128)',
#                      'pe': 'rgb(20,128,20)',
#                      'tpe': 'rgb(180,180,25)',
#                      'c': 'rgb(141,103,166)'}
#
# marker_dict = {'t': 's',
#                'd': 'o',
#                'p': 'D',
#                'tp': 'p',
#                'te': 's',
#                'de': 'o',
#                'pe': 'D',
#                'tpe': 'p',
#                'c': '*'}
#
# marker_dict_plotly = {'t': 'cross-open-dot',
#                       'd': 'circle-open-dot',
#                       'p': 'x-open-dot',
#                       'tp': 'triangle-up-open-dot',
#                       'te': 'y-down-open',
#                       'de': 'diamond-open-dot',
#                       'pe': 'hourglass-open',
#                       'tpe': 'hash-open-dot',
#                       'c': 'star'}

setup = False
label_dict, color_dict, color_dict_plotly, marker_dict, marker_dict_plotly = None, None, None, None, None


def setup_plotting(models):
    """
    Populates the necessary dictionaries for plotting. Must run this before using most
    plotting functions (those that require the dictionary above.

    Parameters:
        models: a dictionary of models of the form {key (string): model (DynamicsModel)}
    """

    global label_dict, color_dict, color_dict_plotly, marker_dict, marker_dict_plotly, setup

    setup = True

    label_dict = {models[key].str: models[key].cfg.model.plotting.label for key in models}
    color_dict = {models[key].str: models[key].cfg.model.plotting.color for key in models}
    color_dict_plotly = {models[key].str: models[key].cfg.model.plotting.color_plotly for key in models}
    marker_dict = {models[key].str: models[key].cfg.model.plotting.marker for key in models}
    marker_dict_plotly = {models[key].str: models[key].cfg.model.plotting.marker_plotly for key in models}


def find_latest_checkpoint(cfg):
    '''
    Try to find the latest checkpoint in the log directory if cfg.checkpoint
    is not provided (usually through the command line).
    '''
    # same path as in save_log method, but with {} replaced to wildcard *
    checkpoint_paths = os.path.join(os.getcwd(),
                                    cfg.checkpoint_file.replace("{}", "*"))

    # use glob to find files (returned a list)
    files = glob.glob(checkpoint_paths)

    # If we cannot find one (empty file list), then do nothing and return
    if not files:
        return None

    # find the one with maximum last modified time (getmtime). Don't sort
    last_modified_file = max(files, key=os.path.getmtime)

    return last_modified_file


def plot_reacher(states, actions):
    ar = np.stack(states)
    l = np.shape(ar)[0]
    xs = np.arange(l)

    X = ar[:, -3]
    Y = ar[:, -2]
    Z = ar[:, -1]

    actions = np.stack(actions)

    fig = plotly.subplots.make_subplots(rows=2, cols=1,
                                        subplot_titles=("Position", "Action - Torques"),
                                        vertical_spacing=.15)  # go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=X, name='X',
                             line=dict(color='firebrick', width=4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=Y, name='Y',
                             line=dict(color='royalblue', width=4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=Z, name='Z',
                             line=dict(color='green', width=4)), row=1, col=1)

    fig.add_trace(go.Scatter(x=xs, y=actions[:, 0], name='M1',
                             line=dict(color='firebrick', width=4)), row=2, col=1)
    fig.add_trace(go.Scatter(x=xs, y=actions[:, 1], name='M2',
                             line=dict(color='royalblue', width=4)), row=2, col=1)
    fig.add_trace(go.Scatter(x=xs, y=actions[:, 2], name='M3',
                             line=dict(color='green', width=4)), row=2, col=1)
    fig.add_trace(go.Scatter(x=xs, y=actions[:, 3], name='M4',
                             line=dict(color='orange', width=4)), row=2, col=1)
    fig.add_trace(go.Scatter(x=xs, y=actions[:, 4], name='M5',
                             line=dict(color='black', width=4)), row=2, col=1)

    fig.update_layout(title='Position of Reacher Task',
                      xaxis_title='Timestep',
                      yaxis_title='Angle (Degrees)',
                      plot_bgcolor='white',
                      xaxis=dict(
                          showline=True,
                          showgrid=False,
                          showticklabels=True, ),
                      yaxis=dict(
                          showline=True,
                          showgrid=False,
                          showticklabels=True, ),
                      )
    fig.show()


def generate_errorbar_traces(ys, xs=None, percentiles='66+95', color=None, name=None):
    if xs is None:
        xs = [list(range(len(y))) for y in ys]

    minX = min([len(x) for x in xs])

    xs = [x[:minX] for x in xs]
    ys = [y[:minX] for y in ys]

    assert all([(len(y) == len(ys[0])) for y in ys]), \
        'Y should be the same size for all traces'

    assert all([(x == xs[0]) for x in xs]), \
        'X should be the same for all traces'

    y = np.array(ys)

    def median_percentile(data, des_percentiles='66+95'):
        median = np.nanmedian(data, axis=0)
        out = np.array(list(map(int, des_percentiles.split("+"))))
        for i in range(out.size):
            assert 0 <= out[i] <= 100, 'Percentile must be >0 <100; instead is %f' % out[i]
        list_percentiles = np.empty((2 * out.size,), dtype=out.dtype)
        list_percentiles[0::2] = out  # Compute the percentile
        list_percentiles[1::2] = 100 - out  # Compute also the mirror percentile
        percentiles = np.nanpercentile(data, list_percentiles, axis=0)
        return [median, percentiles]

    out = median_percentile(y, des_percentiles=percentiles)
    ymed = out[0]
    # yavg = np.median(y, 0)

    err_traces = [
        dict(x=xs[0], y=ymed.tolist(), mode='lines', name=name, type='scatter', legendgroup=f"group-{name}",
             line=dict(color=color, width=4))]

    intensity = .3
    '''
    interval = scipy.stats.norm.interval(percentile/100, loc=y, scale=np.sqrt(variance))
    interval = np.nan_to_num(interval)  # Fix stupid case of norm.interval(0) returning nan
    '''

    for i, p_str in enumerate(percentiles.split("+")):
        p = int(p_str)
        high = out[1][2 * i, :]
        low = out[1][2 * i + 1, :]

        err_traces.append(dict(
            x=xs[0] + xs[0][::-1], type='scatter',
            y=(high).tolist() + (low).tolist()[::-1],
            fill='toself',
            fillcolor=(color[:-1] + str(f", {intensity})")).replace('rgb', 'rgba')
            if color is not None else None,
            line=dict(color='rgba(0,0,0,0.0)'),
            legendgroup=f"group-{name}",
            showlegend=False,
            name=name + str(f"_std{p}") if name is not None else None,
        ), )
        intensity -= .1

    return err_traces, xs, ys


def plot_states(ground_truth, predictions, idx_plot=None, plot_avg=True, save_loc=None, show=True):
    """
    Plots the states given in predictions against the groundtruth. Predictions
    is a dictionary mapping model types to predictions
    """
    assert setup, "Must run setup_plotting before this function"

    num = np.shape(ground_truth)[0]
    dx = np.shape(ground_truth)[1]
    if idx_plot is None:
        idx_plot = list(range(dx))

    if plot_avg:
        fig, ax = plt.subplots()
        plt.title("Predictions Averaged")
        plt.xlabel("Timestep")
        plt.ylabel("Average State Value")
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        gt = np.zeros(ground_truth[:, 0:1].shape)
        for i in idx_plot:
            gt = np.hstack((gt, ground_truth[:, i:i + 1]))
        gt_avg = np.average(gt[:, 1:], axis=1)
        plt.plot(gt_avg, c='k', label='Groundtruth')

        for key in predictions:
            pred = predictions[key]
            p = np.zeros(pred[:, 0:1].shape)
            for i in idx_plot:
                p = np.hstack((p, pred[:, i:i + 1]))
            p_avg = np.average(p[:, 1:], axis=1)
            chopped = [(x if abs(x) < 3 else float("nan")) for x in p_avg]
            plt.plot(chopped, c=color_dict[key], label=label_dict[key], markersize=10, marker=marker_dict[key],
                     markevery=50)
        # plt.ylim(-.5, 1.5)
        plt.legend()
        if save_loc:
            plt.savefig(save_loc + "-avg_states.pdf")
        if show:
            plt.show()
        else:
            plt.close()

    for i in idx_plot:
        fig, ax = plt.subplots()
        gt = ground_truth[:, i]
        plt.title("Predictions on one dimension")
        plt.xlabel("Timestep")
        plt.ylabel("State Value")
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.plot(gt, c='k', label='Groundtruth')
        for key in predictions:
            # print(key)
            pred = predictions[key][:, i]
            # chopped = np.maximum(np.minimum(pred, 3), -3)  # to keep it from messing up graphs when it diverges
            chopped = [(x if abs(x) < 3 else float("nan")) for x in pred]
            plt.plot(chopped, c=color_dict[key], label=label_dict[key], markersize=10, marker=marker_dict[key],
                     markevery=50)

        plt.legend()

        if save_loc:
            plt.savefig(save_loc + "-state%d.pdf" % i)
        if show:
            plt.show()
        else:
            plt.close()


def plot_loss(train_logs, test_logs, cfg, save_loc=None, show=False, title=None):
    """
    Plots the loss against the epoch number, designed to work with Nathan's DynamicsModel
    TODO: only integers on x-axis

    Parameters:
        logs: a list of lists of loss values, one list for each net in the model
        s: the string describing the model, ie 'd' or 'tpe'
    """
    assert setup, "Must run setup_plotting before this function"

    fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                        # subplot_titles=("Position", "Action - Torques"),
                                        vertical_spacing=.15)  # go.Figure()
    colors = [
        '#1f77b4',  # muted blue
        '#ff7f0e',  # safety orange
        '#2ca02c',  # cooked asparagus green
        '#d62728',  # brick red
        '#9467bd',  # muted purple
        '#8c564b',  # chestnut brown
        '#e377c2',  # raspberry yogurt pink
        '#7f7f7f',  # middle gray
        '#bcbd22',  # curry yellow-green
        '#17becf'  # blue-teal
    ]

    markers = [
        "cross-open-dot",
        "circle-open-dot",
        "x-open-dot",
        "triangle-up-open-dot",
        "y-down-open",
        "diamond-open-dot",
        "hourglass-open",
        "hash-open-dot",
        "star-open-dot",
        "square-open-dot",
    ]

    def add_line(fig, log, type, ind=-1):
        if ind == -1:
            name = type
        else:
            name = type + str(ind)
        if type == 'Test':
            fig.add_trace(go.Scatter(x=np.arange(len(log)).tolist(), y=log,
                                     name=name, legendgroup=type,
                                     line=dict(color=colors[ind], width=4),
                                     marker=dict(color=colors[ind], symbol=markers[ind], size=16)),
                          row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=np.arange(len(log)).tolist(), y=log,
                                     name=name, legendgroup=type,
                                     line=dict(color=colors[ind], width=4, dash='dash'),
                                     marker=dict(color=colors[ind], symbol=markers[ind], size=16)),
                          row=1, col=1)
        return fig

    if len(np.shape(train_logs)) > 1:
        # ENSEMBLE
        for i, (train, test) in enumerate(zip(train_logs, test_logs)):
            fig = add_line(fig, train, type="Train", ind=i)
            fig = add_line(fig, test, type="Test", ind=i)
    else:
        # BASE
        fig = add_line(fig, train_logs, type="Train", ind=-1)
        fig = add_line(fig, test_logs, type="Test", ind=-1)

    fig.update_layout(font=dict(
        family="Times New Roman, Times, serif",
        size=24,
        color="black"
    ),
        title='Training Plot ' + cfg.model.str,
        xaxis_title='Epoch',
        yaxis_title='Loss',
        plot_bgcolor='white',
        width=1000,
        height=1000,
        margin=dict(l=10, r=0, b=10),
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True, ),
        yaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True, ),
    )
    if show: fig.show()
    fig.write_image(save_loc + ".png")


def add_marker(err_traces, color=[], symbol=None, skip=None):
    mark_every = 100
    size = 30
    l = len(err_traces[0]['x'])
    if skip is not None:
        size_list = [0] * skip + [size] + [0] * (mark_every - 1 - skip)
    else:
        size_list = [size] + [0] * (mark_every - 1)
    repeat = int(l / mark_every)
    size_list = size_list * repeat
    line = err_traces[0]
    line['mode'] = 'lines+markers'
    line['marker'] = dict(
        color=line['line']['color'],
        size=size_list,
        symbol="x" if symbol is None else symbol,
        line=dict(width=4,
                  color='rgba(1,1,1,1)')
    )
    err_traces[0] = line
    return err_traces


def plot_mse_err(mse_batch, save_loc=None, show=True, log_scale=True, title=None):
    assert setup, "Must run setup_plotting before this function"

    arrays = []
    keys = [k for k in mse_batch[0].keys()]
    for k in keys:
        temp = []
        for data in mse_batch:
            temp.append(data[k])
        arrays.append(np.stack(temp))

    traces_plot = []
    for ar, k in zip(arrays, keys):
        tr, xs, ys = generate_errorbar_traces(ar, xs=None, percentiles='66+95', color=color_dict_plotly[k],
                                              name=label_dict[k])
        w_marker = []
        # for t in tr:
        m = add_marker(tr, color=color_dict_plotly[k], symbol=marker_dict_plotly[k], skip=25)
        # w_marker.append(m)
        [traces_plot.append(t) for t in m]

    layout = dict(title=f"Average Error over Run",
                  xaxis={'title': 'Prediction Step'},
                  yaxis={'title': 'Mean Error', 'range': [np.log10(0.01), np.log10(10000)]},
                  yaxis_type="log",
                  font=dict(family='Times New Roman', size=30, color='#7f7f7f'),
                  height=1000,
                  width=1500,
                  plot_bgcolor='white',
                  legend={'x': .01, 'y': .98, 'bgcolor': 'rgba(50, 50, 50, .03)',
                          'font': dict(family='Times New Roman', size=22, color='#7f7f7f')}
                  )

    fig = {
        'data': traces_plot,
        'layout': layout
    }

    import plotly.io as pio
    fig = go.Figure(fig)
    if show: fig.show()
    fig.write_image(save_loc + ".pdf")

    return fig


def plot_mse(MSEs, save_loc=None, show=True, log_scale=True, title=None):
    """
    Plots MSE graphs for the sequences given given

    Parameters:
    ------------
    MSEs: a dictionary mapping model type key to an array of MSEs
    """
    assert setup, "Must run setup_plotting before this function"

    fig, ax = plt.subplots()
    title = title or "%s MSE for a variety of models" % ('Log ' if log_scale else '')
    plt.title(title)
    plt.xlabel("Timesteps")
    plt.ylabel('Mean Square Error')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    for key in MSEs:
        mse = MSEs[key]
        if log_scale:
            plt.semilogy(mse, color=color_dict[key], label=label_dict[key], marker=marker_dict[key], markevery=50)
        else:
            plt.plot(mse, color=color_dict[key], label=label_dict[key], marker=marker_dict[key], markevery=50)
    plt.legend()
    if save_loc:
        plt.savefig(save_loc)
    if show:
        plt.show()
    else:
        plt.close()


def plot_lorenz(data, cfg, predictions=None):
    assert setup, "Must run setup_plotting before this function"

    import plotly.graph_objects as go

    fig = go.Figure()

    for dat in data:
        x, y, z = dat.states[:, 0], dat.states[:, 1], dat.states[:, 2]
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            # color=(1, c[i], 0),
            marker=dict(
                size=2,
                color=np.arange(len(x)),
                colorscale='Viridis',
            ),
            line=dict(
                color='black',
                width=4
            ),
        ))

    color_scales_dict = {'t': 'Inferno',
                     'd': 'Magma',
                     'p': 'Plasma',
                     'tp': 'Blackbody',
                     'te': 'Electric',
                     'de': 'Hot',
                     'pe': 'Jet',
                     'tpe': 'Plotly3'}

    if predictions is not None:
        for key, p in predictions.items():
            fig.add_trace(go.Scatter3d(x=p[:, 0], y=p[:, 1], z=p[:, 2],
                                       name=label_dict[key], legendgroup=key,
                                       marker=dict(
                                           size=1,
                                           color=np.arange(len(x)),
                                           colorscale=color_scales_dict[key],
                                       ),
                                       line=dict(
                                           color=color_dict_plotly[key],
                                           width=1
                                       ),
                                       ))


    fig.update_layout(
        width=1500,
        height=800,
        autosize=False,
        showlegend=True if predictions is not None else False,
        font=dict(
            family="Times New Roman, Times, serif",
            size=18,
            color="black"
        ),
        scene_camera=dict(eye=dict(x=1.5 * -.1, y=1.5 * 1.5, z=1.5 * .25)),
        scene=dict(
            # xaxis=dict(nticks=4, range=[-100, 100], ),
            # yaxis=dict(nticks=4, range=[-100, 100], ),
            # zaxis=dict(nticks=4, range=[-100, 100], ),
            xaxis=dict(nticks=5, range=[-40, 40],
                       backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgb(128, 128, 128)",
                       showbackground=True,
                       zerolinecolor="rgb(0, 0, 0)",
                       ),
            yaxis=dict(nticks=5, range=[-60, 60],
                       backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgb(128, 128, 128)",
                       showbackground=True,
                       zerolinecolor="rgb(0, 0, 0)",
                       ),
            zaxis=dict(nticks=5, range=[-40, 75],
                       backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgb(128, 128, 128)",
                       showbackground=True,
                       zerolinecolor="rgb(0, 0, 0)",
                       ),
            aspectratio=dict(x=1.2, y=1.2, z=0.7),
            aspectmode='manual'
        ),
        margin=dict(r=10, l=10, b=10, t=10),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        # plot_bgcolor='rgba(0,0,0,0)'
    )

    fig.show()
    fig.write_image(os.getcwd() + "/lorenz.png")


def plot_sorted(ground_truth, deltas, idx_plot=None, save_loc=None, show=True):
    assert setup, "Must run setup_plotting before this function"

    num = ground_truth.shape[0]
    dx = ground_truth.shape[1]
    if idx_plot is None:
        idx_plot = list(range(dx))

    # Extracting deltas
    ground_truth_d = ground_truth[1:,:] - ground_truth[:-1,:]
    deltas = {key: deltas[key][:-1,:] for key in deltas}

    for idx in idx_plot:
        # Sorting
        gt = ground_truth_d[:,idx].ravel()
        delt = [{key: deltas[key][i,idx] for key in deltas} for i in range(num-1)]
        zipped = list(zip(gt, delt))
        zipped.sort()
        arr = np.array(zipped)
        gts = []
        delts = {key: [] for key in deltas}
        for gt_i, delts_i in zipped:
            gts.append(gt_i)
            _ = {key: delts[key].append(delts_i[key]) for key in delts}

        # Plotting
        fig, ax = plt.subplots()
        plt.title("Sorted Predictions - Dimension %d" % idx)
        plt.ylabel("Delta Predictions")
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.plot(gts, c='k', label='Groundtruth')
        for key in delts:
            # plt.plot(preds[key], label=label_dict[key], c=color_dict[key])
            plt.scatter(np.arange(len(delts[key])), delts[key], c=color_dict[key],
                        label=label_dict[key], marker=marker_dict[key], s=3)

        plt.ylim(min(np.min(gt)*.8, np.min(gt)*1.2), max(np.max(gt)*.8, np.max(gt)*1.2))
        plt.legend()

        if save_loc:
            plt.savefig(save_loc + "-state%d.pdf" % idx)
        if show:
            plt.show()
        else:
            plt.close()

    # Debug: plot unsorted
    for idx in idx_plot:
        gt = ground_truth_d[:,idx].ravel()
        pred = {key: deltas[key][:,idx].ravel() for key in deltas}

        fig, ax = plt.subplots()
        plt.title("Unsorted Predictions - Dimension %d" % idx)
        plt.ylabel("Delta Predictions")
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.plot(gt, c='k', label='Groundtruth')
        for key in pred:
            plt.plot(pred[key], label=label_dict[key], c=color_dict[key])

        plt.ylim(min(np.min(gt)*.8, np.min(gt)*1.2), max(np.max(gt)*.8, np.max(gt)*1.2))
        plt.legend()

        if save_loc:
            plt.savefig(save_loc + "-unsorted-state%d.pdf" % idx)
        if show:
            plt.show()
        else:
            plt.close()


def plot_evaluations(data, x, ylabel=None, xlabel=None, title=None, log_scale=False, save_loc=None, show=True):
    """
    Plots plots for sample efficiency tests

    data: dictionary of arrays of eval values
    """
    assert setup, "Must run setup_plotting before this function"

    fig, ax = plt.subplots()
    plt.title(title or "Trajectory prediction evalutaions")
    if ylabel:
        plt.ylabel(ylabel)
    if xlabel:
        plt.xlabel(xlabel)
    if log_scale:
        plt.yscale('log')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    for key in data:
        plt.plot(x, data[key], color=color_dict[key], label=label_dict[key], marker=marker_dict[key])
    plt.legend()
    if save_loc:
        plt.savefig(save_loc)
    if show:
        plt.show()
    else:
        plt.close()


def plot_evaluations_3d(data, x, y, ylabel=None, xlabel=None, zlabel=None, title=None, log_scale=False, save_loc=None, show=True):
    assert setup, "Must run setup_plotting before this function"

    X = np.tile(x, len(y)).reshape(len(y), -1).T
    Y = np.tile(y, len(x)).reshape(len(x), -1)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    plt.title(title or "Trajectory prediction evalutaions")
    if ylabel:
        yLabel = ax.set_ylabel(ylabel)
    if xlabel:
        xLabel = ax.set_xlabel(xlabel)
    if zlabel:
        zLabel = ax.set_zlabel(zlabel)
    if log_scale:
        data = {key: np.log(data[key]) for key in data}
    for key in data:
        ax.plot_wireframe(X, Y, data[key], color=color_dict[key], label=label_dict[key])
    plt.legend(loc='middle right')
    ax.view_init(elev=40, azim=-130)
    if save_loc:
        plt.savefig(save_loc)
    if show:
        plt.show()
    else:
        plt.close()


@hydra.main(config_path='config-plot.yaml')
def plot(cfg):
    pass


if __name__ == '__main__':
    sys.exit(plot())
