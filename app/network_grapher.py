import os
import random

import pylab
import networkx as nx


class NetworkGraphHandler:
    _output_directory = '../figures/'
    _file_ext = '.png'

    def __init__(self):
        # Create the directory where we will store figures if it doesn't exist already
        if not os.path.isdir(self._output_directory):
            os.makedirs(self._output_directory)

        self._graph = nx.Graph()
        self._figure_number = 0

    def _add_nodes(self, edge):
        for node in edge:
            if node not in self._graph.nodes():
                x_position = random.randrange(0, 100)
                y_position = random.randrange(0, 100)
                self._graph.add_node(node, Position=(x_position, y_position))

    def _get_fig(self, edge):
        self._add_nodes(edge)
        self._graph.add_edge(*edge)
        figure = pylab.figure()
        nx.draw(self._graph, pos=nx.get_node_attributes(self._graph, 'Position'))
        return figure

    def draw_updated_graph(self, *edge):
        new_figure = self._get_fig(edge)
        new_figure.canvas.draw()
        pylab.draw()
        pylab.savefig(self._output_directory + f'{self._figure_number}'.zfill(5) + self._file_ext, type='png')
        pylab.close(new_figure)
        self._figure_number += 1
