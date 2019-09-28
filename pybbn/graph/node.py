from copy import deepcopy
from functools import reduce


class Node(object):
    """
    A node.
    """

    def __init__(self, id):
        """
        :param id: Numeric identifier.
        """
        self.id = id
        self.metadata = dict()

    def add_metadata(self, k, v):
        """
        Adds metadata.
        :param k: Key. Typically a string value.
        :param v: Value. Any object.
        """
        self.metadata[k] = v

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memodict={}):
        cls = self.__class__
        result = cls.__new__(cls)
        memodict[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memodict))
        return result

    def __str__(self):
        return '{}'.format(self.id)


class BbnNode(Node):
    """
    A BBN node.
    """

    def __init__(self, variable, probs):
        """
        :param variable: A variable.
        :param probs: Array of conditional probabilities.
        """
        Node.__init__(self, variable.id)
        self.variable = variable
        self.probs = probs
        self.potential = None
        self.weight = len(self.variable.values)

    def get_weight(self):
        """
        Gets the weight, which is the number of values.
        :return: Weight.
        """
        # return len(self.variable.values)
        return self.weight

    def to_dict(self):
        """
        Gets a JSON serializable dictionary representation.
        :return: Dictionary.
        """
        return {
            'probs': [p for p in self.probs],
            'variable': self.variable.to_dict()
        }

    def __str__(self):
        return '{}|{}|{}'.format(self.id, self.variable.name, str.join(',', self.variable.values))


class Clique(Node):
    """
    A clique.
    """

    def __init__(self, nodes):
        """
        :param nodes: An array of BbnNodes.
        """
        nids = [n.id for n in nodes]
        nids.sort()
        sid = str.join('-', [str(x) for x in nids])
        Node.__init__(self, sid)
        self.nodes = nodes
        self.marked = False
        self.node_ids = set([node.id for node in self.nodes])

    def get_sid(self):
        sids = '-'.join(sorted([n.variable.name for n in self.nodes]))
        return sids

    def is_marked(self):
        """
        :return: A boolean indicating if the clique is marked.
        """
        return self.marked

    def mark(self):
        """
        Marks this clique.
        """
        self.marked = True

    def unmark(self):
        """
        Unmarks this clique.
        """
        self.marked = False

    def get_node_ids(self):
        """
        :return: An array of numeric ids of the nodes in this clique.
        """
        return self.node_ids

    def is_superset(self, that):
        """
        :param that: Clique.
        :return: A boolean indicating if this clique is a superset of the clique passed in.
        """
        s1 = self.get_node_ids()
        s2 = that.get_node_ids()
        return s1.issuperset(s2)

    def get_weight(self):
        """
        Gets the weight of this clique; the weight is product of the weights of the nodes in this clique.
        :return: Weight.
        """
        return reduce(lambda x, y: x * y, [node.get_weight() for node in self.nodes])

    def contains(self, id):
        """
        :param id: Numeric id.
        :return: A boolean indicating if the specified id exists in this clique.
        """
        result = len([n for n in self.nodes if n.id == id])
        if result > 0:
            return True
        else:
            return False

    def get_sep_set(self, that):
        """
        Creates a separation-set from this node and the one passed in. The separation-set is composed
        of the intersection of the two cliques. If this node has [0, 1, 2] and the node passed in has
        [1, 2, 3], then the separation set will be [1, 2].
        :param that: Clique.
        :return: Separation-set.
        """
        return SepSet(self, that)

    def __str__(self):
        names = sorted([node.variable.name for node in self.nodes])
        return '({})'.format(str.join(',', names))


class SepSet(Clique):
    """
    Separation-set.
    """

    def __init__(self, left, right):
        """
        :param left: Clique.
        :param right: Clique.
        """
        lhs = {x.id for x in left.nodes}
        rhs = {x.id for x in right.nodes}
        intersection = lhs & rhs

        sid = '-'.join(str(x) for arr in [lhs, intersection, rhs] for x in arr)
        Node.__init__(self, sid)
        self.nodes = [x for x in left.nodes if x.id in intersection]
        self.marked = False

        self.left = left
        self.right = right
        self.is_empty_intersection = False if len(intersection) > 0 else True

    @property
    def is_empty(self):
        return self.is_empty_intersection

    @property
    def cost(self):
        """
        :return: The cost.
        """
        return self.get_cost()

    @property
    def mass(self):
        """
        :return: The mass.
        """
        return self.get_mass()

    def get_cost(self):
        """
        The cost is the sum of the weights of the cliques connected to this separation-set.
        :return: Cost.
        """
        return self.left.get_weight() + self.right.get_weight()

    def get_mass(self):
        """
        The mass is the number of nodes in this separation-set.
        :return: Mass.
        """
        return len(self.nodes)

    def __str__(self):
        s = '{}'.format(str.join(',', [node.variable.name for node in self.nodes]))
        s = '|{} -- {} -- {}|'.format(self.left, s, self.right)
        return s
