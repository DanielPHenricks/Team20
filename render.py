#!/usr/bin/env python3
import os
import argparse
import numpy as np
import trimesh

import pyrender
from PIL import Image


# Helper function: look_at
def look_at(eye, target, up):
    """
    Build a 4x4 camera pose matrix given eye, target, and up vectors.
    """
    eye = np.array(eye, dtype=np.float64)
    target = np.array(target, dtype=np.float64)
    up = np.array(up, dtype=np.float64)

    # Forward vector (from eye to target)
    forward = target - eye
    forward /= np.linalg.norm(forward)

    # Right vector
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)

    # Recomputed orthogonal up vector
    true_up = np.cross(right, forward)

    # Build 4x4 matrix
    mat = np.eye(4, dtype=np.float64)
    mat[0, :3] = right
    mat[1, :3] = true_up
    mat[2, :3] = -forward  # negative forward for right-handed camera
    mat[:3, 3] = eye

    return mat

# Helper function: rotation_from_vectors
def rotation_from_vectors(vec_from, vec_to):
    """
    Compute a 4x4 rotation matrix that rotates vec_from to vec_to.
    """
    vec_from = np.array(vec_from, dtype=np.float64)
    vec_to = np.array(vec_to, dtype=np.float64)
    vec_from /= np.linalg.norm(vec_from)
    vec_to /= np.linalg.norm(vec_to)

    v = np.cross(vec_from, vec_to)
    c = np.dot(vec_from, vec_to)
    s = np.linalg.norm(v)

    # If vectors are almost identical, no rotation needed
    if s < 1e-8:
        return np.eye(4, dtype=np.float64)

    # If vectors are opposite, rotate 180 degrees around any orthogonal axis
    if np.isclose(c, -1.0):
        # Find an axis orthogonal to vec_from
        axis = np.array([1.0, 0.0, 0.0])
        if np.allclose(vec_from, axis):
            axis = np.array([0.0, 1.0, 0.0])
        axis = np.cross(vec_from, axis)
        axis /= np.linalg.norm(axis)
        return trimesh.transformations.rotation_matrix(np.pi, axis)

    axis = v / s
    angle = np.arctan2(s, c)
    return trimesh.transformations.rotation_matrix(angle, axis)


def load_mesh(path):
    """
    Load a GLB/3D file and return a single trimesh.Trimesh object.
    Handles both single-mesh and scene files.
    """
    """
    Load a GLB/3D file and return a single trimesh.Trimesh object.
    Handles single-mesh files, scenes, and loaders that return lists.
    """
    loaded = trimesh.load(path)

    # Normalize to a list of trimesh.Trimesh objects
    if isinstance(loaded, trimesh.Scene):
        geom_list = list(loaded.geometry.values())
    elif isinstance(loaded, trimesh.Trimesh):
        geom_list = [loaded]
    elif isinstance(loaded, (list, tuple)):
        geom_list = list(loaded)
    else:
        raise TypeError(f"Unsupported mesh type from trimesh.load: {type(loaded)}")

    # Merge into a single mesh
    mesh = trimesh.util.concatenate(geom_list)

    # Center and normalize size a bit for nicer framing
    mesh.apply_translation(-mesh.centroid)
    scale = 1.0 / max(mesh.extents)
    mesh.apply_scale(scale)

    return mesh


def render_views(
    glb_path: str,
    out_dir: str = "renders",
    n_views: int = 6,
    img_size: int = 512,
):
    """
    Render `n_views` PNG images of the object from different angles around it.

    :param glb_path: Path to the .glb file
    :param out_dir: Directory where PNGs will be saved
    :param n_views: Number of views to render
    :param img_size: Width/height of output images
    """
    os.makedirs(out_dir, exist_ok=True)

    mesh = load_mesh(glb_path)

    # Create scene and add mesh
    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 0.0])  # white-ish background
    mesh_node = scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=False))

    # Simple flat-ish lighting: a few directional lights from different angles
    lights = [
        pyrender.DirectionalLight(intensity=2.0),
        pyrender.DirectionalLight(intensity=2.0),
        pyrender.DirectionalLight(intensity=2.0),
    ]

    # Add lights at different directions
    light_poses = [
        np.eye(4),
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, -1, 0],
                [0, 1, 0, 2],
                [0, 0, 0, 1],
            ]
        ),
        np.array(
            [
                [0, 0, 1, -2],
                [0, 1, 0, 2],
                [-1, 0, 0, 2],
                [0, 0, 0, 1],
            ]
        ),
    ]

    for light, pose in zip(lights, light_poses):
        scene.add(light, pose=pose)

    # Camera (fixed)
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    renderer = pyrender.OffscreenRenderer(img_size, img_size)

    # Put camera at (0, 0, dist), looking toward origin along -Z
    dist = 1.5
    cam_pose = np.eye(4)
    cam_pose[2, 3] = dist  # camera position in world coords
    cam_node = scene.add(camera, pose=cam_pose)

    if n_views == 8:
        # Use the 8 corners of a cube as view directions
        corners = [
            (-1, -1, -1),
            (-1, -1,  1),
            (-1,  1, -1),
            (-1,  1,  1),
            ( 1, -1, -1),
            ( 1, -1,  1),
            ( 1,  1, -1),
            ( 1,  1,  1),
        ]
        target_dir = np.array([0.0, 0.0, -1.0])  # camera looks along -Z
    else:
        corners = None  # will use simple Y-rotation

    for i in range(n_views):
        if corners is not None:
            # Rotate mesh so that the chosen corner direction points toward camera -Z
            corner_dir = np.array(corners[i], dtype=np.float64)
            rot = rotation_from_vectors(corner_dir, target_dir)
            scene.set_pose(mesh_node, pose=rot)
        else:
            # Fallback: rotate the mesh around the Y axis
            theta = 2 * np.pi * (i / n_views)
            rot_y = trimesh.transformations.rotation_matrix(theta, [0, 1, 0])
            scene.set_pose(mesh_node, pose=rot_y)

        color, _ = renderer.render(scene)

        out_path = os.path.join(out_dir, f"view_{i:03d}.png")
        Image.fromarray(color).save(out_path)
        print(f"Saved {out_path}")

    renderer.delete()
    scene.remove_node(mesh_node)
    scene.remove_node(cam_node)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Render N PNG views from a GLB file."
    )
    parser.add_argument("glb_path", help="Path to the .glb file")
    parser.add_argument(
        "-n",
        "--num-views",
        type=int,
        default=6,
        help="Number of views to render (default: 6)",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        default="renders",
        help="Output directory for PNGs (default: renders)",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=512,
        help="Image size (width=height, default: 512)",
    )
    args = parser.parse_args()

    render_views(
        glb_path=args.glb_path,
        out_dir=args.out_dir,
        n_views=args.num_views,
        img_size=args.size,
    )


if __name__ == "__main__":
    main()

"python render.py ./tmp/preview_model.glb -n 8 -o views_out -s 512"