import argparse
import os

import numpy as np


def main(
    simulations_path: str,
    simulation_frames: int,
    simulation_height: int,
    simulation_width: int,
    frames_per_row: int,
    output_path: str,
):
    os.makedirs(output_path, exist_ok=True)
    simulations = [
        dir
        for dir in os.listdir(simulations_path)
        if os.path.isdir(dir)
        and len(
            {"frames.npy", "actions.npy"}.intersection(
                set(os.listdir(os.path.join(simulations_path, dir)))
            )
        )
        == 2
    ]
    # We slide the window along the frames until the end of the window reaches the last frame.
    n_rows = len(simulations) * (simulation_frames - frames_per_row)
    all_frames = np.memmap(
        dtype=np.uint8,
        shape=(n_rows, frames_per_row, simulation_height, simulation_width, 3),
        mode="w+",
        filename=f"{output_path}/frames.npy",
    )
    all_actions = np.memmap(
        dtype=np.uint8,
        shape=(n_rows, frames_per_row, 4),
        mode="w+",
        filename=f"{output_path}/actions.npy",
    )
    current_row = 0
    for simulation in simulations:
        simulation_path = os.path.join(simulations_path, simulation)
        assert os.path.isdir(simulation_path)
        frames = np.memmap(
            dtype=np.uint8,
            shape=(
                simulation_frames,
                simulation_height,
                simulation_width,
                3,
            ),
            mode="r",
            filename=os.path.join(simulation_path, "frames.npy"),
        )
        actions = np.memmap(
            dtype=np.uint8,
            shape=(simulation_frames, 4),
            mode="r",
            filename=os.path.join(simulation_path, "actions.npy"),
        )
        # Run a sliding window over the frames and actions.
        # Collect add each window to the output dataset.
        for i in range(simulation_frames - frames_per_row):
            all_frames[current_row] = frames[i : i + frames_per_row]
            all_actions[current_row] = actions[i : i + frames_per_row]
            current_row += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulations-path",
        type=str,
        default="data",
        help="Path to simulation data",
    )
    parser.add_argument(
        "--simulation-frames",
        type=int,
        default=1000,
        help="Number of frames in simulation",
    )
    parser.add_argument(
        "--simulation-height",
        type=int,
        default=400,
        help="Height of simulation window",
    )
    parser.add_argument(
        "--simulation-width",
        type=int,
        default=400,
        help="Width of simulation window",
    )
    parser.add_argument(
        "--frames-per-row",
        type=int,
        default=3,
        help="Number of frames per row in output dataset",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="dataset",
        help="Path to output dataset",
    )
    args = parser.parse_args()
    main(**vars(args))
