#!/usr/bin/env python3
"""
Improved rendering with strategic 12-view system and enhanced lighting.
"""
import os
import argparse
import numpy as np
import trimesh
import pyrender
from PIL import Image


def look_at(eye, target, up):
    """Build a 4x4 camera pose matrix given eye, target, and up vectors."""
    eye = np.array(eye, dtype=np.float64)
    target = np.array(target, dtype=np.float64)
    up = np.array(up, dtype=np.float64)

    forward = target - eye
    forward /= np.linalg.norm(forward)

    right = np.cross(forward, up)
    right /= np.linalg.norm(right)

    true_up = np.cross(right, forward)

    mat = np.eye(4, dtype=np.float64)
    mat[0, :3] = right
    mat[1, :3] = true_up
    mat[2, :3] = -forward
    mat[:3, 3] = eye

    return mat


def get_12_strategic_views():
    """
    Return 12 strategic view directions that provide comprehensive coverage:
    - 4 cardinal directions (front, right, back, left)
    - 2 vertical (top, bottom)
    - 6 corner/edge views for transition perspectives
    """
    views = []

    # 4 cardinal directions (around Y-axis)
    for i in range(4):
        angle = np.pi / 2 * i
        views.append({
            'rotation': trimesh.transformations.rotation_matrix(angle, [0, 1, 0]),
            'label': ['Front', 'Right', 'Back', 'Left'][i]
        })

    # Top and bottom views
    views.append({
        'rotation': trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]),
        'label': 'Top'
    })
    views.append({
        'rotation': trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]),
        'label': 'Bottom'
    })

    # 6 strategic corner/edge views for better 3D understanding
    corner_angles = [
        (np.pi / 4, np.pi / 6, 'Front-Top-Right'),
        (3 * np.pi / 4, np.pi / 6, 'Back-Top-Right'),
        (5 * np.pi / 4, np.pi / 6, 'Back-Top-Left'),
        (7 * np.pi / 4, np.pi / 6, 'Front-Top-Left'),
        (np.pi / 4, -np.pi / 6, 'Front-Bottom-Right'),
        (5 * np.pi / 4, -np.pi / 6, 'Back-Bottom-Left'),
    ]

    for h_angle, v_angle, label in corner_angles:
        # Combine horizontal and vertical rotations
        rot_h = trimesh.transformations.rotation_matrix(h_angle, [0, 1, 0])
        rot_v = trimesh.transformations.rotation_matrix(v_angle, [1, 0, 0])
        combined = np.dot(rot_h, rot_v)
        views.append({'rotation': combined, 'label': label})

    return views


def load_mesh(path):
    """Load a GLB/3D file and return a single trimesh.Trimesh object."""
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

    # Center and normalize size for consistent framing
    mesh.apply_translation(-mesh.centroid)
    scale = 1.0 / max(mesh.extents)
    mesh.apply_scale(scale)

    return mesh


def create_enhanced_lighting(scene):
    """
    Create enhanced lighting setup with:
    - Main directional light (key light)
    - Fill lights from multiple angles
    - Subtle ambient lighting
    """
    # Key light (main directional from front-top)
    key_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
    key_pose = look_at([2, 3, 2], [0, 0, 0], [0, 1, 0])
    scene.add(key_light, pose=key_pose)

    # Fill light (softer, from opposite side)
    fill_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=1.5)
    fill_pose = look_at([-2, 2, -1], [0, 0, 0], [0, 1, 0])
    scene.add(fill_light, pose=fill_pose)

    # Back light (rim lighting for depth)
    back_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=1.0)
    back_pose = look_at([0, 1, -3], [0, 0, 0], [0, 1, 0])
    scene.add(back_light, pose=back_pose)

    # Subtle side lights for better color definition
    side_light1 = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=0.8)
    side_pose1 = look_at([3, 0, 0], [0, 0, 0], [0, 1, 0])
    scene.add(side_light1, pose=side_pose1)

    side_light2 = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=0.8)
    side_pose2 = look_at([-3, 0, 0], [0, 0, 0], [0, 1, 0])
    scene.add(side_light2, pose=side_pose2)


def render_views_improved(
    glb_path: str,
    out_dir: str = "renders",
    n_views: int = 12,
    img_size: int = 768,
):
    """
    Render improved PNG images with strategic viewing angles and enhanced lighting.

    :param glb_path: Path to the .glb file
    :param out_dir: Directory where PNGs will be saved
    :param n_views: Number of views to render (recommended: 12)
    :param img_size: Width/height of output images (recommended: 768 or 1024)
    """
    os.makedirs(out_dir, exist_ok=True)

    mesh = load_mesh(glb_path)

    # Create scene with clean white background
    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0])
    mesh_node = scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=False))

    # Add enhanced lighting
    create_enhanced_lighting(scene)

    # Camera setup
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    renderer = pyrender.OffscreenRenderer(img_size, img_size)

    # Camera distance and pose
    dist = 1.8  # Slightly further for better framing
    cam_pose = np.eye(4)
    cam_pose[2, 3] = dist
    cam_node = scene.add(camera, pose=cam_pose)

    # Get strategic views
    if n_views == 12:
        views = get_12_strategic_views()
    else:
        # Fall back to simple rotation for other view counts
        views = []
        for i in range(n_views):
            theta = 2 * np.pi * (i / n_views)
            rot_y = trimesh.transformations.rotation_matrix(theta, [0, 1, 0])
            views.append({'rotation': rot_y, 'label': f'View {i+1}'})

    # Render each view
    for i, view_info in enumerate(views[:n_views]):
        rotation = view_info['rotation']
        label = view_info['label']

        scene.set_pose(mesh_node, pose=rotation)
        color, _ = renderer.render(scene)

        out_path = os.path.join(out_dir, f"view_{i:03d}.png")
        Image.fromarray(color).save(out_path)
        print(f"Saved {out_path} ({label})")

    renderer.delete()
    print(f"Done rendering {n_views} views.")


def main():
    parser = argparse.ArgumentParser(description="Improved renderer with strategic 12-view system")
    parser.add_argument("glb_path", help="Path to the .glb file")
    parser.add_argument(
        "-n",
        "--num-views",
        type=int,
        default=12,
        help="Number of views to render (default: 12)",
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
        default=768,
        help="Image size (width=height, default: 768)",
    )
    args = parser.parse_args()

    render_views_improved(
        glb_path=args.glb_path,
        out_dir=args.out_dir,
        n_views=args.num_views,
        img_size=args.size,
    )


if __name__ == "__main__":
    main()
