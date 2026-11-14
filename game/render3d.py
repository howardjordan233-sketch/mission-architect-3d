"""A small software 3D renderer in pure Python.

No pygame, no NumPy. It turns low-poly shapes into flat-shaded 2D
polygons sorted far to near (the painter's algorithm). The scenes draw
what it returns with pygame.draw.polygon.

Coordinates: y is up. Unit shapes sit on y=0 and are 1 unit tall, so a
part of height h placed at height y fills y..y+h.
"""
import math

LIGHT = (-0.45, 0.8, -0.4)  # direction the light comes from (normalised below)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)
NEAR = 0.1


# ---------------------------------------------------------------- shapes
def unit_cube():
    """x and z from -1 to 1, y from 0 to 1. Faces wound counter-clockwise from outside."""
    v = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1),
         (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)]
    f = [[0, 1, 2, 3],  # bottom
         [4, 7, 6, 5],  # top
         [0, 4, 5, 1],  # back (z = -1)
         [2, 6, 7, 3],  # front (z = +1)
         [1, 5, 6, 2],  # right
         [3, 7, 4, 0]]  # left
    return v, f


def unit_cylinder(sides=10):
    """Radius 1, y from 0 to 1."""
    v = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        v.append((math.cos(a), 0, math.sin(a)))
    for i in range(sides):
        a = 2 * math.pi * i / sides
        v.append((math.cos(a), 1, math.sin(a)))
    f = []
    for i in range(sides):
        j = (i + 1) % sides
        f.append([i, sides + i, sides + j, j])
    f.append(list(range(sides)))  # bottom (x toward z gives a -y normal)
    f.append(list(range(2 * sides - 1, sides - 1, -1)))  # top
    return v, f


def unit_cone(sides=10):
    """Base radius 1 at y=0, apex at y=1."""
    v = [(math.cos(2 * math.pi * i / sides), 0, math.sin(2 * math.pi * i / sides))
         for i in range(sides)]
    v.append((0, 1, 0))
    apex = sides
    f = [[i, apex, (i + 1) % sides] for i in range(sides)]
    f.append(list(range(sides)))  # bottom
    return v, f


_CACHE = {}


def shape_mesh(shape, sides=10):
    key = (shape, sides)
    if key not in _CACHE:
        if shape == "cube":
            _CACHE[key] = unit_cube()
        elif shape == "cylinder":
            _CACHE[key] = unit_cylinder(sides)
        elif shape == "cone":
            _CACHE[key] = unit_cone(sides)
        else:
            raise ValueError("unknown shape %r" % shape)
    return _CACHE[key]


# ---------------------------------------------------------------- transforms
def scale(verts, sx, sy, sz):
    return [(x * sx, y * sy, z * sz) for x, y, z in verts]


def translate(verts, dx, dy, dz):
    return [(x + dx, y + dy, z + dz) for x, y, z in verts]


def rotate_y(verts, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [(x * c + z * s, y, -x * s + z * c) for x, y, z in verts]


def rotate_x(verts, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [(x, y * c - z * s, y * s + z * c) for x, y, z in verts]


def rotate_z(verts, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [(x * c - y * s, x * s + y * c, z) for x, y, z in verts]


# ---------------------------------------------------------------- vectors
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n else (0.0, 0.0, 0.0)


def face_normal(pts):
    """Outward normal of a counter-clockwise face (first non-degenerate triple)."""
    for k in range(1, len(pts) - 1):
        n = _cross(_sub(pts[k], pts[0]), _sub(pts[k + 1], pts[0]))
        if _dot(n, n) > 1e-12:
            return _norm(n)
    return (0.0, 0.0, 0.0)


def shade_for(normal):
    """0.3 (facing away from the light) to 1.0 (facing it)."""
    return 0.3 + 0.7 * max(0.0, _dot(normal, LIGHT))


# ---------------------------------------------------------------- camera
def make_camera(w, h, yaw=0.6, pitch=0.35, dist=12.0, target=(0.0, 3.0, 0.0), fov=1.0):
    return {"w": w, "h": h, "yaw": yaw, "pitch": pitch, "dist": dist,
            "target": target, "focal": (min(w, h) / 2) / math.tan(fov / 2)}


def to_view(verts, cam):
    """World space to camera space (camera looks down +z)."""
    tx, ty, tz = cam["target"]
    v = translate(verts, -tx, -ty, -tz)
    v = rotate_y(v, -cam["yaw"])
    v = rotate_x(v, -cam["pitch"])
    return [(x, y, z + cam["dist"]) for x, y, z in v]


def project(verts, cam, ox=0.0, oy=0.0):
    """Camera-space points to screen points. Points behind the camera give None."""
    f, cx, cy = cam["focal"], cam["w"] / 2 + ox, cam["h"] / 2 + oy
    out = []
    for x, y, z in verts:
        if z <= NEAR:
            out.append(None)
        else:
            out.append((cx + x * f / z, cy - y * f / z))
    return out


def project_point(p, cam, ox=0.0, oy=0.0):
    """One world point to the screen, or None if behind the camera."""
    return project(to_view([p], cam), cam, ox, oy)[0]


# ---------------------------------------------------------------- render
def part_mesh(part):
    """World-space vertices and faces for one part dict.

    part keys: shape, height, width, and optional y, x, z, sx, sz, yaw, tilt,
    sides, color, alpha, tag.
    """
    verts, faces = shape_mesh(part["shape"], part.get("sides", 10))
    w = part["width"]
    sx = part.get("sx", w)
    sz = part.get("sz", w)
    v = scale(verts, sx, part["height"], sz)
    if part.get("tilt"):
        v = translate(v, 0, -part["height"] / 2, 0)
        v = rotate_z(v, part["tilt"])
        v = translate(v, 0, part["height"] / 2, 0)
    if part.get("yaw"):
        v = rotate_y(v, part["yaw"])
    v = translate(v, part.get("x", 0.0), part.get("y", 0.0), part.get("z", 0.0))
    return v, faces


def render(parts, cam, ox=0.0, oy=0.0, cull=True):
    """Returns [(points_2d, color, shade, depth, part)] sorted far to near.

    Back faces and faces with any point behind the camera are dropped.
    """
    out = []
    for part in parts:
        world, faces = part_mesh(part)
        view = to_view(world, cam)
        screen = project(view, cam, ox, oy)
        color = part.get("color", (200, 200, 200))
        for face in faces:
            vpts = [view[i] for i in face]
            if any(p[2] <= NEAR for p in vpts):
                continue
            n_view = face_normal(vpts)
            centre = (sum(p[0] for p in vpts) / len(vpts),
                      sum(p[1] for p in vpts) / len(vpts),
                      sum(p[2] for p in vpts) / len(vpts))
            if cull and _dot(n_view, centre) >= 0:
                continue
            n_world = face_normal([world[i] for i in face])
            pts = [screen[i] for i in face]
            out.append((pts, color, shade_for(n_world), centre[2], part))
    out.sort(key=lambda t: -t[3])
    return out


def lit(color, shade):
    """Apply a shade (0.3-1.0) to an (r, g, b) color."""
    return (min(255, int(color[0] * shade)), min(255, int(color[1] * shade)),
            min(255, int(color[2] * shade)))
