## Usage

The power-ps monitoring tool monitors a specfic process and it's children processes if there are any. Run example(assumes python3.5): python 28736 --interval 2 --duration 60 --plot process_graph.png --include-children. This will attach to process 28736 check every 2 seconds, run for 60 seconds generate a graph called process_graph.png and include children processes if there are any. Duration is optional, you can send a SIGTERM to the script process to kill it and it will still generate the graph for use over an unknown duration.

## Modules
Relies on the following modules: time, argparse, psutil, signal and sys.
