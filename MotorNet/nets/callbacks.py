import copy
from tensorflow.keras.callbacks import Callback
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import clear_output


class BatchLogger(Callback):
    """A Logger that logs metrics per batch steps instead of per epoch step."""
    def __init__(self):
        super().__init__()
        self.history = {}
        self.weights_log = []

    def on_train_begin(self, logs=None):
        # log initial weights
        self.weights_log.append(copy.deepcopy(self.model.weights))

    def on_batch_end(self, batch, logs=None):
        logs = logs or {}
        for metric, v in logs.items():
            self.history.setdefault(metric, []).append(v)
        self.weights_log.append(copy.deepcopy(self.model.weights))


class TrainingPlotter(Callback):
    def __init__(self, task, plot_freq=20):
        super().__init__()
        self.task = task
        self.plot_freq = plot_freq
        self.loss = []
        self.logs = []
        self.cartesian_loss = []
        self.muscle_loss = []
        self.activity_loss = []
        self.weight_loss = []

    def on_train_begin(self, logs=None):
        self.loss = []
        self.logs = []
        self.cartesian_loss = []
        self.muscle_loss = []
        self.activity_loss = []
        self.weight_loss = []

    def on_batch_end(self, batch, logs=None):
        self.logs.append(logs)
        self.loss.append(logs.get('loss'))
        self.cartesian_loss.append(logs.get('RNN_loss') * self.task.loss_weights['cartesian position'])
        self.muscle_loss.append(logs.get('RNN_4_loss') * self.task.loss_weights['muscle state'])
        self.activity_loss.append((self.model.losses[0]))
        self.weight_loss.append((self.model.losses[1]))

        if batch % self.plot_freq == 0 or len(self.loss) == 1:
            [inputs, targets, init_states] = self.task.generate(batch_size=3, n_timesteps=self.task.last_n_timesteps)
            results = self.model([inputs, init_states], training=False)
            j_results = results['joint position']
            c_results = results['cartesian position']
            m_results = results['muscle state']
            h_results = results['gru_hidden0']

            clear_output(wait=True)
            n = np.arange(0, len(self.loss))
            fig = plt.figure(constrained_layout=True)
            gs = fig.add_gridspec(1, 1)
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.plot(n, self.cartesian_loss, label='cartesian loss')
            ax1.plot(n, self.muscle_loss, label='muscle activation loss')
            ax1.plot(n, self.activity_loss, label='RNN activity loss')
            ax1.plot(n, self.weight_loss, label='RNN weight loss')
            ax1.set(xlabel='iteration', ylabel='loss')
            ax1.legend()
            plt.show()

            for trial in range(3):
                plt.figure(figsize=(14, 2.5)).set_tight_layout(True)

                plt.subplot(141)
                plt.plot(targets[trial, :, 0].numpy().squeeze(), color='#1f77b4', linestyle='dashed')
                plt.plot(targets[trial, :, 1].numpy().squeeze(), color='#ff7f0e', linestyle='dashed')
                plt.plot(j_results[trial, :, 0].numpy().squeeze(), color='#1f77b4', label='sho')
                plt.plot(j_results[trial, :, 1].numpy().squeeze(), color='#ff7f0e', label='elb')
                plt.legend()
                plt.xlabel('time (ms)')
                plt.ylabel('angle (rad)')

                #plt.subplot(142)
                #plt.plot(j_results[trial, :, 2].numpy().squeeze(), label='sho')
                #plt.plot(j_results[trial, :, 3].numpy().squeeze(), label='elb')
                #plt.legend()
                #plt.xlabel('time (ms)')
                #plt.ylabel('angle velocity (rad/sec)')

                plt.subplot(142)
                plt.plot(m_results[trial, :, 0, :].numpy().squeeze())
                plt.xlabel('time (ms)')
                plt.ylabel('activation (a.u.)')

                plt.subplot(143)
                plt.plot(m_results[trial, :, 2, :].numpy().squeeze())
                plt.xlabel('time (ms)')
                plt.ylabel('muscle velocity (m/sec)')

                plt.subplot(144)
                plt.plot(h_results[trial, :, :].numpy().squeeze())
                plt.xlabel('time (ms)')
                plt.ylabel('hidden unit activity')

                plt.show()
