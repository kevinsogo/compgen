import itertools, math

class GeomError(Exception): ...

def interval_contains(a, b, v):
    return min(a, b) <= v <= max(a, b)

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        super().__init__()

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, s):
        return Point(self.x * s, self.y * s)

    __rmul__ = __mul__

    def __truediv__(self, d):
        return Point(self.x / d, self.y / d)

    def __floordiv__(self, d):
        return Point(self.x // d, self.y // d)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def cross(self, other):
        return self.x * other.y - self.y * other.x

    def rotleft(self):
        return Point(-self.y, self.x)

    def rotright(self):
        return Point(self.y, -self.x)

    def on_axis(self):
        return any(self.dot(axis) == 0 for axis in (Point(1, 0), Point(0, 1)))

    rectilinear = on_axis

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not (self == other)

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __hash__(self):
        return (hash((self.x, self.y)) * 3) ^ 0xcfb24569ab3dddac

    def mag2(self):
        return self.x**2 + self.y**2

    def __bool__(self):
        return bool(self.x) or bool(self.y)

    def __iter__(self):
        yield self.x
        yield self.y

    def __str__(self):
        return f'({self.x}, {self.y})'

    def __repr__(self):
        return f'Point({self.x!r}, {self.y!r})'


class Seg:
    # intended to be a (closed) line segment, but the current implementation makes this quite flexible.
    # it can also represent anything that can be represented by two points, e.g., a line, or a ray.
    # specialized operations are prefixed with line_, ray_, etc.
    # whether it is a segment, line or a ray, it is meant to be a closed set. (i.e., includes endpoints)
    # TODO maybe create a Line class, Ray class, etc.? and have meaningful interactions and conversions
    # between them?
    def __init__(self, a, b):
        if not (isinstance(a, Point) and isinstance(b, Point)):
            raise GeomError("Both endpoints must be Point instances")
        self.a = a
        self.b = b
        super().__init__()

    def bounding_box_contains(self, p):
        return interval_contains(self.a.x, self.b.x, p.x) and interval_contains(self.a.y, self.b.y, p.y)

    def __abs__(self):
        return abs(self.vec)

    @property
    def vec(self):
        return self.b - self.a

    def mag2(self):
        return self.vec.mag2()

    def parallel(self, other):
        return self.vec.cross(other.vec) == 0

    def perpendicular(self, other):
        return self.vec.dot(other.vec) == 0

    def rectilinear(self):
        return self.vec.on_axis()

    axis_aligned = rectilinear

    def intersects(self, other):
        return self.vec and other.vec and self.crosses(other) or any(p in other for p in self) or any(p in self for p in other)

    def crosses(self, other):
        return self.line_crosses(other) and other.line_crosses(self)

    def __and__(self, other):
        # find the intersection point or segment, or None ### @rem
        if self.crosses(other):
            return self.line_intersect_line(other)
        endpoints = {p for p in self if p in other} | {p for p in other if p in self}
        assert len(endpoints) <= 2
        if len(endpoints) == 2:
            # TODO the ordering of this might be dependent on the hashing function, so be careful! ### @rem
            a, b = endpoints
            return Seg(a, b)
        if len(endpoints) == 1:
            a, = endpoints
            return a

    def __contains__(self, pt):
        return self.line_contains(pt) and self.bounding_box_contains(pt)

    def line_crosses(self, other):
        # a line operation ### @rem
        if not self.vec: raise GeomError("not a line!")
        return not self.parallel(other) and self.vec.cross(other.a - self.a) * self.vec.cross(other.b - self.b) <= 0

    def line_intersect_line(self, other):
        # a line operation ### @rem
        ### @@ rem {
        # assumes 'other' is also a line
        # this is an inherently non-integer operation
        ### @@ }
        den = self.vec.cross(other.vec)
        if den == 0: raise GeomError("doesn't intersect in a line")
        return self.line_point_at((other.a - self.a).cross(other.vec) / den)

    def line_contains(self, pt):
        # a line operation
        return self.vec.cross(pt - self.a) == 0

    def line_point_at(self, t):
        # a ray operation
        return self.a + self.vec * t

    def seg_point_at(self, t):
        if 0 <= t <= 1: return self.line_point_at(t)

    def ray_point_at(self, t):
        if t >= 0: return self.line_point_at(t)

    def ray_crosses_line(self, other):
        # a ray operation ### @rem
        # assumes 'other' is a line ### @rem
        return not self.parallel(other) and (other.a - self.a).cross(other.vec) * self.vec.cross(other.vec) >= 0

    def __bool__(self):
        return self.a != self.b

    def __iter__(self):
        yield self.a
        yield self.b

    def __hash__(self):
        return (hash((self.a, self.b)) * 5) ^ 0x5a0add14e160f4bc

    def __str__(self):
        return f'[{self.a}, {self.b}]'

    def __repr__(self):
        return f'Seg({self.a!r}, {self.b!r})'

def collinear(a, b, c):
    return Seg(a, b).parallel(Seg(b, c))

class Edged:
    # also assumes '.vertices' exist... fix naming and ideas later. ### @rem
    def edges(self):
        raise NotImplementedError

    def intersects(self, other):
        # quadratic
        return (
            any(aedge.intersects(bedge) for aedge, bedge in itertools.product(self.edges(), other.edges())) or
            any(apt in bedge for apt, bedge in itertools.product(self, other.edges())) or
            any(bpt in aedge for aedge, bpt in itertools.product(self.edges(), other)) or
            any(apt == bpt for apt, bpt in itertools.product(self, other))
        )

class Polygon(Edged):
    def __init__(self, vertices):
        self.vertices = list(vertices)
        super().__init__()

    def edges(self):
        yield from (Seg(*pair) for pair in zip(self.vertices, self.vertices[1:] + self.vertices[:1]))

    sides = edges
    
    def simple(self):
        # quadratic implementation. TODO optimize to almost linear using sweep line ### @rem
        return not any(a.intersects(b)
                for (ai, a), (bi, b) in itertools.combinations(enumerate(self.edges()), 2)
                if abs(ai - bi) not in {1, len(self) - 1}) and self.signed_area2() != 0

    def overlaps(self, other):
        # two polygons contain a common point (either on interior or boundary) ### @rem
        raise NotImplementedError

    def in_boundary(self, pt):
        return any(pt in edge for edge in self.edges())

    def inside(self, pt):
        return not self.in_boundary(pt) and self.winding_number(pt) != 0

    def __contains__(self, pt):
        # contains in the boundary or interior ### @rem
        # equivalent to (in_boundary(pt) or inside(pt)) ### @rem
        return self.in_boundary(pt) or self.winding_number(pt) != 0

    def winding_number(self, pt):
        # counterclockwise = positive
        # only works for points not in the boundary of the polygon
        right_ray = Seg(pt, pt + Point(1, 0))
        return sum((ed.b.y > pt.y) - (ed.a.y > pt.y) for ed in self.edges() if right_ray.ray_crosses_line(ed))

    def rectilinear(self):
        return all(edge.rectilinear() for edge in self.edges())

    def counterclockwise(self):
        return self.signed_area2() > 0

    def clockwise(self):
        return self.signed_area2() < 0

    def signed_area2(self):
        ''' the twice of the signed area. counterclockwise = positive ''' ### @rem
        return sum(edge.a.cross(edge.b) for edge in self.edges())

    def area2(self):
        return abs(self.signed_area2())

    def subvertices(self, i, j):
        i %= len(self)
        j %= len(self)
        while True:
            assert 0 <= i < len(self)
            yield self.vertices[i]
            if i == j: break
            i += 1
            if i >= len(self): i -= len(self)

    def shortest_path(self, start, end):
        ### @@ rem {
        # a bit slow
        # assumes that the polygon is simple, but won't check because it's also slow!

        # also, assumes that the start and end points are strictly in the interior.
        # needs adjustment otherwise, though I imagine it's a simple adjustment. I'm just lazy.
        ### @@ }

        if not self.inside(start): raise GeomError("start point on boundary not supported... yet")
        if not self.inside(end): raise GeomError("end point on boundary not supported... yet")

        def get_edges():
            # direct path ### @rem
            seg = Seg(start, end)
            intersects = sum(map(seg.intersects, self.edges()))
            if intersects == 0:
                yield seg

            # start/end to vertex ### @rem
            for point in [start, end]:
                for vert in self.vertices:
                    seg = Seg(point, vert)
                    intersects = sum(map(seg.intersects, self.edges()))
                    assert intersects >= 2
                    if intersects == 2:
                        yield seg
            
            # vertex to vertex ### @rem
            # this is the slowest part... it takes cubic time. ### @rem
            for (ai, a), (bi, b) in itertools.combinations(enumerate(self.vertices), 2):
                seg = Seg(a, b)
                intersects = sum(map(seg.intersects, self.edges()))
                assert intersects >= 3
                if intersects <= 4:
                    poly1 = Polygon(self.subvertices(ai, bi))
                    poly2 = Polygon(self.subvertices(bi, ai))
                    if self.area2() == poly1.area2() + poly2.area2(): # now check if the segment is inside.
                        yield seg

        nodes = [start, end] + self.vertices
        adj = {point: [] for point in nodes}
        for seg in get_edges():
            c = abs(seg)
            adj[seg.a].append((seg.b, c))
            adj[seg.b].append((seg.a, c))

        # now, dijkstra from start ### @rem
        # TODO delegate to something in, say, kg.graphs (?) ### @rem
        from heapq import heappush, heappop
        dist = {i: float('inf') for i in nodes}
        parent = {}
        class Dadj:
            def __init__(self, i, p, d):
                self.i = i
                self.p = p
                self.d = d
                super().__init__()

            def __lt__(self, other):
                return self.d < other.d

            def __eq__(self, other):
                return self.d == other.d and self.i == other.i and self.p == other.p

            def __iter__(self):
                return iter((self.i, self.p, self.d))

        pq = [Dadj(start, start, 0)]
        while pq:
            i, p, d = heappop(pq)
            if dist[i] <= d: continue
            dist[i] = d
            parent[i] = p
            if i == end: break
            for j, c in adj[i]:
                if dist[j] > d + c: heappush(pq, Dadj(j, i, d + c))

        # there should always be a path if it is simple ### @rem
        assert dist[end] < float('inf') 

        sequence = [end]
        while end != start:
            end = parent[end]
            sequence.append(end)

        return Polyline(sequence[::-1])




    def __iter__(self):
        return iter(self.vertices)

    def __len__(self):
        return len(self.vertices)

    def __str__(self):
        return f'Polygon[{", ".join(map(str, self.vertices))}]'

    def __repr__(self):
        return f'Polygon({self.vertices!r})'



class Polyline(Edged):
    def __init__(self, vertices):
        if not vertices: raise GeomError("Polylines must have at least one vertex")
        self.vertices = list(vertices)
        super().__init__()

    def edges(self):
        yield from (Seg(*pair) for pair in zip(self.vertices, self.vertices[1:]))

    def rectilinear(self):
        return all(edge.rectilinear() for edge in self.edges())

    def __abs__(self):
        return sum(map(abs, self.edges()))

    def __iter__(self):
        return iter(self.vertices)

    def __len__(self):
        # the idea is that the length is the number of edges... hope that's not confusing ### @rem
        return len(self.vertices) - 1

    def __str__(self):
        return f'Polyline[{", ".join(map(str, self.vertices))}]'

    def __repr__(self):
        return f'Polyline({self.vertices!r})'
