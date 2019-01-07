from __future__ import (unicode_literals, division, print_function,
                        absolute_import)

import time
import argparse
import psutil
import signal
import sys

class BaseMemoryStats():
    def __init__(self):
        self.rss = 0
        self.vms = 0

def get_percent(process):
    try:
        return process.cpu_percent()
    except AttributeError:
        return process.get_cpu_percent()
    except:
        return 0

def get_memory(process):
    try:
        return process.memory_info()
    except AttributeError:
        return process.get_memory_info()
    except:
        return BaseMemoryStats()

def all_children(pr):
    processes = []
    children = []
    try:
        children = pr.children()
    except AttributeError:
        children = pr.get_children()
    except Exception:  # pragma: no cover
        pass

    for child in children:
        processes.append(psutil.Process(child.pid))
    return processes


def main():

    parser = argparse.ArgumentParser(
        description='Record CPU and memory usage for a process')

    parser.add_argument('process_id_or_command', type=str,
                        help='the process id or command')

    parser.add_argument('--log', type=str,
                        help='output the statistics to a file')

    parser.add_argument('--plot', type=str,
                        help='output the statistics to a plot')

    parser.add_argument('--duration', type=float,
                        help='how long to record for (in seconds). If not '
                             'specified, the recording is continuous until '
                             'the job exits.')

    parser.add_argument('--interval', type=float,
                        help='how long to wait between each sample (in '
                             'seconds). By default the process is sampled '
                             'as often as possible.')

    parser.add_argument('--include-children',
                        help='include sub-processes in statistics (results '
                             'in a slower maximum sampling rate).',
                        action='store_true')

    args = parser.parse_args()

    # Attach to process
    try:
        pid = int(args.process_id_or_command)
        print("Attaching to process {0}".format(pid))
        sprocess = None
    except Exception:
        import subprocess
        command = args.process_id_or_command
        print("Starting up command '{0}' and attaching to process"
              .format(command))
        sprocess = subprocess.Popen(command, shell=True)
        pid = sprocess.pid

    monitor(pid, logfile=args.log, plot=args.plot, duration=args.duration,
            interval=args.interval, include_children=args.include_children)

    if sprocess is not None:
        sprocess.kill()


def monitor(pid, logfile=None, plot=None, duration=None, interval=None,
            include_children=False):

    # We import psutil here so that the module can be imported even if psutil
    # is not present (for example if accessing the version)
    import psutil

    def signal_term_handler(signal, frame):
        try:
            print("SIGTERM detected. Generating graphs...")
            plot_graphs(process_name, log, plot)
        except Exception as e:
           print("Error: Unable to handle SIGTERM")
           print(str(e))

        # Stopping stats collection
        sys.exit(0)

    # Registering the callback
    signal.signal(signal.SIGTERM, signal_term_handler)

    pr = psutil.Process(pid)
    children = all_children(pr)
    process_name = "Process: '%s'" % str(pr.name())
    if len(children) > 0 and include_children:
        process_name += " | Num Children: '%s'" % str(len(children))

    # Record start time
    start_time = time.time()

    if logfile:
        f = open(logfile, 'w')
        f.write("# {0:12s} {1:12s} {2:12s} {3:12s}\n".format(
            'Elapsed time'.center(12),
            'CPU (%)'.center(12),
            'Real (MB)'.center(12),
            'Virtual (MB)'.center(12))
        )

    log = {}
    log['times'] = []
    log['cpu'] = []
    log['mem_real'] = []
    log['mem_virtual'] = []

    try:

        # Start main event loop
        while True:

            # Find current time
            current_time = time.time()

            # Check if we have reached the maximum time
            if duration is not None and current_time - start_time > duration:
                break

            # Get current CPU and memory
            try:
                current_cpu = get_percent(pr)
                current_mem = get_memory(pr)
            except Exception:
                break
            current_mem_real = current_mem.rss / 1024. ** 2
            current_mem_virtual = current_mem.vms / 1024. ** 2

            # Get information for children
            if include_children:
                for child in children:
                    try:
                        current_cpu += get_percent(child)
                        current_mem = get_memory(child)
                    except Exception:
                        continue
                    current_mem_real += current_mem.rss / 1024. ** 2
                    current_mem_virtual += current_mem.vms / 1024. ** 2

            if logfile:
                f.write("{0:12.3f} {1:12.3f} {2:12.3f} {3:12.3f}\n".format(
                    current_time - start_time,
                    current_cpu,
                    current_mem_real,
                    current_mem_virtual))
                f.flush()

            if interval is not None:
                time.sleep(interval)

            # If plotting, record the values
            if plot:
                log['times'].append(current_time - start_time)
                log['cpu'].append(current_cpu)
                log['mem_real'].append(current_mem_real)
                log['mem_virtual'].append(current_mem_virtual)

        if plot:
            plot_graphs(process_name, log, plot)

    except KeyboardInterrupt:  # pragma: no cover
        pass

    if logfile:
        f.close()


def plot_graphs(process_name, log, plot):
    try:
        # Use non-interactive backend, to enable operation on headless machines
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        with plt.rc_context({'backend': 'agg'}):

            fig = plt.figure()
            plt.title(process_name)
            ax = fig.add_subplot(1, 1, 1)
            ay = fig.add_subplot(1, 1, 1)

            ax.plot(log['times'], log['cpu'], '-', lw=2, color='r')

            ax.set_ylabel('CPU (%) (100% = 1 Core Usage)', color='r')
            ax.set_xlabel('time (s)')
            ax.set_ylim(0., max(max(log['cpu']) * 1.2, 10.0))

            ax2 = ax.twinx()
            ay2 = ay.twinx()

            ax2.plot(log['times'], log['mem_real'], '-', lw=2, color='b')
            ay2.plot(log['times'], log['mem_virtual'], '-', lw=2, color='c')
            plt.legend(handles=[mpatches.Patch(color='b', label='Real Memory (MB)'), mpatches.Patch(color='c', label='Virtual Memory (MB)')])
            ax2.set_ylim(0, max(log['mem_virtual']) * 1.2)
            ay2.set_ylim(0, max(log['mem_virtual']) * 1.2)

            ax2.set_ylabel('See Legend', labelpad=-3)

            ax.grid()

            fig.savefig(plot)

    except Exception as e:
        print("Error: Could not generate graph")
        print(str(e))

if __name__ == "__main__":
    main()
