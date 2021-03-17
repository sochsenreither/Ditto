from re import search
from collections import defaultdict
from statistics import mean, stdev
from glob import glob
from os.path import join

from benchmark.utils import PathMaker


class Setup:
    def __init__(self, nodes, rate, tx_size):
        self.nodes = nodes
        self.rate = rate
        self.tx_size = tx_size

    def __str__(self):
        return (
            f' Committee size: {self.nodes} nodes\n'
            f' Input rate: {self.rate} txs\n'
            f' Transaction size: {self.tx_size} B\n'
        )

    def __eq__(self, other):
        return isinstance(other, Setup) and str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def from_str(cls, raw):
        nodes = int(search(r'.* Committee size: (\d+)', raw).group(1))
        rate = int(search(r'.* Input rate: (\d+)', raw).group(1))
        tx_size = int(search(r'.* Transaction size: (\d+)', raw).group(1))
        return cls(nodes, rate, tx_size)


class Result:
    def __init__(self, mean_tps, mean_latency, std_tps=0, std_latency=0):
        self.mean_tps = mean_tps
        self.mean_latency = mean_latency
        self.std_tps = std_tps
        self.std_latency = std_latency

    def __str__(self):
        return(
            f' TPS: {self.mean_tps} +/- {self.std_tps} tx/s\n'
            f' Latency: {self.mean_latency} +/- {self.std_latency} ms\n'
        )

    @classmethod
    def from_str(cls, raw):
        tps = int(search(r'.* End-to-end TPS: (\d+)', raw).group(1))
        latency = int(search(r'.* End-to-end latency: (\d+)', raw).group(1))
        return cls(tps, latency)

    @classmethod
    def aggregate(cls, results):
        if len(results) == 1:
            return results[0]

        mean_tps = round(mean([x.mean_tps for x in results]))
        mean_latency = round(mean([x.mean_latency for x in results]))
        std_tps = round(stdev([x.mean_tps for x in results]))
        std_latency = round(stdev([x.mean_latency for x in results]))
        return cls(mean_tps, mean_latency, std_tps, std_latency)


class LogAggregator:
    def __init__(self):
        filenames = glob(join(PathMaker.results_path(), '*.txt'))
        data = ''
        for filename in filenames:
            with open(filename, 'r') as f:
                data += f.read()

        records = defaultdict(list)
        for chunk in data.replace(',', '').split('RESULTS')[1:]:
            if chunk:
                records[Setup.from_str(chunk)] += [Result.from_str(chunk)]

        self.records = {k: Result.aggregate(v) for k, v in records.items()}

    def print(self):
        self._print_latency()
        self._print_tps()

    def _print_latency(self):
        organized = defaultdict(list)
        for setup, result in self.records.items():
            setup.rate = 'X'
            organized[setup] += [(result.mean_tps, result)]

        for setup, values in organized.items():
            values.sort(key=lambda x: x[0])
            data = '\n'.join(f' Variable value: X={x}\n{y}' for x, y in values)
            string = (
                '\n'
                '-----------------------------------------\n'
                ' RESULTS:\n'
                '-----------------------------------------\n'
                f'{setup}'
                '\n'
                f'{data}'
                '-----------------------------------------\n'
            )

            filename = f'{setup.nodes}-x-{setup.tx_size}.txt'
            with open(filename, 'w') as f:
                f.write(string)

    def _print_tps(self, max_latency=4000):
        organized = defaultdict(list)
        for setup, result in self.records.items():
            if result.mean_latency <= max_latency:
                nodes = setup.nodes
                setup.nodes = 'X'
                setup.rate = '-'
               
                new_point = all(nodes != x[0] for x in organized[setup])
                highest_tps = False
                for w, r in organized[setup]:
                    if result.mean_tps > r.mean_tps and nodes == w:
                        organized[setup].remove((w, r))
                        highest_tps = True
                if new_point or highest_tps:
                    organized[setup] += [(nodes, result)]

        print(organized)
        for setup, values in organized.items():
            values.sort(key=lambda x: x[0])
            data = '\n'.join(f' Variable value: X={x}\n{y}' for x, y in values)
            string = (
                '\n'
                '-----------------------------------------\n'
                ' RESULTS:\n'
                '-----------------------------------------\n'
                f'{setup}'
                '\n'
                f'{data}'
                '-----------------------------------------\n'
            )

            filename = f'x-any-{setup.tx_size}.txt'
            with open(filename, 'w') as f:
                f.write(string)
