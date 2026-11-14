import ast
import pathlib

from game import render3d as R


def _centroid(verts):
    n = len(verts)
    return (sum(v[0] for v in verts) / n, sum(v[1] for v in verts) / n,
            sum(v[2] for v in verts) / n)


def _all_outward(verts, faces):
    c = _centroid(verts)
    for f in faces:
        pts = [verts[i] for i in f]
        n = R.face_normal(pts)
        fc = _centroid(pts)
        out = (fc[0] - c[0], fc[1] - c[1], fc[2] - c[2])
        if R._dot(n, out) <= 0:
            return False
    return True


def test_cube_has_six_outward_faces():
    v, f = R.unit_cube()
    assert len(v) == 8 and len(f) == 6
    assert _all_outward(v, f)


def test_cylinder_and_cone_faces_point_out():
    for mesh in (R.unit_cylinder(10), R.unit_cone(10)):
        assert _all_outward(*mesh)
    v, f = R.unit_cylinder(10)
    assert len(f) == 12
    v, f = R.unit_cone(8)
    assert len(f) == 9


def test_back_faces_are_dropped():
    cam = R.make_camera(800, 600, yaw=0, pitch=0, dist=10, target=(0, 0.5, 0))
    faces = R.render([{"shape": "cube", "height": 1, "width": 1}], cam)
    # head-on with no pitch only the front face shows
    assert len(faces) == 1


def test_three_faces_from_a_corner():
    cam = R.make_camera(800, 600, yaw=0.7, pitch=0.4, dist=10, target=(0, 0.5, 0))
    faces = R.render([{"shape": "cube", "height": 1, "width": 1}], cam)
    assert len(faces) == 3


def test_behind_camera_is_dropped():
    cam = R.make_camera(800, 600, yaw=0, pitch=0, dist=2, target=(0, 0, 0))
    faces = R.render([{"shape": "cube", "height": 1, "width": 1, "z": -5}], cam)
    assert faces == []
    assert R.project_point((0, 0, -5), cam) is None


def test_sorted_far_to_near():
    cam = R.make_camera(800, 600, yaw=0.5, pitch=0.3, dist=12)
    parts = [{"shape": "cylinder", "height": 2, "width": 0.6, "y": 0},
             {"shape": "cube", "height": 0.5, "width": 0.8, "y": 2},
             {"shape": "cone", "height": 1, "width": 0.6, "y": 2.5}]
    faces = R.render(parts, cam)
    depths = [f[3] for f in faces]
    assert depths == sorted(depths, reverse=True)


def test_shade_in_range():
    cam = R.make_camera(800, 600, yaw=2.0, pitch=0.6)
    parts = [{"shape": s, "height": 1, "width": 1, "y": i * 1.2}
             for i, s in enumerate(["cube", "cylinder", "cone"])]
    for pts, color, shade, depth, part in R.render(parts, cam):
        assert 0.3 <= shade <= 1.0
        assert all(p is not None for p in pts)


def test_center_projects_to_screen_center():
    cam = R.make_camera(800, 600, yaw=1.1, pitch=0.3, dist=9, target=(0, 2, 0))
    x, y = R.project_point((0, 2, 0), cam)
    assert abs(x - 400) < 1e-6 and abs(y - 300) < 1e-6


def test_game_package_never_imports_pygame():
    for path in pathlib.Path("game").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name.startswith("pygame") for a in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("pygame"), path
